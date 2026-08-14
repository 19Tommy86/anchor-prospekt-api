"""Husstandsprofilen — «hvem beskytter jeg».

Dette er den mest sensitive filen i systemet. Den ligger kryptert på disk,
committes aldri, og sendes aldri i sin helhet til en sky-modell.

Modellen er bevisst enkel og fullt lesbar som YAML. Går programvaren i stykker,
skal et menneske kunne åpne filen på en telefon og lese den.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Person:
    navn: str
    rolle: str = "beboer"  # voksen | barn | gjest | dyr
    fodselsaar: int | None = None
    telefon: str | None = None
    medisiner: list[str] = field(default_factory=list)
    allergier: list[str] = field(default_factory=list)
    merknad: str | None = None

    @property
    def er_sarbar(self) -> bool:
        """Krever ekstra hensyn ved evakuering eller strømbrudd."""
        return bool(self.medisiner) or self.rolle in {"barn", "dyr"}


@dataclass(slots=True)
class Sted:
    navn: str
    type: str  # tilfluktsrom | legevakt | apotek | vann | motepunkt | butikk | ...
    lat: float | None = None
    lon: float | None = None
    adresse: str | None = None
    avstand_km: float | None = None
    merknad: str | None = None


@dataclass(slots=True)
class Ressurs:
    navn: str
    mengde: float
    enhet: str
    kategori: str = "annet"  # mat | vann | drivstoff | medisin | ved | batteri
    holdbar_til: date | None = None
    forbruk_per_dogn: float | None = None

    def dogn_igjen(self) -> float | None:
        """Hvor lenge holder denne ressursen på oppgitt forbruk?"""
        if not self.forbruk_per_dogn:
            return None
        return round(self.mengde / self.forbruk_per_dogn, 1)

    def utlopt_om(self, idag: date | None = None) -> timedelta | None:
        if self.holdbar_til is None:
            return None
        return self.holdbar_til - (idag or date.today())


@dataclass(slots=True)
class Husstand:
    navn: str
    lat: float
    lon: float
    adresse: str | None = None
    kommune: str | None = None
    prisomrade: str = "NO1"
    personer: list[Person] = field(default_factory=list)
    steder: list[Sted] = field(default_factory=list)
    ressurser: list[Ressurs] = field(default_factory=list)
    motepunkt: str | None = None
    varmekilde: str | None = None
    v2l_kjoretoy: str | None = None
    batteri_kwh: float | None = None

    # -- oppslag som brukes både av panelet og av stemmesvarene ---------------

    def naermeste(self, type_: str) -> Sted | None:
        aktuelle = [
            s for s in self.steder if s.type == type_ and s.avstand_km is not None
        ]
        if not aktuelle:
            # Uten avstand kan vi fortsatt returnere første treff — bedre enn
            # ingenting når familien står i mørket.
            for s in self.steder:
                if s.type == type_:
                    return s
            return None
        return min(aktuelle, key=lambda s: s.avstand_km)  # type: ignore[arg-type]

    def sarbare_personer(self) -> list[Person]:
        return [p for p in self.personer if p.er_sarbar]

    def dogn_med_vann(self) -> float | None:
        """Liter vann delt på 3 liter per person per døgn (DSBs tommelfingerregel)."""
        liter = sum(r.mengde for r in self.ressurser if r.kategori == "vann")
        mennesker = len([p for p in self.personer if p.rolle != "dyr"])
        if not liter or not mennesker:
            return None
        return round(liter / (3.0 * mennesker), 1)

    def mangler(self) -> list[str]:
        """Hull i profilen. Aina skal mase om disse i fredstid.

        Et tomt møtepunkt er systemets viktigste manglende data — se docs/05.
        """
        hull: list[str] = []
        if not self.motepunkt:
            hull.append("Møtepunkt hvis familien blir adskilt er ikke satt")
        if not self.personer:
            hull.append("Ingen personer registrert")
        if not any(s.type == "tilfluktsrom" for s in self.steder):
            hull.append("Nærmeste tilfluktsrom er ikke registrert")
        if not any(r.kategori == "vann" for r in self.ressurser):
            hull.append("Ingen vannlagring registrert")
        if not self.varmekilde:
            hull.append("Alternativ varmekilde er ikke registrert")
        for p in self.personer:
            # Kun voksne — barn har ofte ikke egen telefon, og da er det ikke et
            # hull i profilen at feltet er tomt.
            if p.rolle == "voksen" and p.medisiner and not p.telefon:
                hull.append(f"{p.navn} bruker medisiner, men mangler telefonnummer")
        return hull


def _dato(verdi: Any) -> date | None:
    if verdi is None:
        return None
    if isinstance(verdi, date):
        return verdi
    return date.fromisoformat(str(verdi))


def last_husstand(sti: Path | str) -> Husstand:
    """Les husstandsprofilen fra YAML.

    Kaster FileNotFoundError hvis filen mangler — kalleren avgjør om det er
    fatalt. Kjernen skal starte uten profil, men da med reduserte svar.
    """
    data = yaml.safe_load(Path(sti).read_text(encoding="utf-8")) or {}

    return Husstand(
        navn=data.get("navn", "Husstanden"),
        lat=float(data["lat"]),
        lon=float(data["lon"]),
        adresse=data.get("adresse"),
        kommune=data.get("kommune"),
        prisomrade=data.get("prisomrade", "NO1"),
        motepunkt=data.get("motepunkt"),
        varmekilde=data.get("varmekilde"),
        v2l_kjoretoy=data.get("v2l_kjoretoy"),
        batteri_kwh=data.get("batteri_kwh"),
        personer=[Person(**p) for p in data.get("personer", [])],
        steder=[Sted(**s) for s in data.get("steder", [])],
        ressurser=[
            Ressurs(**{**r, "holdbar_til": _dato(r.get("holdbar_til"))})
            for r in data.get("ressurser", [])
        ],
    )
