# 05 — Beredskapspakken

Beredskapspakken er Ainas offline hukommelse: alt systemet må kunne svare på når
det ikke finnes nett. Den bygges i fredstid, oppdateres automatisk, og er
selvstendig lesbar — også hvis programvaren ikke starter.

**Alt innhold er offentlig og ugradert.** Systemet skal ikke inneholde, søke etter
eller utlede skjermet informasjon. Det er både et juridisk krav og en
designbeslutning: hele verdien ligger i å ha strukturert det åpne på forhånd.

## Struktur på disk

```
data/beredskapspakke/
├── manifest.yaml              versjon, byggetidspunkt, sjekksummer
├── husstand/                  familien, ressurser, planer (kryptert)
├── sted/
│   ├── tilfluktsrom.geojson   offentlige tilfluktsrom, DSB via Geonorge
│   ├── helse.geojson          legevakt, sykehus, apotek, AED
│   ├── vann.geojson           drikkevannsposter, bekker, kommunale punkter
│   ├── forsyning.geojson      matbutikk, bensin, jernvare
│   └── kommune.md             kommunens kriseplan, kontaktpunkter, møteplasser
├── kart/
│   └── norge.pmtiles          offline kartfliser
├── prosedyrer/                statiske sjekklister — brukes i nivå RØD
│   ├── stromutfall.md
│   ├── vannmangel.md
│   ├── evakuering.md
│   ├── forstehjelp.md
│   ├── brann.md
│   └── samband.md
├── varsler/                   siste hentede MET Alerts, NVE, kriseinfo
└── indeks/                    vektorindeks for fritekstsøk
```

`prosedyrer/` er ren markdown med vilje. Kan leses av et menneske på en telefon
med filutforsker, uten Aina i det hele tatt. Det er siste skanse.

## Hva pakken må kunne svare på uten nett

Dette er kravlisten. Klarer pakken disse, er den ferdig:

1. Hvor er nærmeste offentlige tilfluktsrom, og hvordan går jeg dit?
2. Hvor er nærmeste legevakt og apotek, og hva er åpningstidene?
3. Hvor får jeg drikkevann hvis kranen er tørr?
4. Hvor lenge holder maten, veden, medisinene og drivstoffet vårt?
5. Hva er kommunens plan, og hvor er møteplassen vår hvis vi blir adskilt?
6. Hva var siste værvarsel og siste farevarsel, og hvor gammelt er det?
7. Hva gjør vi ved strømbrudd, vannmangel, brann, evakuering?
8. Hvem ringer vi, i hvilken rekkefølge, og på hvilken frekvens/kanal?

Punkt 5 og 8 kan ikke automatiseres. De **må** fylles ut av familien. Aina bør
mase om det i fredstid — en tom møteplass-oppføring er systemets viktigste
manglende data.

## Innhentingsjobber

| Jobb | Kilde | Frekvens | Nivå |
|---|---|---|---|
| Værvarsel 9 døgn | MET Locationforecast | 1 t | GRØNN, GUL* |
| Farevarsel | MET Alerts | 10 min | GRØNN, GUL* |
| Flom/skred | NVE Varsom | 1 t | GRØNN |
| Kriseinfo | kriseinfo.no, NRK, politiet | 15 min | GRØNN |
| Vegmeldinger | Vegvesenet Datex II | 15 min | GRØNN |
| Strømpris | Tibber / hvakosterstrommen.no | Daglig 13:00 | GRØNN |
| Tilfluktsrom | Geonorge | Månedlig | GRØNN |
| POI (helse, vann, forsyning) | OSM Overpass, radius 25 km | Månedlig | GRØNN |
| Kartfliser | PMTiles-bygg | Kvartalsvis | Manuelt |
| Kommunal kriseplan | Kommunens nettsted | Kvartalsvis | Halvmanuelt |

\* I GUL prøver jobben fortsatt, i tilfelle bare deler av nettet er nede.

## Regelen om alder

Hvert datasett bærer `hentet_kl`. Aina skal alltid oppgi alder når data er eldre
enn TTL, og **nekte å svare** når data er eldre enn `max_useful`:

> «Siste værvarsel jeg fikk er fra i går kl. 18:40 — 14 timer gammelt. Det meldte
> kuling fra nordvest i kveld. Jeg har ikke fått oppdatering siden nettet gikk.»

Aldri: «Det blir kuling i kveld.» Forskjellen er hele tillitsforholdet.

## Personvern i pakken

`husstand/` inneholder de mest sensitive dataene i systemet — hvem som bor der,
når de er hjemme, helseopplysninger, hva som er lagret. Kravene:

- kryptert på disk (LUKS på volumet, i tillegg til filnivå for helsedata)
- aldri i git, aldri i sky-backup i klartekst
- aldri sendt til en sky-modell — sky-kall får kun det spørsmålet krever, aldri
  hele profilen
- eksporterbar og slettbar på ett minutt (GDPR, og fordi kunden eier dataene)
