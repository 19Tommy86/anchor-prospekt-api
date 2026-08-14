"""Værvarsel fra MET Norway (api.met.no).

Ingen API-nøkkel. To ting er likevel obligatoriske etter MET sine vilkår, og
begge er implementert her:

  1. En identifiserende User-Agent med kontaktinfo. Kall uten dette blir avvist.
  2. Caching og betinget henting. Vi lagrer `Expires` og `Last-Modified` og
     sender `If-Modified-Since`, slik at vi ikke henter det samme igjen.

Vi lagrer hele 9-døgnsvarselet, ikke bare i dag. Det er hele offline-strategien:
går nettet kl. 07, har vi fortsatt en brukbar prognose for resten av uka — merket
med når den ble hentet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import httpx

from aina.cache import Cache, Friskhet
from aina.connectors.base import KildeUtilgjengelig, Konnektor

URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# Norske tekster for MET sine symbolkoder. Kun de vanligste — resten faller
# tilbake til koden selv, som er lesbar nok.
SYMBOLTEKST = {
    "clearsky": "klarvær",
    "fair": "lettskyet",
    "partlycloudy": "delvis skyet",
    "cloudy": "skyet",
    "fog": "tåke",
    "lightrain": "lett regn",
    "rain": "regn",
    "heavyrain": "kraftig regn",
    "lightsleet": "lett sludd",
    "sleet": "sludd",
    "lightsnow": "lett snø",
    "snow": "snø",
    "heavysnow": "kraftig snø",
    "rainshowers": "regnbyger",
    "snowshowers": "snøbyger",
    "thunderstorm": "tordenvær",
}


def symbol_til_norsk(symbol: str | None) -> str:
    if not symbol:
        return "ukjent"
    base = symbol.split("_")[0]
    return SYMBOLTEKST.get(base, base)


class Vaerkonnektor(Konnektor):
    navn = "vaer.met"

    def __init__(
        self,
        cache: Cache,
        *,
        lat: float,
        lon: float,
        altitude: int = 0,
        user_agent: str,
        klient: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(cache)
        self.lat = round(lat, 4)  # MET ber om maks 4 desimaler
        self.lon = round(lon, 4)
        self.altitude = altitude
        self.user_agent = user_agent
        self._klient = klient
        self._last_modified: str | None = None

    @property
    def friskhet(self) -> Friskhet:
        # Varselet oppdateres om lag hver time. Etter 12 timer merkes det som
        # gammelt, etter 9 døgn er det verdiløst — da har vi ikke lenger data
        # som dekker dagen i dag.
        return Friskhet(
            ttl=timedelta(hours=1),
            stale_ok=timedelta(hours=12),
            max_useful=timedelta(days=9),
        )

    def cache_nokkel(self) -> str:
        return f"{self.navn}:{self.lat},{self.lon}"

    async def hent_ferskt(self) -> dict[str, Any]:
        params = {"lat": self.lat, "lon": self.lon}
        if self.altitude:
            params["altitude"] = self.altitude

        headers = {"User-Agent": self.user_agent}
        if self._last_modified:
            headers["If-Modified-Since"] = self._last_modified

        klient = self._klient or httpx.AsyncClient(timeout=10.0)
        try:
            svar = await klient.get(URL, params=params, headers=headers)
        except httpx.HTTPError as e:
            raise KildeUtilgjengelig(f"MET nås ikke: {e}") from e
        finally:
            if self._klient is None:
                await klient.aclose()

        if svar.status_code == 304:
            raise KildeUtilgjengelig("Uendret siden sist (304)")
        if svar.status_code == 403:
            raise KildeUtilgjengelig(
                "MET avviste kallet (403). Sjekk at AINA_USER_AGENT har kontaktinfo."
            )
        if svar.status_code != 200:
            raise KildeUtilgjengelig(f"MET svarte {svar.status_code}")

        self._last_modified = svar.headers.get("Last-Modified")
        return self._forenkle(svar.json())

    @staticmethod
    def _forenkle(rådata: dict[str, Any]) -> dict[str, Any]:
        """Trekk ut det panelet og stemmen faktisk bruker.

        Vi lagrer et forenklet varsel i stedet for hele MET-responsen: mindre
        på disk, og uavhengig av at MET endrer felt vi ikke bruker.
        """
        serie = rådata.get("properties", {}).get("timeseries", [])
        punkter = []
        for punkt in serie[:216]:  # 9 døgn
            data = punkt.get("data", {})
            naa = data.get("instant", {}).get("details", {})
            neste_time = data.get("next_1_hours", {})
            neste_6 = data.get("next_6_hours", {})
            oppsummering = neste_time.get("summary") or neste_6.get("summary") or {}
            nedbor = (
                neste_time.get("details", {}).get("precipitation_amount")
                if neste_time
                else neste_6.get("details", {}).get("precipitation_amount")
            )
            punkter.append(
                {
                    "tid": punkt.get("time"),
                    "temperatur": naa.get("air_temperature"),
                    "vind": naa.get("wind_speed"),
                    "vindkast": naa.get("wind_speed_of_gust"),
                    "vindretning": naa.get("wind_from_direction"),
                    "symbol": oppsummering.get("symbol_code"),
                    "beskrivelse": symbol_til_norsk(oppsummering.get("symbol_code")),
                    "nedbor_mm": nedbor,
                }
            )

        return {
            "sted": rådata.get("geometry", {}).get("coordinates"),
            "oppdatert": rådata.get("properties", {})
            .get("meta", {})
            .get("updated_at"),
            "punkter": punkter,
        }
