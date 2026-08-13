.PHONY: hjelp oppsett test lint kjor opp ned beredskapstest

KJERNE := services/aina-core
PY     := $(KJERNE)/.venv/bin/python

hjelp:
	@echo "make oppsett          installer utviklingsmiljø"
	@echo "make test             kjør testene"
	@echo "make lint             ruff"
	@echo "make kjor             start kjernen lokalt på :8080"
	@echo "make opp / ned        hele stacken via docker compose"
	@echo "make beredskapstest   simuler strømbrudd mot en kjørende kjerne"

oppsett:
	python3 -m venv $(KJERNE)/.venv
	$(KJERNE)/.venv/bin/pip install -e "$(KJERNE)[dev]"
	@test -f packs/husstand.yaml || cp packs/husstand.example.yaml packs/husstand.yaml
	@test -f .env || cp .env.example .env
	@echo "Klart. Fyll ut packs/husstand.yaml og .env."

test:
	cd $(KJERNE) && .venv/bin/python -m pytest -q

lint:
	cd $(KJERNE) && .venv/bin/python -m ruff check aina tests

kjor:
	cd $(KJERNE) && .venv/bin/python -m uvicorn aina.api.app:app --reload --port 8080

opp:
	docker compose -f deploy/docker-compose.yml --profile full up -d

ned:
	docker compose -f deploy/docker-compose.yml --profile full down

# Den viktigste testen i hele prosjektet: virker systemet når strømmen går?
# Kjør den på ordentlig med hovedbryteren minst én gang i kvartalet.
beredskapstest:
	@echo "→ Simulerer internettbortfall"
	@curl -s -X POST localhost:8080/api/system/tilstand \
		-H 'content-type: application/json' \
		-d '{"internett": false}' | python3 -m json.tool
	@echo "→ Simulerer strømbrudd, batteri 55 %"
	@curl -s -X POST localhost:8080/api/system/tilstand \
		-H 'content-type: application/json' \
		-d '{"internett": false, "nettstrom": false, "batteri_prosent": 55}' | python3 -m json.tool
	@echo "→ Simulerer kritisk batteri"
	@curl -s -X POST localhost:8080/api/system/tilstand \
		-H 'content-type: application/json' \
		-d '{"internett": false, "nettstrom": false, "batteri_prosent": 18}' | python3 -m json.tool
	@echo "→ Tilbake til normal"
	@curl -s -X POST localhost:8080/api/system/tilstand \
		-H 'content-type: application/json' -d '{}' | python3 -m json.tool
