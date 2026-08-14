"""Tester for cachen og konnektor-fallbacken.

Kjernepåstanden som testes: uten nett skal Aina svare med lagrede data og si
hvor gamle de er — helt til de er så gamle at et ærlig «vet ikke» er riktigere.
"""

from datetime import UTC, datetime, timedelta

import pytest

from aina.cache import Cache, Friskhet
from aina.connectors.base import KildeUtilgjengelig, Konnektor

FRISKHET = Friskhet(
    ttl=timedelta(hours=1),
    stale_ok=timedelta(hours=12),
    max_useful=timedelta(days=2),
)
NAA = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


@pytest.fixture
def cache() -> Cache:
    c = Cache(":memory:")
    yield c
    c.lukk()


def test_tomt_oppslag_gir_none(cache):
    assert cache.hent("finnes-ikke", FRISKHET) is None


def test_ferskt_oppslag(cache):
    cache.lagre("v", {"temp": 7}, naa=NAA)
    o = cache.hent("v", FRISKHET, naa=NAA + timedelta(minutes=10))
    assert o.verdi == {"temp": 7}
    assert o.er_ferskt and not o.er_gammelt and not o.er_ubrukelig


def test_gammelt_men_brukbart(cache):
    cache.lagre("v", {"temp": 7}, naa=NAA)
    o = cache.hent("v", FRISKHET, naa=NAA + timedelta(hours=5))
    assert o.er_gammelt and not o.er_ubrukelig
    assert o.alder_tekst == "5 t gammelt"


def test_for_gammelt_markeres_ubrukelig(cache):
    cache.lagre("v", {"temp": 7}, naa=NAA)
    o = cache.hent("v", FRISKHET, naa=NAA + timedelta(days=3))
    assert o.er_ubrukelig


def test_overskriving(cache):
    cache.lagre("v", 1, naa=NAA)
    cache.lagre("v", 2, naa=NAA + timedelta(minutes=5))
    assert cache.hent("v", FRISKHET, naa=NAA + timedelta(minutes=6)).verdi == 2


@pytest.mark.parametrize(
    ("delta", "forventet"),
    [
        (timedelta(seconds=30), "nettopp"),
        (timedelta(minutes=20), "20 min gammelt"),
        (timedelta(hours=14), "14 t gammelt"),
        (timedelta(days=3), "3 døgn gammelt"),
    ],
)
def test_alderstekst(cache, delta, forventet):
    cache.lagre("v", 1, naa=NAA)
    assert cache.hent("v", FRISKHET, naa=NAA + delta).alder_tekst == forventet


# --- konnektor-fallback ------------------------------------------------------


class FalskKonnektor(Konnektor):
    navn = "test"

    def __init__(self, cache: Cache, *, feiler: bool = False) -> None:
        super().__init__(cache)
        self.feiler = feiler
        self.antall_kall = 0

    @property
    def friskhet(self) -> Friskhet:
        return FRISKHET

    async def hent_ferskt(self):
        self.antall_kall += 1
        if self.feiler:
            raise KildeUtilgjengelig("nede")
        return {"fra": "nett"}


async def test_henter_fra_nett_naar_cachen_er_tom(cache):
    k = FalskKonnektor(cache)
    svar = await k.hent()
    assert svar.kilde == "nett"
    assert not svar.er_gammelt


async def test_fersk_cache_sparer_kilden(cache):
    k = FalskKonnektor(cache)
    await k.hent()
    await k.hent()
    assert k.antall_kall == 1


async def test_faller_tilbake_til_lager_naar_kilden_er_nede(cache):
    k = FalskKonnektor(cache)
    await k.hent()

    nede = FalskKonnektor(cache, feiler=True)
    cache.lagre("test", {"fra": "nett"}, naa=datetime.now(UTC) - timedelta(hours=5))
    svar = await nede.hent()

    assert svar is not None
    assert svar.kilde == "lager"
    assert svar.er_gammelt


async def test_uten_nett_hoppes_kilden_helt_over(cache):
    k = FalskKonnektor(cache)
    await k.hent()
    cache.lagre("test", {"fra": "nett"}, naa=datetime.now(UTC) - timedelta(hours=5))

    før = k.antall_kall
    svar = await k.hent(tillat_nett=False)
    assert k.antall_kall == før
    assert svar.kilde == "lager"


async def test_vet_ikke_naar_alt_er_for_gammelt(cache):
    """Aina skal si «vet ikke» heller enn å presentere gammelt som ferskt."""
    k = FalskKonnektor(cache, feiler=True)
    cache.lagre("test", {"fra": "nett"}, naa=datetime.now(UTC) - timedelta(days=5))
    assert await k.hent() is None


def test_friskhet_validerer_rekkefolge():
    with pytest.raises(ValueError):
        Friskhet(
            ttl=timedelta(hours=5),
            stale_ok=timedelta(hours=1),
            max_useful=timedelta(days=1),
        )
