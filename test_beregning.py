"""
Tester for BRRRR-beregningene og PDF-uthentingen.

Kjør:  pytest -q

Hver test som starter med "test_regresjon" dekker en feil som faktisk
fantes i koden. De står der for at feilen ikke skal komme tilbake.
"""

import math

import pytest

from beregning import Assumptions, ManglerPris, annuity_payment, compute_metrics
from prospekt import hent_nokkeltall


# ---------------------------------------------------------------- annuitet

def test_annuitet_kjent_verdi():
    """1 000 000 kr over 30 år til 4,9 % skal gi ca. 5 307 kr/mnd."""
    betaling = annuity_payment(1_000_000, 0.049, 30)
    assert math.isclose(betaling, 5307, abs_tol=5)


def test_regresjon_annuitet_null_rente():
    """
    Ved 0 % rente ga formelen 0/0 og krasjet med ZeroDivisionError.
    Nå fordeles lånet likt over antall måneder.
    """
    betaling = annuity_payment(1_200_000, 0.0, 10)
    assert math.isclose(betaling, 10_000)


def test_annuitet_avviser_null_aar():
    with pytest.raises(ValueError):
        annuity_payment(1_000_000, 0.049, 0)


# ------------------------------------------------------------ compute_metrics

def test_regresjon_manglende_pris_gir_feil_ikke_gjetning():
    """
    Tidligere: mangler prisen, ble total_cost lik oppussingsbudsjettet
    alene (300 000). Yield ble da 54 % i stedet for 8 % – eiendommen så
    ut som en gullgruve. Nå sier koden ifra i stedet for å gjette.
    """
    with pytest.raises(ManglerPris):
        compute_metrics({"BRA_m2": 131.0}, Assumptions())


def test_avviser_negativ_pris():
    with pytest.raises(ManglerPris):
        compute_metrics({"totalpris": -500_000}, Assumptions())


def test_grunnleggende_regnestykke():
    """Kjøp 2 000 000 + 300 000 oppussing, 20 % egenkapital."""
    r = compute_metrics({"totalpris": 2_000_000, "BRA_m2": 100}, Assumptions())

    assert r["purchase_price"] == 2_000_000
    assert r["total_cost"] == 2_300_000
    assert r["equity"] == 460_000          # 20 % av 2 300 000
    assert r["loan"] == 1_840_000
    assert r["total_cost"] == r["equity"] + r["loan"]


def test_yield_regnes_mot_total_kostnad():
    r = compute_metrics({"totalpris": 2_000_000, "BRA_m2": 100}, Assumptions())
    a = Assumptions()

    forventet_brutto = (a.rent_est_mid * 12) / 2_300_000
    assert math.isclose(r["gross_yield"], round(forventet_brutto, 4))
    assert r["net_yield"] < r["gross_yield"]   # netto trekker fra driftskostnader


def test_arv_og_refinansiering():
    """BRA 100 m² x 30 000 kr/m² = 3 000 000 i verdi etter oppussing."""
    r = compute_metrics({"totalpris": 2_000_000, "BRA_m2": 100}, Assumptions())

    assert r["arv_mid"] == 3_000_000
    # 75 % av 3 000 000 = 2 250 000, minus lån 1 840 000 = 410 000
    assert r["refi_cashout_mid"] == 410_000


def test_refinansiering_aldri_negativ():
    """Er eiendommen verdt lite, skal uttaket være 0 – ikke et negativt tall."""
    r = compute_metrics({"totalpris": 5_000_000, "BRA_m2": 20}, Assumptions())
    assert r["refi_cashout_mid"] == 0.0


def test_manglende_bra_gir_none_ikke_gjettet_tall():
    """
    Tidligere ble BRA satt til 131 m² når det manglet – et tall hentet
    fra en tilfeldig eiendom. Nå returneres None med en advarsel.
    """
    r = compute_metrics({"totalpris": 2_000_000}, Assumptions())

    assert r["arv_mid"] is None
    assert r["refi_cashout_mid"] is None
    assert any("BRA" in adv for adv in r["advarsler"])


def test_advarsel_ved_negativ_kontantstrom():
    dyrt = Assumptions(rent_est_mid=5_000)
    r = compute_metrics({"totalpris": 4_000_000, "BRA_m2": 100}, dyrt)

    assert r["cashflow_month"] < 0
    assert any("Negativ kontantstrøm" in adv for adv in r["advarsler"])


def test_egenkapitalandel_kan_endres():
    """Egenkapitalandelen lå hardkodet til 20 %. Nå er den en forutsetning."""
    r = compute_metrics({"totalpris": 2_000_000}, Assumptions(equity_share=0.35))
    assert r["equity"] == 0.35 * 2_300_000


def test_frontend_felter_finnes_fortsatt():
    """Frontend-en leser disse feltene – de må ikke forsvinne."""
    r = compute_metrics({"totalpris": 2_000_000, "BRA_m2": 100}, Assumptions())
    for felt in ("cashflow_month", "gross_yield", "net_yield", "refi_cashout_mid",
                 "total_cost", "loan", "equity", "arv_mid"):
        assert felt in r


# ---------------------------------------------------------------- PDF-uthenting

def test_regresjon_pris_hentes_fra_prospekt():
    """
    Tidligere hentet uthentingen kun BRA. Prisen ble aldri plukket opp,
    så analysen fikk aldri vite hva eiendommen kostet.
    """
    tekst = "Prisantydning: kr 3 950 000,-\nTotalpris: 4 052 300\nBRA: 131 m2"
    ut = hent_nokkeltall(tekst)

    assert ut["totalpris"] == 4_052_300
    assert ut["prisantydning"] == 3_950_000
    assert ut["BRA_m2"] == 131


def test_belop_med_punktum_som_tusenskille():
    ut = hent_nokkeltall("Totalpris 3.950.000")
    assert ut["totalpris"] == 3_950_000


def test_belop_med_hardt_mellomrom():
    """PDF-uthenting gir ofte U+00A0 i stedet for vanlig mellomrom."""
    ut = hent_nokkeltall("Totalpris: 3 950 000")
    assert ut["totalpris"] == 3_950_000


def test_areal_med_desimal():
    ut = hent_nokkeltall("Bruksareal: 131,5 m2")
    assert ut["BRA_m2"] == 131.5


def test_fyllprikker_mellom_etikett_og_tall():
    ut = hent_nokkeltall("Prisantydning ......... kr 2 500 000")
    assert ut["prisantydning"] == 2_500_000


def test_henter_flere_felter():
    tekst = (
        "Prisantydning: 3 200 000\n"
        "BRA: 84 m2\n"
        "P-rom: 78 m2\n"
        "Felleskostnader: 3 500 per mnd\n"
        "Kommunale avgifter: 14 000 per år\n"
    )
    ut = hent_nokkeltall(tekst)

    assert ut["prisantydning"] == 3_200_000
    assert ut["BRA_m2"] == 84
    assert ut["p_rom_m2"] == 78
    assert ut["felleskostnader_mnd"] == 3_500
    assert ut["kommunale_avgifter_aar"] == 14_000


def test_tom_tekst_gir_tomt_resultat():
    assert hent_nokkeltall("") == {}


def test_ignorerer_urimelig_smaa_belop():
    """Et sidetall skal ikke tolkes som en kjøpesum."""
    assert "totalpris" not in hent_nokkeltall("Totalpris 42")


def test_ignorerer_urimelig_areal():
    assert "BRA_m2" not in hent_nokkeltall("BRA: 99999 m2")
