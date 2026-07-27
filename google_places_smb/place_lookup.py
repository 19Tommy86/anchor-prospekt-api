"""
Google Places SMB Data Fetcher
================================
Fase 1 av "auto-generer nettside for lokale bedrifter"-prosjektet.

Formål: Ta imot bedriftsnavn + by, slå opp bedriften i Google Places API,
og returnere en ren, strukturert JSON-blokk med de 5 datapunktene vi
trenger for å generere en nettside:
    1. Firmanavn
    2. Full adresse
    3. Telefonnummer
    4. Åpningstider
    5. Rating + antall anmeldelser

Arkitektur (MVP, "legacy" Places API):
    Steg 1: "Find Place From Text" -> finner Place ID ut fra fritekst-søk
            (billigere og mer presist enn Text Search når vi allerede vet
            navn + by, siden vi kun ber om ett treff).
    Steg 2: "Place Details" -> henter de faktiske feltene vi trenger,
            basert på Place ID fra steg 1.

Vi bruker den "klassiske" Places API (maps.googleapis.com/maps/api/place/...)
fordi den er enklest å komme i gang med for en MVP og krever minimal
autentisering (kun API-nøkkel i URL). Når appen skal skaleres bør man
vurdere å migrere til "Places API (New)" (places.googleapis.com), som har
bedre feltmasker og lavere pris per kall for enkelte felt-kombinasjoner.

Kjøre fra terminal:
    python place_lookup.py "Hansen Rørleggerservice" "Horten"

Kjøre som modul i eget script:
    from place_lookup import hent_bedriftsdata
    resultat = hent_bedriftsdata("Hansen Rørleggerservice", "Horten")
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import requests

# --- Konfigurasjon -----------------------------------------------------
# API-nøkkelen skal ALDRI hardkodes i koden. Vi leser den fra miljøvariabelen
# GOOGLE_PLACES_API_KEY. Se .env.example for hvordan du setter denne opp.
API_KEY_ENV_VAR = "GOOGLE_PLACES_API_KEY"

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Timeout i sekunder for HTTP-kall. Viktig å ha en grense slik at scriptet
# ikke henger for evig hvis Google sine servere er trege.
HTTP_TIMEOUT_SEKUNDER = 10

# Feltene vi ber Google Details-endepunktet om. Å spesifisere "fields"
# eksplisitt (i stedet for å hente alt) reduserer kostnaden per API-kall.
DETAILS_FELTER = ",".join(
    [
        "name",
        "formatted_address",
        "formatted_phone_number",
        "international_phone_number",
        "opening_hours",
        "rating",
        "user_ratings_total",
        "place_id",
        "url",  # lenke til bedriften på Google Maps
        "business_status",  # f.eks. OPERATIONAL / CLOSED_PERMANENTLY
    ]
)


class GooglePlacesError(Exception):
    """Egendefinert unntak for feil som oppstår mot Google Places API."""


def _hent_api_nokkel() -> str:
    """
    Henter API-nøkkelen fra miljøvariabelen.
    Kaster tydelig feil med en gang hvis den mangler, i stedet for å
    feile kryptisk lenger nede i HTTP-kallet.
    """
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        raise GooglePlacesError(
            f"Miljøvariabelen '{API_KEY_ENV_VAR}' er ikke satt. "
            "Sett den med f.eks: export GOOGLE_PLACES_API_KEY='din-nøkkel'"
        )
    return api_key


def finn_place_id(sokestreng: str, api_key: str) -> str:
    """
    Steg 1: Slår opp fritekst (f.eks. "Hansen Rørleggerservice, Horten")
    og returnerer Google sin unike Place ID for treffet.

    Bruker "Find Place From Text"-endepunktet med input_type=textquery,
    som er laget nettopp for "jeg har et navn, gi meg ID-en".
    """
    params = {
        "input": sokestreng,
        "inputtype": "textquery",
        "fields": "place_id,name",
        "language": "no",
        "key": api_key,
    }

    try:
        respons = requests.get(FIND_PLACE_URL, params=params, timeout=HTTP_TIMEOUT_SEKUNDER)
        respons.raise_for_status()  # kaster feil ved HTTP-statuskoder som 4xx/5xx
    except requests.exceptions.Timeout as exc:
        raise GooglePlacesError("Tidsavbrudd (timeout) mot Google Places API.") from exc
    except requests.exceptions.RequestException as exc:
        raise GooglePlacesError(f"Nettverksfeil mot Google Places API: {exc}") from exc

    data = respons.json()
    status = data.get("status")

    if status == "ZERO_RESULTS":
        raise GooglePlacesError(f"Fant ingen bedrift som matcher søket: '{sokestreng}'.")
    if status == "REQUEST_DENIED":
        raise GooglePlacesError(
            "Google avviste forespørselen (REQUEST_DENIED). "
            "Sjekk at API-nøkkelen er gyldig og at 'Places API' er aktivert i Google Cloud Console."
        )
    if status == "OVER_QUERY_LIMIT":
        raise GooglePlacesError("Kvote/rate-limit overskredet hos Google (OVER_QUERY_LIMIT).")
    if status == "INVALID_REQUEST":
        raise GooglePlacesError(f"Ugyldig forespørsel (INVALID_REQUEST) for søket: '{sokestreng}'.")
    if status != "OK":
        raise GooglePlacesError(f"Uventet status fra Google Places API: {status}")

    kandidater = data.get("candidates") or []
    if not kandidater:
        # Skjer i praksis nesten aldri når status="OK", men vi sjekker likevel
        # defensivt siden det er en ekstern API vi ikke kontrollerer.
        raise GooglePlacesError(f"Google returnerte OK, men ingen kandidater for: '{sokestreng}'.")

    return kandidater[0]["place_id"]


def hent_place_details(place_id: str, api_key: str) -> dict[str, Any]:
    """
    Steg 2: Henter detaljene til bedriften basert på Place ID fra steg 1.
    """
    params = {
        "place_id": place_id,
        "fields": DETAILS_FELTER,
        "language": "no",
        "key": api_key,
    }

    try:
        respons = requests.get(PLACE_DETAILS_URL, params=params, timeout=HTTP_TIMEOUT_SEKUNDER)
        respons.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise GooglePlacesError("Tidsavbrudd (timeout) mot Google Places API (Details).") from exc
    except requests.exceptions.RequestException as exc:
        raise GooglePlacesError(f"Nettverksfeil mot Google Places API (Details): {exc}") from exc

    data = respons.json()
    status = data.get("status")

    if status != "OK":
        raise GooglePlacesError(f"Klarte ikke å hente detaljer (status={status}) for place_id={place_id}.")

    return data.get("result", {})


def _formater_apningstider(details: dict[str, Any]) -> Optional[list[str]]:
    """
    Google returnerer åpningstider som en liste med tekststrenger allerede
    oversatt til norsk (pga. language=no), f.eks:
    ["mandag: 08:00–16:00", "tirsdag: 08:00–16:00", ...]

    Returnerer None hvis bedriften ikke har registrert åpningstider hos
    Google (f.eks. rene nettbaserte tjenester, eller mangelfull GMB-profil).
    """
    opening_hours = details.get("opening_hours")
    if not opening_hours:
        return None
    return opening_hours.get("weekday_text")


def strukturer_bedriftsdata(details: dict[str, Any]) -> dict[str, Any]:
    """
    Plukker ut og strukturerer nøyaktig de 5 datapunktene vi trenger,
    med trygge fallback-verdier (None) hvis Google mangler data på et felt.
    Ufullstendige Google-profiler er vanlig for små, lokale bedrifter —
    derfor MÅ vi håndtere manglende felt uten at scriptet krasjer.
    """
    return {
        "firmanavn": details.get("name"),
        "adresse": details.get("formatted_address"),
        "telefon": details.get("formatted_phone_number") or details.get("international_phone_number"),
        "apningstider": _formater_apningstider(details),
        "rating": details.get("rating"),
        "antall_anmeldelser": details.get("user_ratings_total"),
        # Ekstra metadata som er nyttig å ha med for videre bruk i pipelinen:
        "place_id": details.get("place_id"),
        "google_maps_url": details.get("url"),
        "driftsstatus": details.get("business_status"),
    }


def hent_bedriftsdata(bedriftsnavn: str, by: str, api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Hovedfunksjon: kombinerer søk + detaljoppslag til ett rent resultat.

    Returnerer alltid et dict med samme "kontrakt" (success/error/data),
    slik at koden som kaller denne funksjonen (f.eks. et webhook-endepunkt
    eller en batch-jobb) alltid vet hva den skal forvente, uansett om
    oppslaget lykkes eller feiler.
    """
    if not bedriftsnavn or not bedriftsnavn.strip():
        return {"success": False, "error": "Bedriftsnavn kan ikke være tomt.", "data": None}
    if not by or not by.strip():
        return {"success": False, "error": "By kan ikke være tom.", "data": None}

    try:
        nokkel = api_key or _hent_api_nokkel()
        sokestreng = f"{bedriftsnavn.strip()}, {by.strip()}"

        place_id = finn_place_id(sokestreng, nokkel)
        details = hent_place_details(place_id, nokkel)
        strukturert_data = strukturer_bedriftsdata(details)

        return {"success": True, "error": None, "data": strukturert_data}

    except GooglePlacesError as exc:
        # Forventede, "kjente" feil (bedrift finnes ikke, feil API-nøkkel osv.)
        return {"success": False, "error": str(exc), "data": None}
    except Exception as exc:  # noqa: BLE001 - siste sikkerhetsnett mot ukjente feil
        return {"success": False, "error": f"Uventet feil: {exc}", "data": None}


def _kjor_som_cli() -> None:
    """
    Lar deg teste scriptet direkte fra terminalen:
        python place_lookup.py "Hansen Rørleggerservice" "Horten"
    """
    if len(sys.argv) != 3:
        print('Bruk: python place_lookup.py "<Bedriftsnavn>" "<By>"')
        print('Eksempel: python place_lookup.py "Hansen Rørleggerservice" "Horten"')
        sys.exit(1)

    bedriftsnavn, by = sys.argv[1], sys.argv[2]
    resultat = hent_bedriftsdata(bedriftsnavn, by)

    # ensure_ascii=False slik at æøå vises riktig i terminalen,
    # ikke som \uXXXX-escape-koder.
    print(json.dumps(resultat, indent=2, ensure_ascii=False))

    # Sett riktig exit-kode slik at scriptet kan brukes i automasjons-
    # pipelines (f.eks. shell-script eller CI) som sjekker suksess/feil.
    sys.exit(0 if resultat["success"] else 1)


if __name__ == "__main__":
    _kjor_som_cli()
