"""Lokal cache med «stale-while-offline».

En vanlig cache kaster data når de blir gamle. Denne gjør det motsatte: den
beholder dem, men merker dem. Uten nett er et 14 timer gammelt værvarsel det
beste vi har — og det er nyttig, så lenge brukeren får vite at det er 14 timer
gammelt.

Tre terskler per datasett (se ../../docs/02-arkitektur.md § Datakontrakt):

    ttl         under denne: ferskt, ikke hent på nytt
    stale_ok    mellom ttl og denne: brukes, men merkes som gammelt
    max_useful  over denne: brukes ikke. Aina sier «vet ikke» i stedet for å gjette.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_SKJEMA = """
CREATE TABLE IF NOT EXISTS cache (
    nokkel     TEXT PRIMARY KEY,
    verdi      TEXT NOT NULL,
    hentet_kl  TEXT NOT NULL,
    kilde      TEXT NOT NULL DEFAULT 'nett'
);
"""


@dataclass(frozen=True, slots=True)
class Friskhet:
    ttl: timedelta
    stale_ok: timedelta
    max_useful: timedelta

    def __post_init__(self) -> None:
        if not (self.ttl <= self.stale_ok <= self.max_useful):
            raise ValueError("Krever ttl <= stale_ok <= max_useful")


@dataclass(frozen=True, slots=True)
class Oppslag:
    """Et cachet svar, med alt brukergrensesnittet trenger for å være ærlig."""

    verdi: Any
    hentet_kl: datetime
    alder: timedelta
    er_ferskt: bool
    er_gammelt: bool
    er_ubrukelig: bool

    @property
    def alder_tekst(self) -> str:
        s = int(self.alder.total_seconds())
        if s < 90:
            return "nettopp"
        if s < 5400:
            return f"{s // 60} min gammelt"
        if s < 172800:
            return f"{s // 3600} t gammelt"
        return f"{s // 86400} døgn gammelt"

    def til_dict(self) -> dict[str, Any]:
        return {
            "verdi": self.verdi,
            "hentet_kl": self.hentet_kl.isoformat(),
            "alder_sekunder": int(self.alder.total_seconds()),
            "alder_tekst": self.alder_tekst,
            "er_gammelt": self.er_gammelt,
        }


class Cache:
    """Trådsikker SQLite-cache. Bevisst enkel — den skal overleve strømbrudd."""

    def __init__(self, sti: Path | str = ":memory:") -> None:
        if sti != ":memory:":
            Path(sti).parent.mkdir(parents=True, exist_ok=True)
        self._laas = threading.Lock()
        self._db = sqlite3.connect(str(sti), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(_SKJEMA)
        self._db.commit()

    def lagre(self, nokkel: str, verdi: Any, naa: datetime | None = None) -> None:
        naa = naa or datetime.now(UTC)
        with self._laas:
            self._db.execute(
                "INSERT INTO cache (nokkel, verdi, hentet_kl) VALUES (?, ?, ?) "
                "ON CONFLICT(nokkel) DO UPDATE SET verdi=excluded.verdi, "
                "hentet_kl=excluded.hentet_kl",
                (nokkel, json.dumps(verdi, ensure_ascii=False), naa.isoformat()),
            )
            self._db.commit()

    def hent(
        self, nokkel: str, friskhet: Friskhet, naa: datetime | None = None
    ) -> Oppslag | None:
        naa = naa or datetime.now(UTC)
        with self._laas:
            rad = self._db.execute(
                "SELECT verdi, hentet_kl FROM cache WHERE nokkel = ?", (nokkel,)
            ).fetchone()
        if rad is None:
            return None

        hentet_kl = datetime.fromisoformat(rad[1])
        alder = naa - hentet_kl
        return Oppslag(
            verdi=json.loads(rad[0]),
            hentet_kl=hentet_kl,
            alder=alder,
            er_ferskt=alder <= friskhet.ttl,
            er_gammelt=alder > friskhet.ttl,
            er_ubrukelig=alder > friskhet.max_useful,
        )

    def slett(self, nokkel: str) -> None:
        with self._laas:
            self._db.execute("DELETE FROM cache WHERE nokkel = ?", (nokkel,))
            self._db.commit()

    def lukk(self) -> None:
        with self._laas:
            self._db.close()
