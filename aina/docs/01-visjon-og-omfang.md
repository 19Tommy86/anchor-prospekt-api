# 01 — Visjon og omfang

## Problemet

Norske husstander er svært digitalt avhengige og samtidig svært eksponerte for
bortfall av strøm og ekom. DSBs egne anbefalinger sier at hver husstand bør klare
seg selv i minst tre døgn. Problemet er ikke at informasjonen mangler — den er
offentlig og god — men at den ligger på nettsider du ikke får åpnet i det øyeblikket
du trenger dem, og i en form ingen har lest på forhånd.

Samtidig sitter de fleste med et smarthus som **blir dummere enn en lysbryter**
når nettet forsvinner, fordi logikken bor i skyen.

## Visjonen

En boks hjemme hos kunden som:

- er nyttig hver dag (vær, kalender, strømpris, bil, lys, varme, påminnelser,
  meldinger), slik at den faktisk blir brukt og vedlikeholdt;
- kjenner husstanden — hvem, hvor, hvilke behov, hvilke ressurser;
- har lastet ned og strukturert offentlig beredskapsinformasjon **på forhånd**;
- overlever nettbortfall, mobilbortfall og strømbrudd i minst tre døgn;
- snakker norsk, lokalt, uten at et ord forlater huset.

## Hva Aina **er**

- Et lokalt system på egen maskinvare i kundens hjem.
- En agent med verktøy: kan lese kalender, sende e-post/SMS, styre hus,
  slå opp i lokal kunnskapsbase, gi kart og sjekklister.
- Et beredskapslager for **offentlig, ugradert** informasjon: tilfluktsrom,
  legevakt, vannposter, farevarsler, kommunale kriseplaner, DSB-anbefalinger.
- Et system med definert oppførsel når ting feiler — se beredskapsnivåene.

## Hva Aina **ikke** er (bevisste avgrensninger)

| Ikke | Hvorfor |
|---|---|
| En erstatning for Nødvarsel, 110/112/113 eller myndighetenes kanaler | Aina **peker på** offisielle kanaler, den erstatter dem aldri. Feil her koster liv. |
| En kilde til gradert eller ikke-offentlig informasjon | Utenfor omfang, ulovlig, og unødvendig. All verdi ligger i å strukturere det som allerede er åpent. |
| Medisinsk rådgiver | Den kan vise førstehjelpsprosedyrer fra offentlige kilder og kontaktinfo. Den diagnostiserer ikke. |
| Et selvforsvars- eller våpensystem | Utenfor omfang. |
| Skjult eller «hemmelig» programvare | Se merknaden om maskering under. |

## Om «å maskere det som et smarthus»

Du beskrev at systemet kanskje bør framstå som et smarthus. Den beste versjonen av
den tanken er ikke kamuflasje, men **produktstrategi** — og jeg vil være ærlig om
forskjellen, fordi den påvirker designet:

- **Som kamuflasje virker det dårlig.** Alle som kommer inn i huset ser et
  veggpanel. Alle som ser på nettverket ditt ser en server. Å «skjule» dette gir
  nesten null reell OPSEC-gevinst, men koster deg mye i brukervennlighet.
- **Som produkt virker det svært godt.** Et beredskapsprodukt selges én gang og
  glemmes. Et smarthus brukes daglig — og et system som brukes daglig er ladet,
  oppdatert, testet og kjent av familien den dagen det gjelder. **Det er den
  faktiske overlevelsesfordelen.**

Konklusjon som ligger til grunn for hele arkitekturen: Aina **er** et smarthus.
Beredskap er en driftsmodus i det samme systemet, ikke en skjult funksjon.

Det som derimot *skal* være diskret er dataene: hvor familien er, når de er hjemme,
hva de har på lager. Det håndteres med kryptering og lokal lagring, ikke med
kamuflasje. Se [07-sikkerhet-og-personvern.md](07-sikkerhet-og-personvern.md).

## Suksesskriterier

Fundamentet er ferdig når disse er sanne:

1. Trekk ut internettkabelen: Aina svarer fortsatt på vær (siste varsel),
   kalender, hus-styring og alle beredskapsspørsmål — og **sier eksplisitt** hvor
   gamle dataene er.
2. Trekk ut strømmen: systemet går over på batteri, dimmer panelet, kutter
   ikke-kritiske tjenester og melder anslått gjenstående driftstid.
3. En familie som ikke er teknisk kan spørre «hva gjør vi nå?» og få et konkret,
   stedbundet svar.
4. Ingen personopplysninger forlater huset uten at det er et eksplisitt valg.
