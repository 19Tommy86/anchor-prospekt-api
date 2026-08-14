"""Tester for husstandsprofilen.

Inkludert en test som leser den ekte eksempelfilen — hvis eksempelet råtner,
gjør oppsettsveiviseren det også.
"""

from pathlib import Path

import pytest

from aina.knowledge import Husstand, Person, Ressurs, Sted, last_husstand

EKSEMPEL = Path(__file__).resolve().parents[3] / "packs" / "husstand.example.yaml"


@pytest.fixture
def husstand() -> Husstand:
    return Husstand(
        navn="Familien Test",
        lat=59.9,
        lon=10.7,
        motepunkt="Flaggstanga",
        varmekilde="Vedovn",
        personer=[
            Person(navn="Voksen", rolle="voksen", telefon="+4790000000"),
            Person(navn="Barn", rolle="barn"),
            Person(navn="Hund", rolle="dyr"),
        ],
        steder=[
            Sted(navn="Fjern", type="tilfluktsrom", avstand_km=4.0),
            Sted(navn="Nær", type="tilfluktsrom", avstand_km=1.1),
        ],
        ressurser=[
            Ressurs(navn="Vann", kategori="vann", mengde=60, enhet="liter",
                    forbruk_per_dogn=6),
        ],
    )


def test_naermeste_velger_korteste_avstand(husstand):
    assert husstand.naermeste("tilfluktsrom").navn == "Nær"


def test_naermeste_uten_treff(husstand):
    assert husstand.naermeste("legevakt") is None


def test_naermeste_uten_avstand_gir_forste_treff():
    h = Husstand(navn="T", lat=0, lon=0, steder=[Sted(navn="Ukjent", type="vann")])
    assert h.naermeste("vann").navn == "Ukjent"


def test_barn_og_dyr_regnes_som_sarbare(husstand):
    navn = {p.navn for p in husstand.sarbare_personer()}
    assert navn == {"Barn", "Hund"}


def test_medisinbruk_gjor_voksen_sarbar():
    p = Person(navn="V", rolle="voksen", medisiner=["insulin"])
    assert p.er_sarbar


def test_dogn_med_vann_teller_ikke_dyr(husstand):
    # 60 liter / (3 l x 2 mennesker) = 10 døgn
    assert husstand.dogn_med_vann() == 10.0


def test_ressurs_regner_ut_dogn_igjen():
    r = Ressurs(navn="Vann", kategori="vann", mengde=60, enhet="l", forbruk_per_dogn=12)
    assert r.dogn_igjen() == 5.0


def test_ressurs_uten_forbruk_gir_none():
    assert Ressurs(navn="Ved", mengde=2, enhet="favner").dogn_igjen() is None


def test_mangler_finner_hull():
    h = Husstand(navn="Tom", lat=0, lon=0)
    hull = h.mangler()
    assert any("Møtepunkt" in m for m in hull)
    assert any("tilfluktsrom" in m for m in hull)
    assert any("Vann" in m or "vann" in m for m in hull)


def test_utfylt_husstand_mangler_mindre(husstand):
    assert not any("Møtepunkt" in m for m in husstand.mangler())


def test_mangler_varsler_om_medisin_uten_telefon():
    h = Husstand(
        navn="T", lat=0, lon=0,
        personer=[Person(navn="Kari", rolle="voksen", medisiner=["insulin"])],
    )
    assert any("Kari" in m and "telefon" in m for m in h.mangler())


def test_eksempelfilen_kan_lastes():
    h = last_husstand(EKSEMPEL)
    assert h.navn == "Familien Pedersen"
    assert h.motepunkt
    assert len(h.personer) == 5
    assert h.naermeste("tilfluktsrom") is not None
    assert h.dogn_med_vann() == 5.0  # 60 l / (3 l x 4 mennesker)


def test_eksempelfilen_er_komplett():
    """Eksempelet skal vise hvordan en ferdig utfylt profil ser ut."""
    hull = last_husstand(EKSEMPEL).mangler()
    assert hull == [], f"Eksempelfilen har hull: {hull}"


def test_manglende_fil_kaster():
    with pytest.raises(FileNotFoundError):
        last_husstand("/finnes/ikke.yaml")
