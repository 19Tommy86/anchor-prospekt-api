"""Tester for konnektorene. Ingen nettverkskall — httpx mockes."""

from datetime import UTC, datetime

import httpx
import pytest

from aina.cache import Cache
from aina.connectors.base import KildeUtilgjengelig
from aina.connectors.met import Vaerkonnektor, symbol_til_norsk
from aina.connectors.strompris import Strompriskonnektor

MET_SVAR = {
    "geometry": {"coordinates": [10.75, 59.91, 20]},
    "properties": {
        "meta": {"updated_at": "2026-01-15T11:00:00Z"},
        "timeseries": [
            {
                "time": "2026-01-15T12:00:00Z",
                "data": {
                    "instant": {
                        "details": {
                            "air_temperature": 7.2,
                            "wind_speed": 6.1,
                            "wind_from_direction": 315.0,
                        }
                    },
                    "next_1_hours": {
                        "summary": {"symbol_code": "lightrain"},
                        "details": {"precipitation_amount": 0.4},
                    },
                },
            }
        ],
    },
}


@pytest.fixture
def cache() -> Cache:
    c = Cache(":memory:")
    yield c
    c.lukk()


def _klient(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- vær ---------------------------------------------------------------------


def test_symbol_oversettes_til_norsk():
    assert symbol_til_norsk("lightrain_day") == "lett regn"
    assert symbol_til_norsk("partlycloudy_night") == "delvis skyet"
    assert symbol_til_norsk(None) == "ukjent"
    # Ukjent kode faller tilbake til koden selv i stedet for å skjule den
    assert symbol_til_norsk("noe_helt_nytt") == "noe"


async def test_vaer_forenkler_met_responsen(cache):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "User-Agent" in request.headers
        return httpx.Response(200, json=MET_SVAR, headers={"Last-Modified": "x"})

    k = Vaerkonnektor(
        cache, lat=59.9139, lon=10.7522, user_agent="aina/test (test@example.com)",
        klient=_klient(handler),
    )
    svar = await k.hent()

    punkt = svar.verdi["punkter"][0]
    assert punkt["temperatur"] == 7.2
    assert punkt["beskrivelse"] == "lett regn"
    assert punkt["nedbor_mm"] == 0.4
    assert svar.kilde == "nett"


async def test_vaer_403_gir_hjelpsom_beskjed(cache):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    # User-Agent uten kontaktinfo — nøyaktig det MET avviser.
    k = Vaerkonnektor(
        cache, lat=59.9, lon=10.7, user_agent="aina", klient=_klient(handler)
    )
    with pytest.raises(KildeUtilgjengelig, match="AINA_USER_AGENT"):
        await k.hent_ferskt()


async def test_vaer_bruker_lager_naar_met_er_nede(cache):
    async def nede(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("ingen rute til vert")

    k = Vaerkonnektor(
        cache, lat=59.9, lon=10.7, user_agent="aina/test", klient=_klient(nede)
    )
    cache.lagre(k.cache_nokkel(), {"punkter": []}, naa=datetime.now(UTC))
    svar = await k.hent()
    assert svar is not None and svar.kilde == "lager"


def test_vaer_runder_koordinater():
    """MET ber om maks 4 desimaler — flere gir unødig cache-spredning."""
    k = Vaerkonnektor(
        Cache(":memory:"), lat=59.913868, lon=10.752245, user_agent="aina/test"
    )
    assert k.lat == 59.9139
    assert k.lon == 10.7522


# --- strømpris ---------------------------------------------------------------


def test_ugyldig_prisomrade_avvises(cache):
    with pytest.raises(ValueError, match="NO"):
        Strompriskonnektor(cache, omraade="NO9")


def test_billigste_vindu_finner_laveste_snitt():
    timer = [
        {"fra": f"t{i}", "til": f"t{i+1}", "kr_per_kwh": pris}
        for i, pris in enumerate([1.2, 1.0, 0.4, 0.3, 0.2, 0.9, 1.5])
    ]
    vindu = Strompriskonnektor._billigste_vindu(timer, timer_lengde=3)
    assert vindu["fra"] == "t2"
    assert vindu["til"] == "t5"
    assert vindu["snitt_kr_per_kwh"] == pytest.approx(0.3)


def test_billigste_vindu_med_for_faa_timer():
    assert Strompriskonnektor._billigste_vindu([], timer_lengde=3) is None


async def test_strompris_uten_morgendagen_er_ikke_feil(cache):
    """Morgendagens priser publiseres først på ettermiddagen."""
    kall = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        kall["n"] += 1
        if kall["n"] == 1:
            return httpx.Response(
                200,
                json=[
                    {"time_start": "a", "time_end": "b", "NOK_per_kWh": 0.5},
                    {"time_start": "b", "time_end": "c", "NOK_per_kWh": 0.4},
                    {"time_start": "c", "time_end": "d", "NOK_per_kWh": 0.3},
                ],
            )
        return httpx.Response(404)

    k = Strompriskonnektor(cache, omraade="NO1", klient=_klient(handler))
    svar = await k.hent()
    assert len(svar.verdi["timer"]) == 3
    assert svar.verdi["billigste"] is not None
