"""Strømpriser per time.

Bruker hvakosterstrommen.no, som ikke krever nøkkel. Det er et bevisst valg:
etter regelen i docs/09 leter vi etter den nøkkelfrie veien først. Har kunden
Tibber, gir den mer (forbruk, Pulse i sanntid over LAN) — men prisen alene skal
ikke kreve et abonnement.

Morgendagens priser publiseres tidlig på ettermiddagen. Vi henter da og lagrer
dem, slik at «når er strømmen billigst i natt?» også kan besvares uten nett.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from aina.cache import Cache, Friskhet
from aina.connectors.base import KildeUtilgjengelig, Konnektor

URL = "https://www.hvakosterstrommen.no/api/v1/prices/{aar}/{maaned}-{dag}_{omraade}.json"

GYLDIGE_OMRADER = {"NO1", "NO2", "NO3", "NO4", "NO5"}


class Strompriskonnektor(Konnektor):
    navn = "strom.pris"

    def __init__(
        self,
        cache: Cache,
        *,
        omraade: str = "NO1",
        klient: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(cache)
        if omraade not in GYLDIGE_OMRADER:
            raise ValueError(f"Ukjent prisområde {omraade!r}, må være ett av {GYLDIGE_OMRADER}")
        self.omraade = omraade
        self._klient = klient

    @property
    def friskhet(self) -> Friskhet:
        # Prisene for et døgn endrer seg ikke etter publisering, så ttl kan være
        # lang. Etter to døgn er de derimot ubrukelige — da gjelder de i går.
        return Friskhet(
            ttl=timedelta(hours=6),
            stale_ok=timedelta(hours=20),
            max_useful=timedelta(days=2),
        )

    def cache_nokkel(self) -> str:
        return f"{self.navn}:{self.omraade}"

    async def hent_ferskt(self) -> dict[str, Any]:
        idag = datetime.now(UTC).date()
        priser = await self._hent_dag(idag)
        # Morgendagens priser finnes først etter publisering — mangler de, er det
        # ikke en feil.
        try:
            priser += await self._hent_dag(idag + timedelta(days=1))
        except KildeUtilgjengelig:
            pass

        return {
            "omraade": self.omraade,
            "timer": priser,
            "billigste": self._billigste_vindu(priser, timer_lengde=3),
        }

    async def _hent_dag(self, dag: Any) -> list[dict[str, Any]]:
        url = URL.format(
            aar=dag.year, maaned=f"{dag.month:02d}", dag=f"{dag.day:02d}", omraade=self.omraade
        )
        klient = self._klient or httpx.AsyncClient(timeout=10.0)
        try:
            svar = await klient.get(url)
        except httpx.HTTPError as e:
            raise KildeUtilgjengelig(f"Strømpris nås ikke: {e}") from e
        finally:
            if self._klient is None:
                await klient.aclose()

        if svar.status_code == 404:
            raise KildeUtilgjengelig(f"Ingen priser publisert for {dag}")
        if svar.status_code != 200:
            raise KildeUtilgjengelig(f"Strømpris-API svarte {svar.status_code}")

        return [
            {
                "fra": rad.get("time_start"),
                "til": rad.get("time_end"),
                "kr_per_kwh": rad.get("NOK_per_kWh"),
            }
            for rad in svar.json()
        ]

    @staticmethod
    def _billigste_vindu(
        timer: list[dict[str, Any]], *, timer_lengde: int = 3
    ) -> dict[str, Any] | None:
        """Finn det sammenhengende vinduet med lavest snittpris.

        Dette er svaret på «når skal jeg lade bilen i natt?».
        """
        gyldige = [t for t in timer if t.get("kr_per_kwh") is not None]
        if len(gyldige) < timer_lengde:
            return None

        beste_start = 0
        beste_snitt = float("inf")
        for i in range(len(gyldige) - timer_lengde + 1):
            vindu = gyldige[i : i + timer_lengde]
            snitt = sum(t["kr_per_kwh"] for t in vindu) / timer_lengde
            if snitt < beste_snitt:
                beste_snitt, beste_start = snitt, i

        return {
            "fra": gyldige[beste_start]["fra"],
            "til": gyldige[beste_start + timer_lengde - 1]["til"],
            "snitt_kr_per_kwh": round(beste_snitt, 4),
        }
