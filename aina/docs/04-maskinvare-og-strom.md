# 04 — Maskinvare og strømforsyning

Målet: **72 timer uten nettstrøm og uten internett**, med stemmestyring i de
første timene og oppslag/kart hele veien.

Alle priser er størrelsesorden i NOK, ment for budsjettering — ikke tilbud.

---

## Effektbudsjettet er designdokumentet

Alt annet følger av dette regnestykket. Vi dimensjonerer for tre døgn.

| Komponent | GRØNN | ORANSJE | RØD |
|---|---|---|---|
| Mini-PC (Intel N100 / N305) | 10–25 W | 9 W | 7 W |
| Ruter + switch | 12 W | 8 W | 6 W (kun switch + AP) |
| Veggpanel | 8 W | 3 W (dimmet) | 0 W (av, vekkes ved berøring) |
| MQTT/sensorer/Meshtastic | 2 W | 2 W | 2 W |
| GPU (valgfri) | 30–120 W | 0 W | 0 W |
| **Sum uten GPU** | **~32 W** | **~22 W** | **~15 W** |

Med et batteribank på **1,28 kWh** (12 V, 100 Ah LiFePO4), ved 90 % brukbar
kapasitet ≈ 1,15 kWh:

- ORANSJE ved 22 W → **~52 timer**
- RØD ved 15 W → **~77 timer**
- Blandet, realistisk profil → **3 døgn med margin**

Vil du ha 5–7 døgn: to banker (2,56 kWh) → ~100 t i ORANSJE. Det er fortsatt en
liten, billig og brannsikker installasjon.

**Den viktigste enkeltbeslutningen: kjør på 12 V likestrøm, ikke via inverter.**
En vanlig 230 V UPS taper 10–20 % på å lage vekselstrøm som PC-en umiddelbart
gjør om til likestrøm igjen. Kjør mini-PC og ruter direkte fra batteriet med
DC-DC-omformere. Det er dagevis ekstra driftstid gratis.

---

## Materialliste

### Kjerne

| Del | Anbefaling | Hvorfor | Ca. |
|---|---|---|---|
| Datamaskin | Mini-PC, Intel N100/N305, **32 GB RAM**, 1 TB NVMe | 32 GB fordi en 7B-modell + database + HA + kart skal ligge samtidig. RAM er billigere enn kompromisser. | 4 000–7 000 |
| Lagring | Ekstra 1 TB NVMe eller SSD, speilet | Kartdata og beredskapspakke må overleve diskfeil | 1 000 |
| Valgfri GPU | Brukt RTX 3060 12 GB, eller Mac mini M-serie som modellnode | Kun for større modeller i GRØNN. Slås av på batteri. | 2 500–8 000 |

En Raspberry Pi 5 kan kjøre alt **unntatt** språkmodellen. Skal Aina snakke
fritt, trenger du x86 med nok RAM.

### Strøm

| Del | Anbefaling | Ca. |
|---|---|---|
| Batteri | LiFePO4 12 V 100 Ah med innebygd BMS | 4 000–7 000 |
| Lader/UPS | DC-UPS eller 12 V lader med automatisk omkobling (< 10 ms) | 1 500–3 000 |
| DC-DC | 12 V → 19 V for PC, 12 V → 12 V regulert for ruter | 600 |
| Overvåking | Shunt/batterimonitor med Modbus eller MQTT, **eller** NUT-kompatibel UPS | 900 |
| 230 V nød-uttak | Liten ren-sinus inverter 300–600 W | 1 500 |

**LiFePO4, ikke blysyre eller vanlig litium.** Tåler flere tusen sykluser,
avgir ikke gass, og har vesentlig bedre termisk sikkerhet — dette står i et
bolighus med barn.

Batterimonitoren er ikke valgfri: **beredskapsmotoren styres av den.** Uten
måling av ladenivå kan ikke Aina vite når den skal gå til RØD.

### Nettverk og samband — i rekkefølge etter når de faller

