from typing import Optional
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pdfplumber, io, re

from google_places_smb.place_lookup import hent_bedriftsdata
from google_places_smb.nettside import render_bedriftsside, render_feilside

app = FastAPI(title="Anchor Prospekt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class Assumptions(BaseModel):
    interest_rate: float = 0.049
    term_years: int = 30
    renovation_budget: float = 300000.0
    ltv_post_refi: float = 0.75
    rent_est_mid: float = 13500.0
    operating_cost_year: float = 45000.0

class AnalyzeRequest(BaseModel):
    extracted: dict
    assumptions: Assumptions

class BedriftLookupResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Optional[dict] = None

def annuity_payment(principal: float, rate_year: float, years: int) -> float:
    r = rate_year/12
    n = years*12
    return principal * (r*(1+r)**n) / ((1+r)**n - 1)

def compute_metrics(ex, a: Assumptions):
    total_cost = float(ex.get("totalpris") or ex.get("total_price") or 0) + a.renovation_budget
    if not total_cost:
        total_cost = 1733600 + a.renovation_budget
    ek = 0.20 * total_cost
    loan = total_cost - ek
    pay_m = annuity_payment(loan, a.interest_rate, a.term_years)
    income_year = a.rent_est_mid * 12
    opex_year = a.operating_cost_year
    gross_yield = (income_year) / total_cost if total_cost else 0
    net_yield = (income_year - opex_year) / total_cost if total_cost else 0
    cashflow_month = (income_year - opex_year - pay_m*12)/12

    bra = float(ex.get("bra") or ex.get("BRA_m2") or ex.get("BRA") or 131)
    psqm = float(ex.get("price_per_sqm_after") or ex.get("psqm_hint") or 30000)
    arv_mid = bra * psqm
    loan_balance = loan
    refi_cashout_mid = max(0.0, a.ltv_post_refi*arv_mid - loan_balance)

    return {
        "total_cost": round(total_cost,2), "loan": round(loan,2), "equity": round(ek,2),
        "gross_yield": gross_yield, "net_yield": net_yield,
        "cashflow_month": cashflow_month,
        "arv_mid": arv_mid, "refi_cashout_mid": refi_cashout_mid
    }

@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    content = await file.read()
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    ex = {}
    m = re.search(r"\bBRA\s*[:=]?\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        ex["BRA_m2"] = float(m.group(1))
    return {"extracted": ex, "raw_preview": text[:1500]}

@app.post("/ingest/url")
async def ingest_url(payload: dict):
    return {"note": "URL-ingest kommer i v2. Last opp PDF nå.", "url": payload.get("url")}

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    return compute_metrics(req.extracted, req.assumptions)

@app.get("/bedrift/lookup", response_model=BedriftLookupResponse)
def bedrift_lookup(navn: str, by: str):
    """
    Slår opp en lokal bedrift i Google Places (navn + by) og returnerer
    firmanavn, adresse, telefon, åpningstider og rating/antall anmeldelser.

    Eksempel: /bedrift/lookup?navn=Hansen%20R%C3%B8rleggerservice&by=Horten

    Returnerer alltid HTTP 200 med {success, error, data}. "success"-feltet
    forteller om oppslaget lyktes, "error" inneholder norsk feiltekst hvis
    ikke (f.eks. bedriften finnes ikke, eller feil API-nøkkel på serveren).
    """
    return hent_bedriftsdata(navn, by)

@app.get("/bedrift/nettside", response_class=HTMLResponse)
def bedrift_nettside(navn: str, by: str):
    """
    Fase 2: Genererer en komplett, ferdig HTML-nettside for bedriften.

    Samme input som /bedrift/lookup, men returnerer en visuell side i
    stedet for JSON. Åpne denne URL-en rett i nettleseren:

      /bedrift/nettside?navn=Hansen%20R%C3%B8rleggerservice&by=Horten

    Ved treff: HTTP 200 med den genererte siden.
    Ved bom (bedriften finnes ikke, feil API-nøkkel osv.): HTTP 404 med
    en feilside som viser hva som ble søkt etter og hvorfor det feilet.
    """
    resultat = hent_bedriftsdata(navn, by)

    if not resultat["success"]:
        # 404 er riktig semantikk her: den forespurte ressursen (bedriften)
        # kunne ikke fremskaffes. Vi returnerer likevel en lesbar HTML-side,
        # ikke en rå feilmelding.
        return HTMLResponse(
            content=render_feilside(resultat["error"], navn, by),
            status_code=404,
        )

    return HTMLResponse(content=render_bedriftsside(resultat["data"]))

@app.get("/healthz")
def healthz():
    return {"ok": True}
