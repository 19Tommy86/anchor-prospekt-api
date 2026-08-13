"""Beredskapsmotoren.

Systemets viktigste mekanisme. I stedet for at tjenester «feiler» når nett eller
strøm forsvinner, flytter Aina seg mellom fire definerte nivåer med hvert sitt
effektbudsjett, tjenestesett og svarpolicy.

Se ../../docs/02-arkitektur.md § Beredskapsnivåene og ADR 0001.

To regler som er lette å bomme på og som testene låser fast:

1. Nivået går **umiddelbart opp** ved forverring, men **med forsinkelse ned**
   igjen. Et flakkende nett skal ikke få systemet til å hoppe fram og tilbake.
2. Kortvarig nettbortfall (under `internett_grense`) utløser ikke nivåbytte i det
   hele tatt. En pakke som forsvinner er ikke en krise.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum


class Nivaa(IntEnum):
    """Høyere tall = mer alvorlig."""

    GRONN = 0
    GUL = 1
    ORANSJE = 2
    ROD = 3

    @property
    def etikett(self) -> str:
        return {
            Nivaa.GRONN: "ALT NORMALT",
            Nivaa.GUL: "UTEN INTERNETT",
            Nivaa.ORANSJE: "STRØMBRUDD",
            Nivaa.ROD: "KRITISK BATTERI",
        }[self]


@dataclass(frozen=True, slots=True)
class Systemtilstand:
    """Målt tilstand. Kommer fra nettverkssjekk, NUT/UPS og MQTT."""

    internett: bool = True
    lan: bool = True
    nettstrom: bool = True
    batteri_prosent: float | None = None
    uten_strom_siden: datetime | None = None

    def uten_strom_i(self, naa: datetime) -> timedelta:
        if self.nettstrom or self.uten_strom_siden is None:
            return timedelta(0)
        return naa - self.uten_strom_siden


@dataclass(frozen=True, slots=True)
class Nivaapolicy:
    """Hva som er tillatt på et gitt nivå."""

    nivaa: Nivaa
    effektbudsjett_w: int
    sky_tillatt: bool
    llm: str | None
    tjenester_av: tuple[str, ...]
    panel_lysstyrke: float
    forklaring: str


POLICY: dict[Nivaa, Nivaapolicy] = {
    Nivaa.GRONN: Nivaapolicy(
        nivaa=Nivaa.GRONN,
        effektbudsjett_w=0,  # 0 = ubegrenset
        sky_tillatt=True,
        llm="lokal+sky",
        tjenester_av=(),
        panel_lysstyrke=1.0,
        forklaring="Alt normalt. Alle konnektorer og modeller tilgjengelige.",
    ),
    Nivaa.GUL: Nivaapolicy(
        nivaa=Nivaa.GUL,
        effektbudsjett_w=0,
        sky_tillatt=False,
        llm="lokal",
        tjenester_av=("sky-modell", "backup-sync", "bakgrunnsindeksering"),
        panel_lysstyrke=1.0,
        forklaring=(
            "Uten internett. Lokal modell og lagrede data. Alle svar merkes "
            "med hvor gamle dataene er."
        ),
    ),
    Nivaa.ORANSJE: Nivaapolicy(
        nivaa=Nivaa.ORANSJE,
        effektbudsjett_w=25,
        sky_tillatt=False,
        llm="lokal-liten",
        tjenester_av=("sky-modell", "gpu", "whisper-medium", "indeksering", "video"),
        panel_lysstyrke=0.35,
        forklaring="Batteridrift. Redusert tjenestesett og dimmet panel.",
    ),
    Nivaa.ROD: Nivaapolicy(
        nivaa=Nivaa.ROD,
        effektbudsjett_w=10,
        sky_tillatt=False,
        llm=None,  # bevisst: ingen språkmodell i RØD
        tjenester_av=(
            "sky-modell",
            "gpu",
            "ollama",
            "whisper",
            "piper",
            "indeksering",
            "video",
        ),
        panel_lysstyrke=0.0,
        forklaring=(
            "Kritisk batteri. Kun oppslag, kart og forhåndsskrevne prosedyrer. "
            "Ingen språkmodell — familien skal få verifisert tekst, ikke generert."
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class Terskler:
    batteri_oransje: float = 60.0
    batteri_rod: float = 25.0
    internett_grense: timedelta = timedelta(seconds=60)
    langvarig_stromutfall: timedelta = timedelta(hours=24)
    nedtrapping: timedelta = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class Vurdering:
    nivaa: Nivaa
    policy: Nivaapolicy
    aarsak: str
    endret: bool
    gjenstaende_timer: float | None = None


def _naa() -> datetime:
    return datetime.now(UTC)


@dataclass
class Beredskapsmotor:
    """Holder nivået. Kall `vurder()` hver gang tilstanden måles."""

    terskler: Terskler = field(default_factory=Terskler)
    klokke: Callable[[], datetime] = _naa

    _nivaa: Nivaa = field(default=Nivaa.GRONN, init=False)
    _internett_nede_siden: datetime | None = field(default=None, init=False)
    _lavere_kandidat_siden: datetime | None = field(default=None, init=False)

    @property
    def nivaa(self) -> Nivaa:
        return self._nivaa

    def vurder(self, tilstand: Systemtilstand) -> Vurdering:
        naa = self.klokke()
        raatt, aarsak, stabil = self._raatt_nivaa(tilstand, naa)
        forrige = self._nivaa

        if raatt >= forrige:
            # Forverring, eller uendret: slår inn umiddelbart.
            self._nivaa = raatt
            self._lavere_kandidat_siden = None
        else:
            # Forbedring: må holde seg stabil gjennom hele nedtrappingsvinduet.
            # Et kortvarig tilbakefall er ikke alvorlig nok til å heve nivået,
            # men det nullstiller nedtrappingen — ellers vil et nett som blinker
            # av og på hvert minutt slippe systemet ned i GRØNN.
            if not stabil:
                self._lavere_kandidat_siden = naa
            elif self._lavere_kandidat_siden is None:
                self._lavere_kandidat_siden = naa
            if naa - self._lavere_kandidat_siden >= self.terskler.nedtrapping:
                self._nivaa = raatt
                self._lavere_kandidat_siden = None
                aarsak = f"{aarsak} (etter stabil bedring)"
            else:
                aarsak = (
                    f"Bedring registrert, holder {forrige.name} til nedtrappingen "
                    f"er over"
                )

        return Vurdering(
            nivaa=self._nivaa,
            policy=POLICY[self._nivaa],
            aarsak=aarsak,
            endret=self._nivaa != forrige,
            gjenstaende_timer=self.gjenstaende_timer(tilstand),
        )

    def _raatt_nivaa(
        self, tilstand: Systemtilstand, naa: datetime
    ) -> tuple[Nivaa, str, bool]:
        """Returnerer (nivå, årsak, stabil).

        `stabil` er False når noe er galt akkurat nå, selv om det ikke er galt
        lenge nok til å heve nivået. Den styrer nedtrappingen.
        """
        # Strøm slår alltid ut nett: batteriet er den harde begrensningen.
        if not tilstand.nettstrom:
            batteri = tilstand.batteri_prosent
            uten_strom = tilstand.uten_strom_i(naa)

            if batteri is not None and batteri <= self.terskler.batteri_rod:
                return Nivaa.ROD, f"Batteri {batteri:.0f} % — under kritisk terskel", False
            if uten_strom >= self.terskler.langvarig_stromutfall:
                timer = uten_strom.total_seconds() / 3600
                return (
                    Nivaa.ROD,
                    f"Uten nettstrøm i {timer:.0f} timer — sparer batteri",
                    False,
                )
            if batteri is None:
                # Ukjent batterinivå på batteridrift: anta det verste.
                return Nivaa.ORANSJE, "Nettstrøm borte, batterinivå ukjent", False
            return Nivaa.ORANSJE, f"Nettstrøm borte, batteri {batteri:.0f} %", False

        # Nettstrøm OK herfra.
        if not tilstand.internett:
            if self._internett_nede_siden is None:
                self._internett_nede_siden = naa
            nede = naa - self._internett_nede_siden
            if nede >= self.terskler.internett_grense:
                return Nivaa.GUL, f"Uten internett i {int(nede.total_seconds())} s", False
            return Nivaa.GRONN, "Kortvarig nettbortfall — ignorert", False

        self._internett_nede_siden = None
        return Nivaa.GRONN, "Alt normalt", True

    def gjenstaende_timer(
        self, tilstand: Systemtilstand, kapasitet_wh: float = 1150.0
    ) -> float | None:
        """Grovt anslag på driftstid igjen på batteri.

        Bruker effektbudsjettet for nivået som ville gjeldt. Bevisst konservativt:
        et for optimistisk anslag er verre enn ingen anslag.
        """
        if tilstand.nettstrom or tilstand.batteri_prosent is None:
            return None
        budsjett = POLICY[self._nivaa].effektbudsjett_w or 30
        tilgjengelig_wh = kapasitet_wh * (tilstand.batteri_prosent / 100.0)
        return round(tilgjengelig_wh / budsjett, 1)


def tjeneste_tillatt(nivaa: Nivaa, tjeneste: str) -> bool:
    return tjeneste not in POLICY[nivaa].tjenester_av
