# ADR 0002 — Home Assistant som enhetslag

**Status:** Vedtatt
**Dato:** 2026-08-11

## Kontekst

Aina må styre lys, varme, låser, sensorer, ladeboks, varmepumpe og lese
strømmåler. Å bygge dette selv betyr Z-Wave, Zigbee, Matter, Modbus og hundrevis
av leverandørspesifikke protokoller — flere årsverk før første lyspære tennes.

Home Assistant løser allerede dette, kjører lokalt, er åpen kildekode og har et
stabilt lokalt API.

## Beslutning

Home Assistant er enhetslaget. Aina Core snakker med det over lokalt
REST/WebSocket-API.

Arbeidsdelingen er streng:

- **Home Assistant:** enheter, tilstand, historikk, enkle automasjoner. «Muskler.»
- **Aina Core:** intensjon, samtale, beredskapsnivå, kunnskap, beslutninger. «Hode.»

Aina skriver ikke automasjoner inn i HA for logikk som hører hjemme i kjernen, og
HA får ikke ansvar for beredskapsnivåene.

## Konsekvenser

**Positivt**
- Tusenvis av integrasjoner tilgjengelig fra dag én, alle lokale.
- **Faller Aina ut, fungerer huset fortsatt.** Lysbryterne virker, varmen står på.
  Dette er en bevisst feilsikring, ikke en bivirkning.
- Stemmelaget (Wyoming) kan deles mellom HA og Aina.
- Kjent for entusiaster — senker terskelen for tidlige kunder.

**Negativt**
- En stor avhengighet vi ikke styrer. Bruddendringer i HA kan koste oss tid.
- Ekstra ledd i responstiden for enhetsstyring (i praksis titalls millisekunder
  på LAN — akseptabelt).
- To systemer å oppdatere og sikre.

## Alternativer vurdert

- **Eget enhetslag.** Forkastet: uforsvarlig ressursbruk for et løst problem.
- **Kun MQTT + egne integrasjoner.** Forkastet: dekker for få enheter, og vi
  ville endt opp med å skrive Home Assistant på nytt, dårligere.
- **Aina som en HA-integrasjon (inni HA).** Forkastet: da arver vi HAs
  oppdateringssyklus og prosessmodell, og mister kontroll over beredskapsnivåene
  og strømstyringen — som er kjerneproduktet.
