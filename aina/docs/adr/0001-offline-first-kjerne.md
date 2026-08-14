# ADR 0001 — Offline-first kjerne med beredskapsnivåer

**Status:** Vedtatt
**Dato:** 2026-08-11

## Kontekst

Produktet selges på løftet om å virke når nettet, mobilnettet eller strømmen er
borte. Den vanlige arkitekturen for stemmeassistenter — tynn klient mot sky —
gjør nøyaktig det motsatte.

Samtidig er det fristende å bygge sky-først fordi det er raskere, og «legge til
offline senere». Det virker aldri: offline-oppførsel er ikke en funksjon man
skrur på, det er en egenskap ved hvordan data flyter.

## Beslutning

1. All logikk og alle data ligger på noden hjemme hos kunden. Skyen er en
   valgfri kilde til friskere data og en større modell.
2. Hver konnektor **må** implementere både `hent_ferskt()` og `hent_lagret()`.
   En konnektor uten offline-vei godkjennes ikke.
3. Systemet har fire eksplisitte beredskapsnivåer — GRØNN, GUL, ORANSJE, RØD —
   med definert effektbudsjett, tillatte tjenester og svarpolicy per nivå.
4. Nivået går umiddelbart opp ved forverring, men med forsinkelse ned igjen, slik
   at flakkende nett ikke gir hopping.
5. I nivå RØD kjøres **ingen språkmodell**. Kun forhåndsskrevne, verifiserte
   prosedyrer og kartdata.
6. Alle data bærer `hentet_kl`. Gamle data skal merkes som gamle. Data eldre enn
   `max_useful` skal ikke brukes til å svare.

## Konsekvenser

**Positivt**
- Løftet i markedsføringen er strukturelt sant, ikke et påheng.
- Nedetid hos oss eller hos en API-leverandør merkes knapt.
- Punkt 6 gir en tillitsegenskap konkurrentene ikke har: systemet lyver ikke om
  hvor ferskt noe er.
- Punkt 5 er både strømsparing og sikkerhet — når det står på spill får familien
  tekst et menneske har skrevet og kontrollert.

**Negativt**
- Hver konnektor koster mer å skrive. Akseptert.
- Krever betydelig lokal maskinvare — se docs/04. Akseptert; det er også en
  inntektskilde.
- Cachet data kan bli gammelt på måter som overrasker. Motvirket av punkt 6 og
  av at alder alltid vises i grensesnittet.

## Alternativer vurdert

- **Sky-først med offline-cache.** Forkastet: gir «degradert produkt» i stedet
  for «annet driftsnivå», og offline-veien blir aldri ordentlig testet.
- **Rent lokalt uten sky i det hele tatt.** Forkastet: da mister vi ferske
  farevarsler og oppdaterte kart, som er den viktigste bruksverdien i fredstid.
