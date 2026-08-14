"""HTTP-grensesnittet mot panelet, stemmelaget og mobil.

Merk hvordan hvert svar bærer `beredskapsnivaa` og datas alder. Panelet skal
aldri måtte gjette hvor gammelt noe er — se docs/06 § designregel 3.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from aina.cache import Cache
from aina.config import Innstillinger, hent_innstillinger
from aina.connectors import Strompriskonnektor, Vaerkonnektor
from aina.knowledge import Husstand, last_husstand
from aina.readiness import Beredskapsmotor, Systemtilstand, Terskler

log = logging.getLogger(__name__)


class Tilstand:
    """Alt kjernen deler. Holdes samlet ett sted for enkel testing."""

    def __init__(self, innst: Innstillinger) -> None:
        self.innst = innst
        self.cache = Cache(innst.cache_sti)
        self.motor = Beredskapsmotor(
            terskler=Terskler(
                batteri_oransje=innst.aina_batteri_oransje,
                batteri_rod=innst.aina_batteri_rod,
            )
        )
        self.system = Systemtilstand()
        self.husstand: Husstand | None = self._last_husstand()

        lat = self.husstand.lat if self.husstand else innst.aina_lat
        lon = self.husstand.lon if self.husstand else innst.aina_lon
        omraade = self.husstand.prisomrade if self.husstand else innst.aina_prisomrade

        self.vaer = Vaerkonnektor(
            self.cache,
            lat=lat,
            lon=lon,
            altitude=innst.aina_altitude,
            user_agent=innst.aina_user_agent,
        )
        self.strompris = Strompriskonnektor(self.cache, omraade=omraade)

    def _last_husstand(self) -> Husstand | None:
        try:
            return last_husstand(self.innst.aina_household_pack)
        except FileNotFoundError:
            log.warning(
                "Ingen husstandsprofil på %s — kjernen starter med reduserte svar. "
                "Kopier packs/husstand.example.yaml og fyll den ut.",
                self.innst.aina_household_pack,
            )
            return None
        except Exception:
            log.exception("Husstandsprofilen kunne ikke leses")
            return None

    @property
    def tillat_nett(self) -> bool:
        return self.system.internett


tilstand: Tilstand | None = None


def hent_tilstand() -> Tilstand:
    if tilstand is None:
        raise HTTPException(503, "Kjernen er ikke startet")
    return tilstand


@asynccontextmanager
async def livssyklus(app: FastAPI):
    global tilstand
    innst = hent_innstillinger()
    logging.basicConfig(level=innst.aina_log_level)
    tilstand = Tilstand(innst)
    log.info("Aina-kjernen startet, node=%s", innst.aina_node_id)
    yield
    tilstand.cache.lukk()


app = FastAPI(
    title="Aina Core",
    description="Offline-first hjem- og beredskapsassistent",
    version="0.1.0",
    lifespan=livssyklus,
)


@app.get("/api/status")
async def status() -> dict[str, Any]:
    t = hent_tilstand()
    v = t.motor.vurder(t.system)
    return {
        "node": t.innst.aina_node_id,
        "beredskapsnivaa": v.nivaa.name,
        "etikett": v.nivaa.etikett,
        "aarsak": v.aarsak,
        "forklaring": v.policy.forklaring,
        "sky_tillatt": v.policy.sky_tillatt and t.innst.aina_cloud_allowed,
        "modell": v.policy.llm,
        "panel_lysstyrke": v.policy.panel_lysstyrke,
        "gjenstaende_timer": v.gjenstaende_timer,
        "husstand": t.husstand.navn if t.husstand else None,
        "system": {
            "internett": t.system.internett,
            "nettstrom": t.system.nettstrom,
            "batteri_prosent": t.system.batteri_prosent,
        },
    }


@app.post("/api/system/tilstand")
async def sett_systemtilstand(ny: dict[str, Any]) -> dict[str, Any]:
    """Kalles av nettverkssjekken og UPS-overvåkingen.

    Skilt ut som et endepunkt slik at nivåbytte kan testes for hånd — noe man
    bør gjøre jevnlig, ikke bare den dagen det gjelder.
    """
    t = hent_tilstand()
    t.system = Systemtilstand(
        internett=ny.get("internett", True),
        lan=ny.get("lan", True),
        nettstrom=ny.get("nettstrom", True),
        batteri_prosent=ny.get("batteri_prosent"),
    )
    v = t.motor.vurder(t.system)
    if v.endret:
        log.warning("Beredskapsnivå → %s: %s", v.nivaa.name, v.aarsak)
    return {"beredskapsnivaa": v.nivaa.name, "endret": v.endret, "aarsak": v.aarsak}


@app.get("/api/vaer")
async def vaer() -> dict[str, Any]:
    t = hent_tilstand()
    svar = await t.vaer.hent(tillat_nett=t.tillat_nett)
    if svar is None:
        raise HTTPException(
            503,
            "Jeg har ikke noe brukbart værvarsel. Siste henting er for gammel til "
            "å si noe om i dag.",
        )
    return svar.til_dict()


@app.get("/api/strompris")
async def strompris() -> dict[str, Any]:
    t = hent_tilstand()
    svar = await t.strompris.hent(tillat_nett=t.tillat_nett)
    if svar is None:
        raise HTTPException(503, "Jeg har ingen gyldige strømpriser lagret.")
    return svar.til_dict()


@app.get("/api/husstand")
async def husstand() -> dict[str, Any]:
    """Oppsummering, ikke rådata.

    Fullstendige personopplysninger eksponeres ikke over API-et — panelet
    trenger dem ikke, og en tynn klient skal ikke lagre dem. Se docs/07 § T1.
    """
    t = hent_tilstand()
    if t.husstand is None:
        raise HTTPException(404, "Ingen husstandsprofil er lastet")
    h = t.husstand
    return {
        "navn": h.navn,
        "kommune": h.kommune,
        "antall_personer": len(h.personer),
        "sarbare": [p.navn for p in h.sarbare_personer()],
        "motepunkt": h.motepunkt,
        "varmekilde": h.varmekilde,
        "dogn_med_vann": h.dogn_med_vann(),
        "naermeste_tilfluktsrom": _sted(h.naermeste("tilfluktsrom")),
        "naermeste_legevakt": _sted(h.naermeste("legevakt")),
        "mangler": h.mangler(),
    }


@app.get("/api/beredskap/sjekk")
async def beredskapssjekk() -> dict[str, Any]:
    """Hva mangler for at systemet skal virke i krise?

    Kjøres i fredstid. Målet er at lista skal være tom.
    """
    t = hent_tilstand()
    hull: list[str] = []
    if t.husstand is None:
        hull.append("Husstandsprofilen er ikke fylt ut")
    else:
        hull.extend(t.husstand.mangler())
    if t.vaer.hent_lagret() is None:
        hull.append("Ingen værvarsel er lagret lokalt ennå")
    if t.system.batteri_prosent is None:
        hull.append("Batteriovervåking er ikke koblet til — nivå RØD kan ikke utløses")
    return {"klar": not hull, "mangler": hull}


def _sted(s: Any) -> dict[str, Any] | None:
    if s is None:
        return None
    return {
        "navn": s.navn,
        "adresse": s.adresse,
        "avstand_km": s.avstand_km,
        "merknad": s.merknad,
    }
