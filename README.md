# anchor-prospekt-api
FastAPI-motor for BRRRR-prospektanalyse
# Anchor Prospekt API 🏡

Dette er API-delen av verktøyet som analyserer eiendomsprospekter basert på **BRRRR-metoden**  
(Buy, Rehab, Rent, Refinance, Repeat).

### Funksjoner
- Tar imot opplastede **PDF-salgsoppgaver**
- Leser og ekstraherer nøkkeltall som BRA, pris og totalpris
- Kjører automatiske **avkastnings- og refinansieringsberegninger**
- Returnerer yield, kontantstrøm, og potensielt frigjort kapital etter refinansiering

---

### ⚙️ Teknisk oppsett

**Stack:**  
FastAPI + pdfplumber + Python 3.10+

**Kjør lokalt**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# åpne http://127.0.0.1:8000/docs
