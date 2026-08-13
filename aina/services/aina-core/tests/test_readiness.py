"""Tester for beredskapsmotoren.

Disse låser fast oppførselen som er lett å ødelegge ved senere endringer:
hysterese, at strøm slår ut nett, og at RØD ikke har språkmodell.
"""

from datetime import UTC, datetime, timedelta

import pytest

from aina.readiness import (
    Beredskapsmotor,
    Nivaa,
    Systemtilstand,
    Terskler,
    tjeneste_tillatt,
)


class Klokke:
    def __init__(self, start: datetime | None = None) -> None:
        self.naa = start or datetime(2026, 1, 15, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.naa

    def gaa(self, **kwargs) -> None:
        self.naa += timedelta(**kwargs)


@pytest.fixture
def klokke() -> Klokke:
    return Klokke()


@pytest.fixture
def motor(klokke: Klokke) -> Beredskapsmotor:
    return Beredskapsmotor(klokke=klokke)


def test_alt_normalt_gir_gronn(motor):
    v = motor.vurder(Systemtilstand())
    assert v.nivaa is Nivaa.GRONN
    assert v.policy.sky_tillatt


def test_kortvarig_nettbortfall_ignoreres(motor, klokke):
    """En tapt pakke er ikke en krise."""
    assert motor.vurder(Systemtilstand(internett=False)).nivaa is Nivaa.GRONN
    klokke.gaa(seconds=30)
    assert motor.vurder(Systemtilstand(internett=False)).nivaa is Nivaa.GRONN


def test_vedvarende_nettbortfall_gir_gul(motor, klokke):
    motor.vurder(Systemtilstand(internett=False))
    klokke.gaa(seconds=61)
    v = motor.vurder(Systemtilstand(internett=False))
    assert v.nivaa is Nivaa.GUL
    assert not v.policy.sky_tillatt
    assert v.policy.llm == "lokal"


def test_stromutfall_gir_oransje(motor):
    v = motor.vurder(Systemtilstand(nettstrom=False, batteri_prosent=85))
    assert v.nivaa is Nivaa.ORANSJE
    assert v.policy.panel_lysstyrke < 1.0
    assert "gpu" in v.policy.tjenester_av


def test_strom_slaar_ut_nett(motor):
    """Med strøm borte spiller det ingen rolle at internett virker."""
    v = motor.vurder(Systemtilstand(internett=True, nettstrom=False, batteri_prosent=90))
    assert v.nivaa is Nivaa.ORANSJE


def test_ukjent_batteri_paa_batteridrift_antar_det_verste(motor):
    v = motor.vurder(Systemtilstand(nettstrom=False, batteri_prosent=None))
    assert v.nivaa is Nivaa.ORANSJE
    assert "ukjent" in v.aarsak


def test_lavt_batteri_gir_rod_uten_sprakmodell(motor):
    v = motor.vurder(Systemtilstand(nettstrom=False, batteri_prosent=20))
    assert v.nivaa is Nivaa.ROD
    # Det viktigste enkeltkravet i hele modulen, jf. ADR 0001 punkt 5.
    assert v.policy.llm is None
    assert not tjeneste_tillatt(Nivaa.ROD, "ollama")


def test_langvarig_stromutfall_gir_rod_selv_med_godt_batteri(motor, klokke):
    startet = klokke.naa - timedelta(hours=25)
    v = motor.vurder(
        Systemtilstand(nettstrom=False, batteri_prosent=80, uten_strom_siden=startet)
    )
    assert v.nivaa is Nivaa.ROD


def test_forverring_slaar_inn_umiddelbart(motor):
    motor.vurder(Systemtilstand(nettstrom=False, batteri_prosent=70))
    v = motor.vurder(Systemtilstand(nettstrom=False, batteri_prosent=10))
    assert v.nivaa is Nivaa.ROD
    assert v.endret


def test_bedring_krever_stabil_periode(motor, klokke):
    """Flakkende nett skal ikke få systemet til å hoppe."""
    motor.vurder(Systemtilstand(internett=False))
    klokke.gaa(seconds=61)
    assert motor.vurder(Systemtilstand(internett=False)).nivaa is Nivaa.GUL

    # Nettet kommer tilbake — men vi blir i GUL til nedtrappingen er over.
    assert motor.vurder(Systemtilstand()).nivaa is Nivaa.GUL
    klokke.gaa(minutes=2)
    assert motor.vurder(Systemtilstand()).nivaa is Nivaa.GUL
    klokke.gaa(minutes=4)
    v = motor.vurder(Systemtilstand())
    assert v.nivaa is Nivaa.GRONN
    assert v.endret


def test_flakkende_nett_nullstiller_nedtrappingen(motor, klokke):
    motor.vurder(Systemtilstand(internett=False))
    klokke.gaa(seconds=61)
    motor.vurder(Systemtilstand(internett=False))

    klokke.gaa(minutes=4)
    motor.vurder(Systemtilstand())  # nettet blinker tilbake
    klokke.gaa(minutes=1)
    motor.vurder(Systemtilstand(internett=False))  # ...og faller igjen
    klokke.gaa(minutes=4)
    # Nedtrappingen startet på nytt, så vi er fortsatt i GUL.
    assert motor.vurder(Systemtilstand()).nivaa is Nivaa.GUL


def test_gjenstaende_timer_er_konservativt(motor):
    tilstand = Systemtilstand(nettstrom=False, batteri_prosent=100)
    v = motor.vurder(tilstand)
    # 1150 Wh / 25 W effektbudsjett ≈ 46 timer
    assert v.gjenstaende_timer is not None
    assert 40 < v.gjenstaende_timer < 50


def test_gjenstaende_timer_er_none_paa_nettstrom(motor):
    assert motor.vurder(Systemtilstand()).gjenstaende_timer is None


def test_egne_terskler_respekteres(klokke):
    motor = Beredskapsmotor(terskler=Terskler(batteri_rod=50.0), klokke=klokke)
    assert motor.vurder(
        Systemtilstand(nettstrom=False, batteri_prosent=45)
    ).nivaa is Nivaa.ROD