| Lag | Løsning | Faller når |
|---|---|---|
| 1. Fiber/kabel | Vanlig bredbånd | Linje eller ISP nede |
| 2. Mobilt | 4G/5G-ruter med **to SIM fra ulike operatører** — Telenor og Telia er fysisk adskilte nett i Norge | Basestasjon uten strøm (typisk 2–4 t reserve) |
| 3. Satellitt | Starlink (~50 W — dyrt i strømbudsjettet, kjør det manuelt) | Sjelden |
| 4. Radio, toveis | **Meshtastic** LoRa 868 MHz, 2–4 noder | Nesten aldri. Rekkevidde km, forbruk milliwatt |
| 5. Radio, enveis | DAB+/FM-mottaker, gjerne RTL-SDR + sveiv/batteriradio som reserve | NRK har egen nødstrøm på senderne |

Meshtastic er den mest undervurderte delen av oppsettet. To noder til under
1 500 kr gir familien tekstmeldinger seg imellom **helt uavhengig av all
infrastruktur** — og Aina kan sende varsler ut på det nettet.

### Veggpanelet — ansiktet

| Del | Anbefaling | Ca. |
|---|---|---|
| Skjerm | 10–13" nettbrett i veggbrakett, eller berøringsskjerm + Pi | 2 500–6 000 |
| Strøm/data | **PoE** + PoE-splitter → én kabel i veggen, og panelet henger på UPS-en | 700 |
| Mikrofon | **Home Assistant Voice PE** eller ReSpeaker-array | 800–1 600 |
| Lyd | Aktiv høyttaler eller innebygd | 500 |

PoE er verdt det: strøm og data i én kabel, ingen synlig lader, og panelet får
nødstrøm fra samme batteri som kjernen.

**Plassering:** gang eller kjøkken, i øyehøyde, der familien passerer daglig.
Et panel i kjelleren blir ikke brukt, og da blir systemet ikke vedlikeholdt.

---

## Om solceller — ærlig regnestykke

Solceller er den vanligste anbefalingen og i norsk vinter den svakeste.

Et 400 W-panel i Sør-Norge gir grovt regnet 1,5–2 kWh per dag i juni og
**0,1–0,3 kWh per dag i desember** — og desember er når strømbruddet kommer. Aina
trenger rundt 0,5 kWh/døgn i ORANSJE. Solcellene dekker altså ikke behovet i den
årstiden systemet er til for.

Prioriteringen bør derfor være:

1. **Batteribank** — dekker 3–5 døgn. Dette er hovedløsningen.
2. **Elbil med V2L** — Ioniq 5, EV6, EV9 og flere gir 3,6 kW fra 230 V-uttak.
   Ett kjøretøy med 60 kWh er i praksis et kraftverk for en 30 W-last. Bruk den
   til å **lade opp banken i én time annenhver dag**, ikke til å drive systemet
   kontinuerlig — bilen bruker mye på bare å holde seg våken.
3. **Liten invertergenerator** (1–2 kW, ~2 000–5 000 kr) hvis det skal vare over
   en uke. Bensin lagres trygt, ute, i begrenset mengde.
4. **Solceller** som supplement mars–oktober, ikke som beredskapsgrunnlag.

Aina bør kjenne V2L-oppsettet i husstandsprofilen og kunne si: «Bilen står på
64 %. Det er nok til å lade banken tolv ganger. Neste lading anbefales i morgen
tidlig.»

---

## Det viktigste maskinvarepoenget

I en norsk vinterkrise er **varme og vann viktigere enn serveren.** En vedovn,
20 liter vann per person og et tørt sted å sove betyr mer enn all programvaren i
dette repoet.

Aina skal vite dette og oppføre seg deretter: den fører oversikt over ved, vann,
mat, medisiner og drivstoff i husstandsprofilen, minner om etterfylling i fredstid,
og i krise sier den *hva du skal gjøre fysisk* før den forteller noe om seg selv.

Systemets rolle er å være den som husker alt du planla den dagen du hadde
overskudd til å planlegge — ikke å være løsningen i seg selv.
