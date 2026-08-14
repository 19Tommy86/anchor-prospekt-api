# 03 — API-nøkler og datakilder

Dette er svaret på «hvilke API-nøkler trenger vi?».

Kortversjonen: **overraskende få.** Det norske offentlige økosystemet er uvanlig
åpent, og hele stemme-/AI-laget kan kjøre lokalt uten noen nøkkel i det hele tatt.
Nøklene du faktisk må skaffe handler stort sett om *dine egne kontoer* — strøm,
bil, kalender, utgående meldinger.

> **Verifiser før produksjon.** Vilkår, priser og endepunkter endres. Tabellene
> under er utgangspunkt for innkjøp og arkitektur, ikke en kontrakt. Alle
> kommersielle tjenester bør bekreftes mot leverandørens egne sider før dere
> binder dere.

---

## A. Krever INGEN nøkkel

Disse dekker mesteparten av beredskapsverdien. At de er nøkkelfrie er også en
robusthetsfordel: ingenting utløper, ingenting kan sperres.

| Behov | Kilde | Merknad | Offline-strategi |
|---|---|---|---|
| Værvarsel | **MET Norway Locationforecast** (`api.met.no`) | Ingen nøkkel, men krever identifiserende `User-Agent` med kontaktinfo, og vilkårene krever at du cacher og bruker `If-Modified-Since`. Kall uten dette blir blokkert. | 9-døgnsvarsel lagres ved hver henting — gir dager med brukbar prognose offline |
| Farevarsel vær | **MET Alerts** (CAP-format) | Ingen nøkkel | Polles hvert 10. min, siste sett beholdes |
| Flom, jordskred, snøskred | **NVE / Varsom** (`api.nve.no`, `api01.nve.no/hydrology`, varsom-API) | Ingen nøkkel | Speiles |
| Kart, flyfoto, høydedata | **Kartverket / Geonorge** WMTS og nedlasting | Ingen nøkkel for åpne data | Se PMTiles under |
| Adresser, matrikkel, stedsnavn | **Kartverket Adresse-API** (`ws.geonorge.no`) | Ingen nøkkel | Kommunen din lastes ned i sin helhet |
| Offentlige tilfluktsrom | **DSB-datasett via Geonorge** | Åpne data | Lastes ned én gang, ligger lokalt for alltid |
| Punkter av interesse: apotek, sykehus, legevakt, bensin, drikkevann, matbutikk | **OpenStreetMap / Overpass** | Ingen nøkkel. Bruk et rimelig uttrekk, ikke sanntidskall | Uttrekk lagres i lokal database |
| Offline kartfliser | **Protomaps PMTiles** generert fra OSM | Ingen nøkkel, én fil | Hele Norge i én fil på disk — fungerer uten nett |
| Kriseinformasjon fra myndighetene | **kriseinfo.no** (DSB), **NRK RSS**, **politiet.no** | RSS/JSON, ingen nøkkel | Siste N artikler beholdes |
| Vegmeldinger, stengte veier, ferje | **Statens vegvesen Datex II / NVDB** | Ingen nøkkel | Speiles, kritisk for evakueringsrute |
| Kollektivtrafikk hele Norge | **Entur JourneyPlanner** (GraphQL) | Ingen nøkkel, men krever `ET-Client-Name`-header | Rutetabeller kan lastes ned som GTFS og brukes offline |
| Strømpris per time | **hvakosterstrommen.no** | Ingen nøkkel, døgnpriser per prisområde NO1–NO5 | Morgendagens priser hentes kl. 13, ligger lokalt |
| Nødnummer, førstehjelp, DSB-egenberedskap | Offentlig tekst | — | Skrives inn i beredskapspakken som statisk innhold |
| Kringkasting | **DAB+/FM via RTL-SDR** | Maskinvare, ikke API | Fungerer når alt annet er nede — se docs/04 |
| Tekstsamband uten mobilnett | **Meshtastic** (LoRa) | Maskinvare, ingen nøkkel | Fungerer uten all infrastruktur |

---

## B. Gratis nøkkel / registrering

| Behov | Tjeneste | Hvordan | Kostnad |
|---|---|---|---|
| Historiske værdata | **MET Frost API** | Registrer og få client ID på frost.met.no | Gratis |
| Strømforbruk og pris i sanntid | **Tibber** | Personlig token på developer.tibber.com/settings/access-token | Gratis for kunder |
| Kalender i skyen | **Google Calendar API** | OAuth 2.0-klient i Google Cloud Console | Gratis innenfor kvote |
| Din egen e-post | **SMTP hos egen leverandør** | Brukernavn/passord eller app-passord | Inkludert |

**Tibber fortjener en merknad.** Sky-API-et gir pris og historikk. Men har du en
**Tibber Pulse**, leverer den sanntids forbruk over ditt eget nettverk — den
datastrømmen fortsetter når internett ligger nede. Aina bør lese Pulse lokalt og
bruke sky-API-et kun til priser. Det er et konkret eksempel på designregelen:
*finn den lokale veien til dataene.*

