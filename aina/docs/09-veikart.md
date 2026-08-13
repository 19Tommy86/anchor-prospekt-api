# 09 — Veikart

Rekkefølgen er valgt slik at systemet er **nyttig fra og med M1**, og at hver
milepæl kan stoppes uten at det som er bygget blir bortkastet.

---

### M0 — Fundament ✅ (dette repoet)

Beredskapsmotor, cache med stale-while-offline, konnektor-grensesnitt,
MET-værkonnektor, husstandsprofil, FastAPI-kjerne, tester, dokumentasjon.

**Ferdig når:** `pytest` er grønn og `/api/status` viser riktig beredskapsnivå.

---

### M1 — Panel og stemme (2–3 uker)

- Home Assistant satt opp, Aina Core snakker med det
- Wyoming: openWakeWord + faster-whisper + Piper, norsk
- Egen «Hei Aina»-vekkeordmodell trent
- Kiosk-PWA på veggpanel med normal- og beredskapsvisning
- Lokal CalDAV (Radicale), kalenderkonnektor

**Ferdig når:** «Hei Aina, hva slags vær er det meldt i dag?» og «har jeg møter i
dag?» besvares med stemme, med nettverkskabelen trukket ut.

Dette er den milepælen som gjør prosjektet ekte for familien. Prioriter den.

---

### M2 — Hverdagsagenten (3–4 uker)

- Verktøyregister med bekreftelseskrav
- Ollama + lokal modell, verktøykall
- Kalender: opprette og flytte møter
- Utgående e-post og SMS, med kø som overlever nettbortfall
- Tibber/HAN: pris, forbruk, billigste ladevindu
- Handleliste og lager

**Ferdig når:** Aina kan planlegge en dag, sende en melding og svare på strømpris.

---

### M3 — Beredskapspakken (3–4 uker)

- Innhentingsjobber: MET Alerts, NVE, kriseinfo, Vegvesenet
- Geodata: tilfluktsrom, helse, vann, forsyning
- PMTiles offline kart i panelet
- Statiske prosedyrer og sjekklister
- Vektorindeks for fritekstoppslag
- Husstandsprofil ferdig utfylt, med lager og møteplasser

**Ferdig når:** de åtte spørsmålene i docs/05 besvares uten nett.

---

### M4 — Strøm og overlevelse (2–3 uker)

- Batteribank, DC-UPS og batterimonitor montert
- NUT/MQTT inn i beredskapsmotoren
- Nivåbytte slår tjenester av og på i praksis
- Estimert gjenstående driftstid i panelet
- V2L-oppsett dokumentert i husstandsprofilen

**Ferdig når:** hovedbryteren slås av og systemet går til ORANSJE, dimmer panelet,
melder gjenstående tid og kjører videre i tre døgn. **Test dette på ordentlig.**

---

### M5 — Samband uten infrastruktur (2 uker)

- Meshtastic-noder, integrasjon mot MQTT
- Aina sender og mottar tekst over LoRa
- Familiestatus over mesh («hjemme / på vei / trygg»)
- DAB+/FM-mottak, opptak av nødmeldinger
- 4G-failover med to operatører

**Ferdig når:** to familiemedlemmer utveksler melding via Aina med mobilnettet
utilgjengelig.

---

### M6 — Produkt (6–8 uker)

- Installasjonsveiviser og oppsettsveiviser for husstandsprofilen
- Signert lisens, kanalbaserte oppdateringer
- Kryptert backup ut av huset
- Sky-modell med PII-filter og revisjonslogg
- Personvernerklæring, databehandleravtaler, ekstern sikkerhetstest
- Maskinvarepakke og monteringsinstruks

**Ferdig når:** en ikke-teknisk familie kan settes opp på en formiddag.

---

## Slik prioriterer vi når vi er i tvil

1. **Virker det uten nett?** Hvis ikke, er det ikke ferdig.
2. **Brukes det i fredstid?** Hvis ikke, blir det ikke vedlikeholdt, og da
   virker det ikke i krise heller.
3. **Kan det feile stille?** Hvis ja, fiks det før noe nytt bygges.
4. **Trenger det en nøkkel?** Finn den nøkkelfrie veien først.

## Åpne spørsmål som må avklares underveis

- Skal vekkeordet være «Aina» eller noe med færre falske treff i vanlig norsk tale?
- Skal barn ha egne profiler med begrenset tilgang, eller ett felles panel?
- Hvor mye av beredskapspakken kan lovlig deles mellom kunder som ferdigbygde
  regionale pakker, og hva må hentes per husstand?
- Skal maskinvaren selges ferdig montert, eller sertifiserer vi installatører?
