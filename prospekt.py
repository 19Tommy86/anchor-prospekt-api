"""
Uthenting av nøkkeltall fra norske salgsoppgaver (PDF).

Den gamle versjonen hentet kun BRA. Prisen ble aldri plukket opp, så
analysen fikk aldri vite hva eiendommen kostet – og regnet på feil
grunnlag uten å si ifra.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Norske prospekter skriver beløp på mange måter:
#   "3 950 000"     (vanlig mellomrom)
#   "3 950 000"     (hardt mellomrom, U+00A0 – vanlig ved PDF-uthenting)
#   "3.950.000"     (punktum som tusenskille)
#   "kr 3 950 000,-"
# Merk: vi bruker IKKE \s her. \s matcher også linjeskift, slik at beløpet
# ville sluke tekst fra neste linje i prospektet. Kun mellomrom, hardt
# mellomrom og punktum er gyldige tusenskiller.
BELOP = r"([\d][\d  .]{2,})"

# Areal kan ha desimaler: "131", "131,5", "131.5"
AREAL = r"(\d+(?:[.,]\d+)?)"


def _parse_belop(rå: str, min_verdi: float) -> Optional[float]:
    """
    Gjør en beløpsstreng om til et tall.

    "3 950 000"  -> 3950000.0
    "3.950.000"  -> 3950000.0

    min_verdi er en nedre fornuftsgrense. Den er ulik per felt: en
    kjøpesum under 100 000 kr er nesten sikkert en feillesing, mens
    felleskostnader på 3 500 kr i måneden er helt normalt.

    Returnerer None hvis strengen ikke gir et fornuftig beløp.
    """
    # Fjern alt som ikke er siffer: mellomrom, hardt mellomrom, punktum,
    # komma, bindestrek og eventuelle linjeskift som slipper gjennom.
    reint = re.sub(r"\D", "", rå)
    if not reint:
        return None

    verdi = float(reint)
    return verdi if verdi >= min_verdi else None


def _parse_areal(rå: str) -> Optional[float]:
    """Gjør "131,5" eller "131.5" om til 131.5."""
    try:
        verdi = float(rå.replace(",", "."))
    except ValueError:
        return None
    # Under 5 m² eller over 2000 m² er nesten sikkert feillesing.
    return verdi if 5 <= verdi <= 2000 else None


def _sok_belop(tekst: str, etiketter: list[str], min_verdi: float) -> Optional[float]:
    """
    Leter etter det første beløpet som står like etter en av etikettene.

    Vi tillater inntil 40 tegn mellom etiketten og tallet, fordi PDF-er
    ofte har "Prisantydning ....... kr 3 950 000" med fyllprikker eller
    kolonner imellom.
    """
    for etikett in etiketter:
        treff = re.search(rf"{etikett}[^\d]{{0,40}}{BELOP}", tekst, flags=re.IGNORECASE)
        if treff:
            belop = _parse_belop(treff.group(1), min_verdi)
            if belop is not None:
                return belop
    return None


def _sok_areal(tekst: str, etiketter: list[str]) -> Optional[float]:
    """Som _sok_belop, men for arealer."""
    for etikett in etiketter:
        treff = re.search(rf"{etikett}[^\d]{{0,25}}{AREAL}", tekst, flags=re.IGNORECASE)
        if treff:
            areal = _parse_areal(treff.group(1))
            if areal is not None:
                return areal
    return None


def hent_nokkeltall(tekst: str) -> dict[str, Any]:
    """
    Plukker ut nøkkeltall fra teksten i en salgsoppgave.

    Returnerer kun feltene som faktisk ble funnet – ingen gjettede
    verdier. Manglende felt er informasjon i seg selv: da vet du at du
    må fylle dem inn manuelt.
    """
    ut: dict[str, Any] = {}

    # Totalpris inkluderer omkostninger og er det beløpet du faktisk
    # betaler, så den prioriteres foran prisantydning.
    totalpris = _sok_belop(tekst, [r"totalpris", r"total\s*pris"], min_verdi=100_000)
    if totalpris is not None:
        ut["totalpris"] = totalpris

    prisantydning = _sok_belop(tekst, [r"prisantydning", r"pris\s*antydning", r"kjøpesum"], min_verdi=100_000)
    if prisantydning is not None:
        ut["prisantydning"] = prisantydning

    bra = _sok_areal(tekst, [r"\bBRA\b", r"bruksareal"])
    if bra is not None:
        ut["BRA_m2"] = bra

    p_rom = _sok_areal(tekst, [r"P-?rom", r"primærrom"])
    if p_rom is not None:
        ut["p_rom_m2"] = p_rom

    felleskost = _sok_belop(tekst, [r"felleskostnader", r"fellesutgifter"], min_verdi=100)
    if felleskost is not None:
        ut["felleskostnader_mnd"] = felleskost

    kommunale = _sok_belop(tekst, [r"kommunale\s*avgifter"], min_verdi=100)
    if kommunale is not None:
        ut["kommunale_avgifter_aar"] = kommunale

    return ut
