# ADR 0003 — Lokal språkmodell, med sky-eskalering kun i nivå GRØNN

**Status:** Vedtatt
**Dato:** 2026-08-11

## Kontekst

Aina må forstå fri norsk tale og velge riktig verktøy. En stor sky-modell gjør
dette klart best. Men produktløftet er at systemet virker uten nett, og de mest
sensitive dataene i systemet er nettopp de en modell trenger kontekst fra.

Samtidig er en 7B-modell på en N100 vesentlig svakere enn en sky-modell, særlig
på norsk og på flertrinns verktøybruk.

## Beslutning

**Lokal modell er standarden, ikke reserveløsningen.**

| Nivå | Modell |
|---|---|
| GRØNN | Lokal først. Eskalerer til sky **kun** hvis lokal modell er usikker, oppgaven er kompleks, `AINA_CLOUD_ALLOWED=true` og PII-filteret slipper forespørselen gjennom |
| GUL | Kun lokal |
| ORANSJE | Lokal, liten modell (3B) |
| RØD | **Ingen modell.** Forhåndsskrevne prosedyrer og direkte oppslag |

I tillegg: alle beredskapskritiske spørsmål besvares fra beredskapspakken via
direkte oppslag — også i GRØNN. En språkmodell skal ikke stå mellom familien og
adressen til nærmeste tilfluktsrom. Modellen formulerer svaret; den finner det ikke.

## Konsekvenser

**Positivt**
- Ingen driftsavbrudd når nettet går — bare et mindre veltalende system.
- Personvernet holder som utgangspunkt, ikke som unntak.
- Ingen løpende token-kostnad for vanlig bruk, som gjør prisstrukturen i docs/08
  mulig.
- Kunden kan slå av sky-modellen helt og fortsatt ha et fullverdig produkt.

**Negativt**
- To modellveier å teste, med ulik kvalitet. Krever et felles evalueringssett
  som kjøres mot begge.
- Lokal modell krever 16–32 GB RAM. Drar maskinvarekostnaden opp.
- Svarkvaliteten varierer med beredskapsnivå. Må kommuniseres, ikke skjules.

## Alternativer vurdert

- **Kun sky.** Forkastet: bryter produktløftet fullstendig.
- **Kun lokal, aldri sky.** Vurdert seriøst. Forkastet fordi enkelte oppgaver
  (lange planer, sammenstilling av dokumenter) blir merkbart bedre, og fordi
  kunden kan velge dette selv med ett flagg.
- **Finjustert liten modell på norsk.** Interessant senere. For tidlig nå —
  vedlikeholdskostnaden ved egne modellvekter er høy før produktet har form.
