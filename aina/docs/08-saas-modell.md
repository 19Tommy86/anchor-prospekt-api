# 08 — SaaS-modellen

Utfordringen: du vil selge dette som en tjeneste, men produktets hele verdi er at
det **ikke** avhenger av tjenesten din. En node som slutter å virke fordi
lisensserveren er nede, er et løftebrudd.

## Løsningen: skyen kan dø, noden lever

```
Kundens hjem                          Vår sky (valgfri)
┌─────────────────────┐              ┌──────────────────────┐
│  Aina Node          │              │  Lisens og fakturering│
│  ─────────────      │  ← signert   │  Oppdateringer        │
│  All logikk         │    lisensfil │  Kryptert backup      │
│  All data           │              │  Sky-modell (proxy)   │
│  Alle avgjørelser   │  → kun       │  Anonym telemetri     │
│                     │    valgfri   │                       │
│  Virker for alltid  │    telemetri │  Kan være nede i uker  │
│  uten skyen         │              │  uten at kunden merker │
└─────────────────────┘              └──────────────────────┘
```

**Lisensen er en signert fil, ikke et API-kall.** Noden får en Ed25519-signert
lisens med utløpsdato langt fram i tid og fornyer den når den har nett. Mister den
kontakt:

| Tid uten kontakt | Oppførsel |
|---|---|
| 0–90 dager | Ingen endring, ingen melding |
| 90–180 dager | Diskré påminnelse i panelet |
| Etter 180 dager | Sky-modell og oppdateringer stopper. **Alt lokalt fortsetter å virke, for alltid.** |

Beredskapsfunksjonene degraderes aldri av manglende betaling. Det er et løfte som
bør stå i vilkårene, ikke bare i koden — det er en betydelig del av tilliten
produktet selges på.

## Hva kunden faktisk betaler for

Ikke for at programvaren skal kjøre — den kjører uansett. For:

1. **Ferske data.** Beredskapspakken, kartene, POI-ene, kommunale planer, holdt
   oppdatert uten at kunden løfter en finger.
2. **Oppdateringer og sikkerhetsfikser**, signert og testet.
3. **Kryptert backup** utenfor huset — huset kan brenne.
4. **Sky-modellen** når den finnes og gir bedre svar.
5. **Support og oppsett.** For de fleste kunder er dette hovedverdien: noen
   installerte batteriet, satte opp panelet og fylte ut husstandsprofilen.

## Prisstruktur, skisse

| Nivå | Innhold | Indikativ pris |
|---|---|---|
| **Selvhosting** | Programvaren, åpen kildekode, egen maskinvare | 0 |
| **Hjem** | Datapakker, oppdateringer, backup | 99–149 kr/mnd |
| **Hjem+** | + sky-modell, prioritert support | 249–349 kr/mnd |
| **Maskinvare** | Ferdig node, batteri, panel, montert | 15 000–35 000 engangs |

Maskinvare og installasjon er trolig den største inntektsposten de første årene,
og også det som avgjør om systemet faktisk virker hos kunden. En feilmontert
batteribank er verre enn ingen.

## Flerkunde-drift uten å se kundens data

Vår sky skal **ikke kunne** lese hjemmedata eller kjøre kommandoer på noden. Det er
en arkitekturbeslutning, ikke en policy:

- Noden **henter**, skyen **dytter aldri**. Ingen innkommende kanal finnes.
- Backup er kryptert på noden med kundens nøkkel. Vi har ikke nøkkelen, og kan
  ikke gjenopprette for kunden — kunden må ta vare på gjenopprettingsnøkkelen.
  Det er en reell ulempe, og den er verdt prisen.
- Telemetri er opt-in, aggregert, uten identifikatorer.
- Sky-modellen mottar kun det filteret slipper gjennom (se docs/07).

Konsekvensen: et innbrudd hos oss gir angriperen en liste over kunder og
faktureringsdata — ikke deres hjem. Det er den forskjellen som gjør at produktet
kan selges til folk som bryr seg om nettopp dette.

## Flåtestyring

For 10 000 noder trengs likevel drift:

- **Kanalbasert utrulling:** `stable` / `beta` / `edge`. Kunden velger, og kan
  låse versjonen.
- **Helsesignal** (opt-in): «noden lever, versjon X, batteri OK» — uten innhold.
- **Kritiske sikkerhetsfikser** kan rulles ut raskere, men aldri stille: kunden
  varsles i panelet.
- **Ingen fjernpålogging** til kundenoder. Support skjer med kundens aktive
  medvirkning gjennom en tidsbegrenset kanal kunden selv åpner.

## Marked, kort

Sannsynlige første kunder i Norge: småbarnsfamilier i eneboliger, hytteeiere,
folk med hjemmekontor og eksisterende smarthus, gårdsbruk, og folk som allerede
har kjøpt aggregat eller solceller. Alle disse har allerede løst *deler* av
problemet med enkeltprodukter som ikke snakker sammen.

Konkurransen er ikke andre beredskapssystemer — den er «jeg har en powerbank og
DSBs brosjyre i skuffen». Produktets jobb er å være så nyttig til daglig at det
faktisk står ladet den dagen brosjyren skulle vært lest.
