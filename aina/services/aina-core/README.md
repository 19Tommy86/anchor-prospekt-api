# aina-core

Kjernen i Aina. Se [hoved-README](../../README.md) for hele prosjektet og
[docs/02-arkitektur.md](../../docs/02-arkitektur.md) for hvordan delene henger
sammen.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn aina.api.app:app --reload --port 8080
```

## Moduler

| Fil | Ansvar |
|---|---|
| `aina/readiness.py` | Beredskapsmotoren — de fire nivåene, hysterese, effektbudsjett |
| `aina/cache.py` | Lokal cache med «stale-while-offline» og ærlig aldersmerking |
| `aina/connectors/base.py` | Grensesnittet alle datakilder må oppfylle, inkl. fallback |
| `aina/connectors/met.py` | Værvarsel fra api.met.no (ingen nøkkel) |
| `aina/connectors/strompris.py` | Timepriser NO1–NO5 (ingen nøkkel) |
| `aina/knowledge/household.py` | Husstandsprofilen — «hvem beskytter jeg» |
| `aina/api/app.py` | HTTP mot panel, stemmelag og mobil |

## Regelen for nye konnektorer

Arv fra `Konnektor` og implementer `hent_ferskt()` og `friskhet`. `hent()` er
allerede skrevet og håndterer cache, fallback og aldersmerking — ikke skriv den
på nytt, og ikke gå utenom den.

En konnektor uten offline-vei godkjennes ikke. Se ADR 0001.
