# 07 — Sikkerhet og personvern

Aina samler det mest sensitive et hjem har: hvem som bor der, når de er hjemme,
helseopplysninger, posisjon, vaner og forsyningslager. Blir dette systemet
kompromittert, er skaden større enn hos et vanlig smarthus. Sikkerhet er derfor
ikke en modul — det er en forutsetning for at produktet kan selges i det hele tatt.

## Trusselmodell

| # | Trussel | Hvor sannsynlig | Konsekvens | Tiltak |
|---|---|---|---|---|
| T1 | Panelet stjeles eller lånes av gjest | Høy | Full lesetilgang til familiens liv | PIN på beredskaps- og profilvisning, ingen hemmeligheter lagret på panelet, panelet er en tynn klient |
| T2 | Kompromittert IoT-enhet på hjemmenettet | Høy | Sidelengs bevegelse mot kjernen | VLAN for IoT, mTLS mellom panel og kjerne, ingen tillit basert på nettverksplassering |
| T3 | Lekkasje via sky-modell | Middels | Personopplysninger til tredjepart | Sky kun i GRØNN, feltnivå-filter før utsending, revisjonslogg over hva som ble sendt |
| T4 | Tyveri av server | Lav | Alt | LUKS full diskkryptering, nøkkel via TPM + oppstarts-PIN |
| T5 | Kompromittert leverandørkjede (oppdatering) | Lav | Full kontroll | Signerte oppdateringer, reproduserbare bygg, kunden kan låse versjon |
| T6 | Angriper med tilgang til SaaS-siden vår | Lav | Mange kunder | Sky-siden skal **ikke kunne** lese kundedata eller kjøre kommandoer på noden. Se docs/08 |
| T7 | Innsidebruk: én i husstanden overvåker en annen | Reell | Alvorlig personskade | Per-person-samtykke, synlig sporingsindikator, ingen skjult posisjonshistorikk |

T7 er lett å overse og hører hjemme her. Et system som vet hvor familien er til
enhver tid er også et perfekt kontrollverktøy. Designsvaret: posisjonsdeling er
opt-in per person, alltid synlig for den det gjelder, og historikk lagres kort.
Ingen «skjult modus». Noensinne.

## Grunnregler

1. **Ingen inngående porter mot internett.** Fjerntilgang skjer over WireGuard.
   Ingen portåpning, ingen UPnP, ingen sky-relé med tilgang til noden.
2. **mTLS internt.** Panel og kjerne autentiserer hverandre med sertifikater fra
   en lokal CA. Nettverksplassering gir ingen tillit.
3. **Kryptert disk.** LUKS på datavolumet. Helsedata krypteres i tillegg på
   feltnivå med egen nøkkel.
4. **Hemmeligheter utenfor git.** SOPS + age i repo, dekryptert kun på noden.
5. **Minste privilegium per konnektor.** Kalender-konnektoren ser aldri
   Tibber-tokenet.
6. **Alt logges lokalt, ingenting logges ut av huset** uten eksplisitt samtykke.
   Feilrapportering er opt-in og anonymisert.

## Sky-grensen

Det eneste stedet data kan forlate huset er sky-modellen. Derfor er den regulert
strengt:

```
Tillatt ut:   spørsmålet, relevant kontekst, generelle fakta
Aldri ut:     fulle navn, adresse, fødselsnummer, helseopplysninger,
              posisjonshistorikk, hele husstandsprofilen, lydopptak
Krav:         nivå GRØNN + AINA_CLOUD_ALLOWED=true + brukeren har samtykket
Logg:         hvert sky-kall logges lokalt med hva som ble sendt, lesbart for kunden
```

Kunden skal kunne slå av sky-modellen helt og fortsatt ha et fungerende produkt.
Det er en produktbeslutning like mye som en sikkerhetsbeslutning: kan man ikke slå
den av, er ikke systemet reelt lokalt.

## GDPR og norsk rett, praktisk

- **Behandlingsansvarlig er kunden**, ikke oss — dataene ligger på kundens
  maskinvare. Det forenkler mye, men fritar oss ikke som databehandler for det
  som eventuelt går via vår sky.
- **Databehandleravtale** kreves for hver tredjepart som faktisk behandler
  personopplysninger (SMS-leverandør, sky-modell, e-postleverandør).
- **Barns data** krever særskilt varsomhet. Foreldre kan samtykke, men designet
  bør uansett minimere: trenger Aina virkelig posisjonshistorikk for et barn,
  eller holder «hjemme / ikke hjemme»?
- **Innsyn, retting, sletting** løses ved at hele profilen er én eksporterbar
  fil kunden eier. Sletting er reell sletting av filen og indeksene.
- **Lydopptak av gjester** i hjemmet: informer, og lagre aldri lyd.

## Ting vi bevisst **ikke** bygger

- Ingen ansiktsgjenkjenning. Gevinsten er liten, personvernkostnaden og
  feilraten stor, og det gjør systemet vanskeligere å forsvare.
- Ingen kontinuerlig lydlagring eller «alltid på»-transkripsjon.
- Ingen skjult drift eller funksjoner som ikke fremgår av grensesnittet.
- Ingen automatisk kontakt med nødetater. Aina kan gi deg nummeret, forberede
  informasjonen og vise veien — mennesket ringer.

## Sikkerhetsoppgaver før første kunde

- [ ] Trusselmodellen gjennomgått med noen utenfra
- [ ] Full diskkryptering med TPM-basert oppstart verifisert
- [ ] mTLS mellom panel og kjerne, sertifikatrullering testet
- [ ] Sky-filteret dekket av tester som feiler ved lekkasje av PII
- [ ] Signerte, verifiserbare oppdateringer
- [ ] Gjenopprettingstest: ny maskinvare fra kryptert backup på under en time
- [ ] Ekstern penetrasjonstest av panel-til-kjerne og WireGuard
- [ ] Personvernerklæring og databehandleravtaler på plass
