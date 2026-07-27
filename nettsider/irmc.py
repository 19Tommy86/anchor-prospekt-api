"""
Innhold for IRMC-nettsiden.

KILDE OG FORBEHOLD
------------------
Innholdet under er rekonstruert fra søketreff mot irmc.no (Hjem, Studio,
Tjenester, Label). Serveren til irmc.no svarte 403 på direkte oppslag, så
sidene er IKKE lest ordrett. Formuleringene under er derfor omskrevet av
meg basert på sammendrag, ikke sitert ordrett fra den eksisterende siden.

Alt her må leses gjennom av eier før publisering.

  [BEKREFTET]  = fremgår tydelig av søketreffene
  [MÅ FYLLES]  = fant ingen kilde, må oppgis av eier

Felter markert [MÅ FYLLES] er satt til None og utelates automatisk fra
den genererte siden i stedet for å vises som tomme eller oppdiktede.
"""

from datetime import date

INNHOLD = {
    # --- Identitet ---
    "navn": "IRMC",                                   # [BEKREFTET]
    "logo_aksent": " NORWAY",                         # [BEKREFTET] "IRMC Norway"
    "juridisk_navn": "IRMC AS",                       # oppgitt av eier
    "overskrift": "International Records Music Company",   # [BEKREFTET]
    "kicker": "Plateselskap & studio · Oslo",         # [BEKREFTET]
    "tagline": (
        "Vi er et plateselskap som slipper urban- og popmusikk av høy kvalitet, "
        "med eget musikkstudio sentralt i Oslo."
    ),                                                # [BEKREFTET] label + studio
    "meta_beskrivelse": (
        "IRMC Norway – plateselskap og musikkstudio i Oslo. Vokalinnspilling, "
        "musikkproduksjon, miks, mastering, release og promotering."
    ),

    # --- Kontakt ---
    "epost": "irmcnorway@gmail.com",                  # [BEKREFTET]
    "telefon": None,                                  # [MÅ FYLLES] fant ikke nummer
    "telefon_lenke": None,
    "sted": "Hasle, Oslo",                            # [BEKREFTET] omtalt som Hasle/Økern
    "cta_tekst": "Book studiotid",

    "sosialt": [                                      # [BEKREFTET] begge finnes
        {"navn": "Facebook", "url": "https://www.facebook.com/irmcnorway/"},
        {"navn": "Instagram", "url": "https://www.instagram.com/irmcnorway/"},
    ],

    # --- Tjenester ---
    # [BEKREFTET] "alt fra vokalinnspilling, musikkproduksjon, miks,
    # mastering til release og promotering"
    "tjenester_overskrift": "Fra idé til ferdig utgivelse",
    "tjenester_ingress": (
        "Vi tar hånd om hele kjeden i eget studio – du trenger ikke koordinere "
        "fem ulike leverandører for å få ut én låt."
    ),
    "tjenester": [
        {"navn": "Vokalinnspilling",
         "beskrivelse": "Profesjonelt lydopptak med tekniker i studio."},
        {"navn": "Musikkproduksjon",
         "beskrivelse": "Produksjon og beats bygget rundt uttrykket ditt."},
        {"navn": "Miks",
         "beskrivelse": "Vi setter sammen sporene til en helhetlig låt."},
        {"navn": "Mastering",
         "beskrivelse": "Siste finpuss så låten står seg på alle plattformer."},
        {"navn": "Release",
         "beskrivelse": "Vi håndterer utgivelsen og får musikken ut."},
        {"navn": "Promotering",
         "beskrivelse": "Arbeidet som gjør at noen faktisk hører låten."},
    ],

    # --- Abonnement ---
    # [BEKREFTET] alle punktene under fremgår av søketreffene
    "tilbud": {
        "merkelapp": "Abonnement",
        "tittel": "Din egen EP, klar for release på 6 måneder",
        "beskrivelse": (
            "Én låt i måneden i seks måneder. Du velger én fast dag i uken, "
            "kommer inn i et profesjonelt studio sentralt i Oslo, og lager "
            "din egen musikk sammen med folk som gjør dette hver dag."
        ),
        "punkter": [
            "10 timer opptak med tekniker hver måned",
            "Én miks og master hver måned",
            "Én produksjon/beat hver måned",
            "Fast studiodag hver uke – du slipper å jage timer",
            "Ferdig EP klar for utgivelse etter 6 måneder",
        ],
        "vilkaar": "6 måneders bindingstid. Ta kontakt for pris og ledige plasser.",
        # [MÅ FYLLES] pris – fant ingen prisopplysninger
    },

    # --- Om oss ---
    "om_overskrift": "Et lite selskap som gjør hele jobben",
    "blokker": [
        {
            "tittel": "Plateselskapet",
            "avsnitt": [
                # [BEKREFTET] etablert 2017, urban/pop, team med lang erfaring
                "IRMC ble etablert i 2017 og gir ut urban- og popmusikk av høy "
                "kvalitet. Bak selskapet står et team med lang erfaring fra bransjen.",
                "Som plateselskap jobber vi for å gi artistene våre verktøyene de "
                "trenger for å lykkes – og for å lage musikken de faktisk vil lage.",
            ],
        },
        {
            "tittel": "Studioet",
            "avsnitt": [
                # [BEKREFTET] eget studio sentralt i Oslo, åpent for alle
                "Vi har vårt eget studio sentralt i Oslo, hvor talentfulle artister, "
                "produsenter og musikere jobber til daglig.",
                "Studioet er ikke forbeholdt artistene på labelen. Vi tar imot alle "
                "som vil prøve seg som artist, eller som trenger lydopptak av høy "
                "kvalitet.",
            ],
        },
    ],

    # --- Kontakt-seksjon ---
    "kontakt_overskrift": "Kom innom studio",
    "kontakt_ingress": (
        "Send en e-post med hva du vil lage, så finner vi ut av resten sammen."
    ),

    "aar": date.today().year,

    # --- Meny ---
    "meny": [
        {"id": "tjenester", "tekst": "Tjenester"},
        {"id": "tilbud", "tekst": "Abonnement"},
        {"id": "om", "tekst": "Om oss"},
        {"id": "kontakt", "tekst": "Kontakt"},
    ],
}