Har du ikke Tibber: `hvakosterstrommen.no` gir deg prisen uten noen nøkkel, og
en HAN-port-leser (P1/MBUS) gir deg forbruket lokalt fra din egen måler. Da er du
helt uavhengig av strømleverandøren din.

---

## C. Betalte nøkler

| Behov | Alternativer | Prisbilde | Anbefaling |
|---|---|---|---|
| **Bil** (ladenivå, rekkevidde, forvarming, lading) | **Enode** (norsk, dekker de fleste merker) · **Smartcar** · **Tesla Fleet API** direkte | Aggregatorene har utviklingsnivå og deretter pris per kjøretøy/mnd. Tesla Fleet krever registrert app med public key på eget domene, og har egen prising. | Start med **Enode** hvis flere bilmerker skal støttes; direkte merke-API kun hvis dere er låst til ett merke |
| **SMS** | **Sveve.no**, **LINK Mobility** (norske) · **Twilio**, **Vonage** (internasjonale) | Størrelsesorden noen tiøre per SMS | Norsk leverandør gir norsk avsender-ID og enklere databehandleravtale |
| **Transaksjonell e-post** | Resend, Postmark, Mailgun | Gratis nivå finnes hos flere | Bruk **egen SMTP** hvis mulig — familiens e-post bør ikke gå via en tredjepart |
| **Sky-språkmodell** | **Anthropic API** (`claude-sonnet-5` / `claude-opus-5`) | Per token | Kun i nivå GRØNN, og kun for oppgaver den lokale modellen ikke klarer |
| **Satellitt-samband** | Starlink · Iridium GO! · Garmin inReach | Abonnement | inReach har API, men krever egen avtale. Se docs/04 |
| **Telefonoppringing** (Aina ringer på dine vegne) | Twilio Voice | Per minutt | Vurder nøye — se § Restaurantbordet |

---

## D. Ting det **ikke** finnes gode API-er for

Her er det viktig å ikke love noe systemet ikke kan holde.

**Bordbestilling på restaurant.** Det finnes ingen åpen norsk API for dette.
OpenTable og TheFork har partner-API-er som krever forretningsavtale, og de dekker
uansett bare kjedede restauranter. Realistiske veier, i prioritert rekkefølge:

1. **Aina skriver e-posten eller SMS-en og lar deg trykke send.** Enkelt, ærlig,
   virker mot alle restauranter, ingen ny nøkkel. Dette er den anbefalte v1.
2. Utfylling av restaurantens eget nettskjema via headless nettleser. Skjørt,
   krever vedlikehold per nettsted, og bryter ofte vilkårene deres.
3. Automatisk oppringing via Twilio Voice + talesyntese. Teknisk mulig. Men
   å la et system ringe folk uten at de vet det er en AI er et reelt etisk og
   juridisk problem — ikke bygg dette uten at Aina identifiserer seg som system.

**Nødvarsel.** Myndighetenes varsel til mobil er *cell broadcast* — det finnes
ingen API å abonnere på. Aina kan ikke motta det. Den kan derimot speile
kriseinfo.no og MET Alerts, og den skal alltid vise til de offisielle kanalene.

**Elhub / måleverdier direkte.** Krever tilgang som markedsaktør. For en husstand
er HAN-porten på måleren den riktige veien.

**Kommunale kriseplaner.** Publiseres som PDF på hver kommunes nettside, uten
standardisert format. Løsningen er en nedlastingsjobb per kommune som legger PDF-en
i beredskapspakken og indekserer teksten. Manuelt arbeid, men engangsarbeid.

---

## E. Minste fornuftige oppsett

Skal du komme i gang, er dette settet:

```
Ingen nøkkel:   MET vær + MET Alerts + NVE + Kartverket + OSM/PMTiles
                + hvakosterstrommen.no + Entur + Vegvesenet + kriseinfo.no
Gratis nøkkel:  Tibber-token (hvis kunde)
Egen konto:     SMTP for e-post
Lokalt, gratis: Whisper (tale) + Piper (stemme) + openWakeWord + Ollama (modell)
```

Det gir vær, farevarsler, kart, strømpris, kollektiv, veg, kriseinfo, full
stemmestyring på norsk og en lokal språkmodell — **uten en eneste betalt nøkkel.**

Legg deretter til, i denne rekkefølgen, etter faktisk behov:
SMS → bil → sky-modell → satellitt.

---

## F. Hvordan nøkler håndteres

- Aldri i git. `.gitignore` blokkerer `.env` og `packs/husstand.yaml`.
- I produksjon: **SOPS + age** eller Docker secrets. Kryptert i repo, dekryptert
  kun på noden.
- Hver nøkkel registreres i `docs/03`-tabellen med eier, fornyelsesdato og
  hva som slutter å virke uten den.
- **Ingen nøkkel skal være kritisk.** Utløper Tibber-tokenet, skal Aina falle
  tilbake til `hvakosterstrommen.no` og si fra i loggen — ikke stoppe.
- Konnektorer får kun de nøklene de trenger, injisert ved oppstart.
