"""
Finansberegninger for BRRRR-analyse.

BRRRR = Buy, Rehab, Rent, Refinance, Repeat.

Skilt ut fra main.py slik at regnestykkene kan testes uten å starte et
web-API. Det er disse tallene som avgjør om du kjøper en eiendom eller
ikke, så de må kunne verifiseres isolert.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Assumptions(BaseModel):
    """
    Forutsetningene analysen bygger på.

    Alt som tidligere lå som skjulte tall inne i regnestykket er flyttet
    hit, slik at du ser dem og kan endre dem. Et tall du ikke ser er et
    tall du ikke kan etterprøve.
    """

    interest_rate: float = Field(default=0.049, ge=0, le=1,
                                 description="Nominell årsrente, f.eks. 0.049 = 4,9 %")
    term_years: int = Field(default=30, gt=0, le=50,
                            description="Nedbetalingstid i år")
    renovation_budget: float = Field(default=300_000.0, ge=0,
                                     description="Oppussingsbudsjett i kroner")
    ltv_post_refi: float = Field(default=0.75, ge=0, le=1,
                                 description="Belåningsgrad ved refinansiering")
    rent_est_mid: float = Field(default=13_500.0, ge=0,
                                description="Forventet husleie per måned")
    operating_cost_year: float = Field(default=45_000.0, ge=0,
                                       description="Driftskostnader per år")

    # Disse to lå tidligere hardkodet inne i beregningen (0.20 og 30000).
    equity_share: float = Field(default=0.20, ge=0, le=1,
                                description="Egenkapitalandel ved kjøp")
    price_per_sqm_after: float = Field(default=30_000.0, ge=0,
                                       description="Antatt kvadratmeterpris etter oppussing")


class ManglerPris(ValueError):
    """Kastes når prospektet ikke inneholder en kjøpesum å regne på."""


def annuity_payment(principal: float, rate_year: float, years: int) -> float:
    """
    Månedlig annuitetsbetaling på et lån.

    Ved 0 % rente er annuitetsformelen udefinert (0/0). Da er betalingen
    ganske enkelt lånet fordelt likt over antall måneder.
    """
    n = years * 12
    if n <= 0:
        raise ValueError("Nedbetalingstiden må være minst ett år.")

    r = rate_year / 12
    if r == 0:
        return principal / n

    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def _finn_pris(ex: dict[str, Any]) -> Optional[float]:
    """
    Leter etter kjøpesummen under de navnene PDF-uthentingen kan gi den.
    Returnerer None hvis ingen av dem finnes.
    """
    for nokkel in ("totalpris", "total_price", "prisantydning", "kjopesum"):
        verdi = ex.get(nokkel)
        if verdi:
            return float(verdi)
    return None


def _finn_bra(ex: dict[str, Any]) -> Optional[float]:
    """Leter etter bruksareal under de navnene som kan forekomme."""
    for nokkel in ("bra", "BRA", "BRA_m2", "bruksareal"):
        verdi = ex.get(nokkel)
        if verdi:
            return float(verdi)
    return None


def compute_metrics(ex: dict[str, Any], a: Assumptions) -> dict[str, Any]:
    """
    Regner ut nøkkeltallene for en eiendom.

    Kaster ManglerPris hvis prospektet ikke har en kjøpesum. Tidligere
    falt koden tilbake på et hardkodet beløp når prisen manglet – det ga
    tall som så ut som en fantastisk investering, men som var regnet på
    feil grunnlag. Det er bedre å si ifra enn å gjette.
    """
    pris = _finn_pris(ex)
    if pris is None:
        raise ManglerPris(
            "Fant ingen kjøpesum i dataene. Oppgi 'totalpris' eller "
            "'prisantydning' før analysen kan kjøres."
        )
    if pris <= 0:
        raise ManglerPris(f"Kjøpesummen må være et positivt beløp, fikk {pris}.")

    advarsler: list[str] = []

    # --- Kjøp og finansiering ---
    total_cost = pris + a.renovation_budget
    ek = a.equity_share * total_cost
    loan = total_cost - ek
    pay_m = annuity_payment(loan, a.interest_rate, a.term_years)

    # --- Drift ---
    income_year = a.rent_est_mid * 12
    opex_year = a.operating_cost_year
    gross_yield = income_year / total_cost
    net_yield = (income_year - opex_year) / total_cost
    cashflow_month = (income_year - opex_year - pay_m * 12) / 12

    # --- Verdi etter oppussing (ARV) og refinansiering ---
    bra = _finn_bra(ex)
    if bra is None:
        # Uten bruksareal kan vi ikke anslå verdien etter oppussing.
        # Vi gjetter ikke – vi sier at tallet mangler.
        arv_mid = None
        refi_cashout_mid = None
        advarsler.append(
            "Bruksareal (BRA) mangler. Verdi etter oppussing og "
            "refinansieringsbeløp kunne ikke beregnes."
        )
    else:
        psqm = float(ex.get("price_per_sqm_after") or a.price_per_sqm_after)
        arv_mid = bra * psqm
        # Lånesaldoen er ikke nedbetalt i oppussingsperioden i denne modellen.
        refi_cashout_mid = max(0.0, a.ltv_post_refi * arv_mid - loan)

    if cashflow_month < 0:
        advarsler.append(
            f"Negativ kontantstrøm: {round(cashflow_month)} kr per måned. "
            "Eiendommen koster deg penger hver måned med disse forutsetningene."
        )

    return {
        # Feltnavnene beholdes uendret – frontend-en leser disse.
        "total_cost": round(total_cost, 2),
        "loan": round(loan, 2),
        "equity": round(ek, 2),
        "gross_yield": round(gross_yield, 4),
        "net_yield": round(net_yield, 4),
        "cashflow_month": round(cashflow_month, 2),
        "arv_mid": round(arv_mid, 2) if arv_mid is not None else None,
        "refi_cashout_mid": round(refi_cashout_mid, 2) if refi_cashout_mid is not None else None,
        # Nye felter:
        "payment_month": round(pay_m, 2),
        "purchase_price": round(pris, 2),
        "advarsler": advarsler,
    }
