"""
Anchor Prospekt API
===================
Analyserer eiendomsprospekter etter BRRRR-metoden
(Buy, Rehab, Rent, Refinance, Repeat).

Endepunkter:
    POST /ingest/pdf   Last opp salgsoppgave, få ut nøkkeltall
    POST /analyze      Regn ut yield, kontantstrøm og refinansiering
    GET  /healthz      Sjekk at tjenesten lever

Selve regnestykkene ligger i beregning.py, PDF-uthentingen i prospekt.py.
Denne filen er kun web-laget.
"""

import io

import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from beregning import Assumptions, ManglerPris, compute_metrics
from prospekt import hent_nokkeltall

app = FastAPI(title="Anchor Prospekt API", version="0.2.0")

# allow_credentials=True sammen med allow_origins=["*"] er ugyldig etter
# CORS-standarden, og nettlesere avviser kombinasjonen. API-et bruker
# ikke cookies eller innlogging, så vi setter credentials til False.
# Før produksjon: bytt "*" med de faktiske domenene frontend-en kjører på.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Grense for opplastede filer. Uten en grense kan en stor fil spise opp
# minnet på serveren.
MAKS_PDF_BYTES = 25 * 1024 * 1024  # 25 MB


class AnalyzeRequest(BaseModel):
    extracted: dict
    assumptions: Assumptions


@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Leser en salgsoppgave (PDF) og henter ut nøkkeltall: totalpris,
    prisantydning, BRA, P-rom, felleskostnader og kommunale avgifter.

    Returnerer kun feltene som faktisk ble funnet. Mangler et felt, må
    du fylle det inn selv før du kjører /analyze.
    """
    innhold = await file.read()

    if not innhold:
        raise HTTPException(status_code=400, detail="Filen er tom.")
    if len(innhold) > MAKS_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Filen er større enn {MAKS_PDF_BYTES // 1024 // 1024} MB.",
        )

    # En ødelagt eller passordbeskyttet PDF skal gi en forståelig melding,
    # ikke en teknisk kræsj med statuskode 500.
    try:
        tekst = ""
        with pdfplumber.open(io.BytesIO(innhold)) as pdf:
            for side in pdf.pages:
                tekst += "\n" + (side.extract_text() or "")
    except Exception as exc:  # noqa: BLE001 - pdfplumber kaster mange ulike feil
        raise HTTPException(
            status_code=400,
            detail=f"Klarte ikke å lese PDF-en. Er filen gyldig? ({exc})",
        ) from exc

    if not tekst.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "Fant ingen tekst i PDF-en. Den er sannsynligvis en skannet "
                "bildefil. Da må nøkkeltallene fylles inn manuelt."
            ),
        )

    ekstrahert = hent_nokkeltall(tekst)

    return {
        "extracted": ekstrahert,
        "mangler": [f for f in ("totalpris", "BRA_m2") if f not in ekstrahert],
        "raw_preview": tekst[:1500],
    }


@app.post("/ingest/url")
async def ingest_url(payload: dict):
    """Ikke implementert ennå – last opp PDF i stedet."""
    return {"note": "URL-ingest kommer i v2. Last opp PDF nå.", "url": payload.get("url")}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Regner ut nøkkeltallene for eiendommen.

    Krever at 'extracted' inneholder en kjøpesum (totalpris eller
    prisantydning). Mangler den, får du en feilmelding i stedet for tall
    – tidligere gjettet koden på et beløp, noe som ga yield-tall som var
    flere ganger for høye.
    """
    try:
        return compute_metrics(req.extracted, req.assumptions)
    except ManglerPris as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/healthz")
def healthz():
    return {"ok": True}
