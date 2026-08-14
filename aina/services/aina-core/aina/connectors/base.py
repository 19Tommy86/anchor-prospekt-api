"""Grensesnittet alle datakilder må oppfylle.

Regelen fra ADR 0001: en konnektor uten offline-vei godkjennes ikke. Derfor er
`hent_ferskt()` og `friskhet` abstrakte, og `hent()` er implementert her én gang
slik at ingen konnektor kan finne på å hoppe over cachen.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aina.cache import Cache, Friskhet, Oppslag

log = logging.getLogger(__name__)


class KildeUtilgjengelig(Exception):
    """Kilden svarte ikke. Ikke en feil — en forventet tilstand."""


@dataclass(frozen=True, slots=True)
class Svar:
    """Det konnektøren gir tilbake. Bærer alltid med seg alder og kilde."""

    verdi: Any
    hentet_kl: datetime
    kilde: str  # "nett" | "lager"
    er_gammelt: bool
    alder_tekst: str

    def til_dict(self) -> dict[str, Any]:
        return {
            "verdi": self.verdi,
            "hentet_kl": self.hentet_kl.isoformat(),
            "kilde": self.kilde,
            "er_gammelt": self.er_gammelt,
            "alder_tekst": self.alder_tekst,
        }


class Konnektor(ABC):
    """Basis for alle datakilder."""

    navn: str = "ukjent"

    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    @property
    @abstractmethod
    def friskhet(self) -> Friskhet: ...

    @property
    def tilgjengelig(self) -> bool:
        """False hvis konnektoren mangler nøkkel eller konfigurasjon.

        Mangler noe, melder konnektoren seg av — den skal ikke hindre oppstart.
        """
        return True

    @abstractmethod
    async def hent_ferskt(self) -> Any:
        """Hent fra kilden. Kaster KildeUtilgjengelig hvis den ikke svarer."""

    def cache_nokkel(self) -> str:
        return self.navn

    def hent_lagret(self, naa: datetime | None = None) -> Oppslag | None:
        return self.cache.hent(self.cache_nokkel(), self.friskhet, naa)

    async def hent(self, *, tillat_nett: bool = True) -> Svar | None:
        """Hovedveien inn. Returnerer None når vi ærlig talt ikke vet noe.

        Rekkefølge:
          1. Fersk cache          → bruk den, ikke plag kilden
          2. Nett tillatt         → prøv å hente, fall tilbake ved feil
          3. Gammel men brukbar   → bruk den, merket med alder
          4. For gammel / tom     → None. Aina sier «vet ikke».
        """
        naa = datetime.now(UTC)
        lagret = self.hent_lagret(naa)

        if lagret is not None and lagret.er_ferskt:
            return self._fra_lager(lagret)

        if tillat_nett and self.tilgjengelig:
            try:
                verdi = await self.hent_ferskt()
                self.cache.lagre(self.cache_nokkel(), verdi, naa)
                return Svar(
                    verdi=verdi,
                    hentet_kl=naa,
                    kilde="nett",
                    er_gammelt=False,
                    alder_tekst="nettopp",
                )
            except KildeUtilgjengelig as e:
                log.info("%s utilgjengelig, faller tilbake til lager: %s", self.navn, e)
            except Exception:
                log.exception("%s feilet uventet, faller tilbake til lager", self.navn)

        if lagret is not None and not lagret.er_ubrukelig:
            return self._fra_lager(lagret)

        return None

    @staticmethod
    def _fra_lager(oppslag: Oppslag) -> Svar:
        return Svar(
            verdi=oppslag.verdi,
            hentet_kl=oppslag.hentet_kl,
            kilde="lager",
            er_gammelt=oppslag.er_gammelt,
            alder_tekst=oppslag.alder_tekst,
        )
