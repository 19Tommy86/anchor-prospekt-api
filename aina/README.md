# Aina

**Offline-first hjem- og beredskapsassistent.**
Et system som gir familien en stemme og et ansikt i hverdagen — og som fortsatt
fungerer når internett, mobilnett eller strøm forsvinner.

> «Hei Aina — hva slags vær er det meldt i dag?»
> «Hei Aina — har jeg møter i dag?»
> «Hei Aina — nettet er nede. Hva gjør vi nå?»

---

## Kjerneidéen

De fleste smarthus- og assistent-produkter er skall rundt et skyende: tar du nettet,
har du en dyr høyttaler. Aina snur det. **Alt som betyr noe kjører lokalt på egen
maskinvare hjemme hos kunden.** Skyen er en bonus — for ferskere data, kraftigere
modeller og backup — aldri en forutsetning.

Tre ting definerer prosjektet:

1. **Beredskapsnivåer.** Systemet vet hvilken tilstand verden er i (nett, strøm,
   batteri) og degraderer kontrollert i fire nivåer i stedet for å bare feile.
   Se [docs/02-arkitektur.md](docs/02-arkitektur.md).
2. **Kunnskap om hvem den beskytter.** En lokal husstandsprofil: hvem bor her,
   hvor, hvilke behov (medisiner, allergier, barn, dyr), hvor er nærmeste
   tilfluktsrom, legevakt, vann, drivstoff, matlager.
   Se [packs/husstand.example.yaml](packs/husstand.example.yaml).
3. **Nyttig hver eneste dag.** Et beredskapssystem du bare bruker i krise blir
   ikke vedlikeholdt, og dermed virker det ikke i krise. Derfor er Aina først og
   fremst et smarthus: vær, kalender, strømpris, bil, lys, varme, meldinger.
   Beredskapen er en modus, ikke et separat produkt.

---

## Hva ligger her nå

Dette repoet er **fundamentet**, ikke et ferdig produkt: kjørbart skjelett +
komplette beslutningsunderlag.

```
aina/
├── docs/                  Arkitektur, API-nøkler, maskinvare, sikkerhet, veikart
│   └── adr/               Arkitekturbeslutninger med begrunnelse
├── services/aina-core/    Python/FastAPI-kjerne: beredskapsmotor, cache, konnektorer
├── packs/                 Husstandsprofil + katalog over offentlige norske datakilder
├── apps/panel/            Veggpanel (kiosk-PWA)
├── deploy/                docker-compose for hele stacken
└── scripts/               Bootstrap av eget GitHub-repo
```

### Start her

| Spørsmål | Dokument |
|---|---|
| Hva er dette, og hvor stopper omfanget? | [docs/01-visjon-og-omfang.md](docs/01-visjon-og-omfang.md) |
| Hvordan henger delene sammen? | [docs/02-arkitektur.md](docs/02-arkitektur.md) |
| **Hvilke API-nøkler trenger vi?** | [docs/03-api-nokler.md](docs/03-api-nokler.md) |
| **Hvilken maskinvare og strømløsning?** | [docs/04-maskinvare-og-strom.md](docs/04-maskinvare-og-strom.md) |
| Hvor henter vi offentlig beredskapsinfo? | [docs/05-beredskapsdata.md](docs/05-beredskapsdata.md) |
| Hvordan får den ansikt og stemme? | [docs/06-stemme-og-veggpanel.md](docs/06-stemme-og-veggpanel.md) |
| Er dette trygt? Personvern? | [docs/07-sikkerhet-og-personvern.md](docs/07-sikkerhet-og-personvern.md) |
| Hvordan blir det en SaaS? | [docs/08-saas-modell.md](docs/08-saas-modell.md) |
| Hva bygger vi først? | [docs/09-veikart.md](docs/09-veikart.md) |

---

## Kom i gang lokalt

```bash
cd services/aina-core
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../../.env.example ../../.env      # fyll inn det du har; alt er valgfritt
uvicorn aina.api.app:app --reload
```

Åpne http://localhost:8080/docs

Kjør testene:

```bash
pytest
```

Kjernen starter **uten en eneste API-nøkkel**. Uten nøkler får du færre
konnektorer, ikke en ødelagt applikasjon — det er hele poenget med designet.

---

## Løft ut i eget GitHub-repo

Mappen er skrevet for å være et selvstendig repo. Når du vil skille den ut:

```bash
./scripts/bootstrap-new-repo.sh aina
```

Se [scripts/bootstrap-new-repo.sh](scripts/bootstrap-new-repo.sh) for detaljer.

---

## Status

Tidlig fundament. Beredskapsmotoren, cachen og MET-værkonnektoren er implementert
og testet. Resten av konnektorene er definerte grensesnitt med stubber, slik at
rekkefølgen på arbeidet er fri.

Lisens: [MIT](LICENSE)
