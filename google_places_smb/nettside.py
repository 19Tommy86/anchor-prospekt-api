"""
Nettside-generator (Fase 2)
===========================
Tar den strukturerte bedriftsdataen fra place_lookup.py og rendrer den
som en ferdig, selvstendig HTML-side.

Designvalg: vi bruker Jinja2 med autoescape=True. Dataene kommer fra en
ekstern API vi ikke kontrollerer, og skal plasseres rett inn i HTML.
Uten escaping kunne et bedriftsnavn som inneholder <script> injisere
kode på den genererte siden (XSS). Jinja2 håndterer dette automatisk —
derfor bygger vi IKKE HTML med f-strenger her.

Siden er bevisst selvstendig (all CSS inline i <style>): ingen eksterne
fonter, ingen CDN, ingen JavaScript. Det gjør at den laster raskt, virker
offline, og kan lagres som én enkelt .html-fil per bedrift senere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Mappen der .html-malene ligger, relativt til denne filen.
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Vi bygger Jinja2-miljøet én gang ved import (ikke per request), fordi
# innlasting og kompilering av maler er relativt dyrt.
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),  # <- XSS-beskyttelsen
    trim_blocks=True,
    lstrip_blocks=True,
)


def _del_apningstider(apningstider: list[str] | None) -> list[dict[str, str]]:
    """
    Google gir oss åpningstider som flate strenger:
        ["mandag: 08:00–16:00", "tirsdag: 08:00–16:00", ...]

    For å kunne vise dette som en pen tabell (dag i én kolonne, tid i
    en annen) splitter vi på første kolon. Hvis en linje mot formodning
    ikke har kolon, viser vi hele linjen som "dag" med tom tid — bedre
    enn å krasje eller droppe informasjonen.
    """
    if not apningstider:
        return []

    rader = []
    for linje in apningstider:
        dag, separator, tid = linje.partition(":")
        if separator:
            rader.append({"dag": dag.strip().capitalize(), "tid": tid.strip()})
        else:
            rader.append({"dag": linje.strip(), "tid": ""})
    return rader


def _stjerne_prosent(rating: float | None) -> float:
    """
    Regner om en rating (f.eks. 4.7) til hvor mange prosent av fem stjerner
    som skal være fylt: 4.7 / 5 = 94%.

    Malen tegner stjernene som to lag: fem grå stjerner i bunnen, og fem
    gule stjerner oppå som klippes til denne prosenten. Vi bruker denne
    teknikken i stedet for et eget halvstjerne-tegn (⯨, U+2BE8), fordi
    det tegnet mangler i mange fonter og da vises som en tom boks.
    Med CSS-klipping får vi presis visning som virker overalt.
    """
    if not rating:
        return 0.0
    # Klem verdien til 0–5 i tilfelle Google returnerer noe uventet.
    trygg = max(0.0, min(5.0, float(rating)))
    return round(trygg / 5 * 100, 2)


def _telefon_lenke(telefon: str | None) -> str | None:
    """
    Lager en klikkbar tel:-lenke. På mobil ringer denne bedriften direkte,
    som er den viktigste konverteringen for en lokal håndverker.

    Vi stripper mellomrom og bindestreker fordi tel:-URI-er skal være
    kompakte: "31 00 00 00" -> "tel:31000000"
    """
    if not telefon:
        return None
    return "tel:" + telefon.replace(" ", "").replace("-", "").replace(" ", "")


def render_bedriftsside(data: dict[str, Any]) -> str:
    """
    Hovedfunksjon: tar den strukturerte dataen fra hent_bedriftsdata()["data"]
    og returnerer ferdig HTML som én streng.
    """
    mal = _env.get_template("bedrift.html")
    return mal.render(
        firmanavn=data.get("firmanavn") or "Bedrift",
        adresse=data.get("adresse"),
        telefon=data.get("telefon"),
        telefon_lenke=_telefon_lenke(data.get("telefon")),
        apningstider=_del_apningstider(data.get("apningstider")),
        rating=data.get("rating"),
        stjerne_prosent=_stjerne_prosent(data.get("rating")),
        antall_anmeldelser=data.get("antall_anmeldelser"),
        google_maps_url=data.get("google_maps_url"),
        driftsstatus=data.get("driftsstatus"),
    )


def render_feilside(feilmelding: str, sokt_navn: str, sokt_by: str) -> str:
    """
    Rendrer en enkel feilside når oppslaget ikke gikk gjennom.
    Vi viser hva som ble søkt etter, slik at du raskt ser om det var
    en skrivefeil i navnet eller om bedriften faktisk mangler i Google.
    """
    mal = _env.get_template("feil.html")
    return mal.render(feilmelding=feilmelding, sokt_navn=sokt_navn, sokt_by=sokt_by)
