#!/usr/bin/env python3
"""
build_pdf.py — assemble les onze pages du blog en UN seul document HTML optimisé
pour l'impression A4 (dist/paleo-blog[-langue].html), puis le convertit en PDF
avec Chromium headless (dist/paleo-blog[-langue].pdf).

- Les templates Twig restent la source de vérité.
- Les iframes YouTube (non imprimables) sont converties en liste de liens.
- Les liens internes path('paleo_xxx') deviennent des ancres (#...).

Usage :  python3 build_pdf.py            → les trois langues
         python3 build_pdf.py fr         → français seul (idem de / en)
"""

import re
import subprocess
import shutil
import sys
from datetime import date
from pathlib import Path

# La sortie console peut être en latin-1 selon la locale : on force l'UTF-8
# pour que les messages accentués ne fassent pas planter le script.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
PAGES_ROOT = ROOT / "templates" / "paleo"
CSS = ROOT / "public" / "css" / "style.css"
DIST = ROOT / "dist"

# Ordre du document : (fichier template, id d'ancre, suffixe de route)
PAGE_ORDER = [
    ("index.html.twig",              "accueil",            "index"),
    ("histoire.html.twig",           "histoire",           "histoire"),
    ("notation.html.twig",           "notation",           "notation"),
    ("graduale-triplex.html.twig",   "triplex",            "triplex"),
    ("puer-natus-est.html.twig",     "puer-natus-est",     "puer"),
    ("viderunt-omnes.html.twig",     "viderunt-omnes",     "viderunt"),
    ("lux-fulgebit.html.twig",       "lux-fulgebit",       "lux"),
    ("victimae-paschalis.html.twig", "victimae-paschalis", "victimae"),
    ("alleluia-noel.html.twig",      "alleluia-noel",      "alleluia_noel"),
    ("alleluia-paques.html.twig",    "alleluia-paques",    "alleluia_paques"),
    ("glossaire.html.twig",          "glossaire",          "glossaire"),
]

# Titres du sommaire, par langue. La référence « T. p. XX » renvoie à la
# pagination du Graduale Triplex (Solesmes, 1979).
TOC_TITLES = {
    "fr": [
        "Introduction",
        "Vous avez dit « grégorien » ?",
        "Les bases de la notation",
        "Le Graduale Triplex",
        "Exemple 1 — Puer natus est · introït · T. p. 47",
        "Exemple 2 — Viderunt omnes · graduel · T. p. 48",
        "Exemple 3 — Lux fulgebit · introït · T. p. 44",
        "Exemple 4 — Victimæ paschali laudes · séquence · T. p. 198",
        "Exemple 5 — Alleluia. Dies sanctificatus · Noël · T. p. 49",
        "Exemple 6 — Alleluia. Pascha nostrum · Pâques · T. p. 197",
        "Glossaire & bibliographie",
    ],
    "de": [
        "Einführung",
        "Was heißt eigentlich „gregorianisch“?",
        "Die Grundlagen der Notation",
        "Das Graduale Triplex",
        "Beispiel 1 — Puer natus est · Introitus · T. S. 47",
        "Beispiel 2 — Viderunt omnes · Graduale · T. S. 48",
        "Beispiel 3 — Lux fulgebit · Introitus · T. S. 44",
        "Beispiel 4 — Victimæ paschali laudes · Sequenz · T. S. 198",
        "Beispiel 5 — Alleluia. Dies sanctificatus · Weihnachten · T. S. 49",
        "Beispiel 6 — Alleluia. Pascha nostrum · Ostern · T. S. 197",
        "Glossar & Bibliographie",
    ],
    "en": [
        "Introduction",
        "What do we mean by “Gregorian”?",
        "The basics of the notation",
        "The Graduale Triplex",
        "Example 1 — Puer natus est · introit · T. p. 47",
        "Example 2 — Viderunt omnes · gradual · T. p. 48",
        "Example 3 — Lux fulgebit · introit · T. p. 44",
        "Example 4 — Victimæ paschali laudes · sequence · T. p. 198",
        "Example 5 — Alleluia. Dies sanctificatus · Christmas · T. p. 49",
        "Example 6 — Alleluia. Pascha nostrum · Easter · T. p. 197",
        "Glossary & bibliography",
    ],
}

COVER = {
    "fr": {
        "lang": "fr",
        "titre_html": "Paléo — le chant grégorien pas à pas",
        "sous_titre": "Le chant grégorien et ses neumes, expliqués pas à pas",
        "desc": ("Un parcours de vulgarisation à travers six chants du "
                 "<em>Graduale Triplex</em>&nbsp;: <em>Puer natus est</em>, "
                 "<em>Viderunt omnes</em>, <em>Lux fulgebit</em>, "
                 "<em>Victimæ paschali laudes</em> et les deux <em>Alleluias</em> "
                 "de Noël et de Pâques."),
        "meta": "Version imprimable",
        "sommaire": "Sommaire",
    },
    "de": {
        "lang": "de",
        "titre_html": "Paléo — der gregorianische Choral Schritt für Schritt",
        "sous_titre": "Der gregorianische Choral und seine Neumen, Schritt für Schritt erklärt",
        "desc": ("Ein allgemein verständlicher Rundgang durch sechs Gesänge des "
                 "<em>Graduale Triplex</em>&nbsp;: <em>Puer natus est</em>, "
                 "<em>Viderunt omnes</em>, <em>Lux fulgebit</em>, "
                 "<em>Victimæ paschali laudes</em> sowie die beiden <em>Alleluia</em> "
                 "von Weihnachten und Ostern."),
        "meta": "Druckfassung",
        "sommaire": "Inhalt",
    },
    "en": {
        "lang": "en",
        "titre_html": "Paléo — Gregorian chant step by step",
        "sous_titre": "Gregorian chant and its neumes, explained step by step",
        "desc": ("A plain-language journey through six chants from the "
                 "<em>Graduale Triplex</em>&nbsp;: <em>Puer natus est</em>, "
                 "<em>Viderunt omnes</em>, <em>Lux fulgebit</em>, "
                 "<em>Victimæ paschali laudes</em> and the two <em>Alleluias</em> "
                 "of Christmas and Easter."),
        "meta": "Printable version",
        "sommaire": "Contents",
    },
}


def anchors_for(lang):
    """Table route → ancre, pour toutes les langues (les liens d'une page
    traduite pointent vers les routes de sa propre langue)."""
    table = {}
    for lg in ("fr", "de", "en"):
        prefix = "paleo_" if lg == "fr" else f"paleo_{lg}_"
        for _tpl, anchor, suffix in PAGE_ORDER:
            table[prefix + suffix] = "#" + anchor
    return table


def block(name, text):
    m = re.search(r"{%\s*block\s+" + name + r"\s*%}(.*?){%\s*endblock\s*%}",
                  text, re.DOTALL)
    return m.group(1) if m else ""


def resolve(text, anchors):
    # commentaires Twig
    text = re.sub(r"{#.*?#}", "", text, flags=re.DOTALL)
    # path('route') -> ancre interne
    text = re.sub(r"{{\s*path\(\s*'([^']+)'\s*\)\s*}}",
                  lambda m: anchors.get(m.group(1), "#" + m.group(1)), text)
    # asset('...') -> chemin (n'apparaît que dans des exemples de code)
    text = re.sub(r"{{\s*asset\(\s*'([^']+)'\s*\)\s*}}",
                  lambda m: m.group(1), text)
    return text


def videos_to_links(text):
    """Remplace chaque <figure class="video-yt">…iframe…</figure> par un lien."""
    pat = re.compile(
        r'<figure class="video-yt">\s*'
        r'<div class="ratio">\s*'
        r'<iframe [^>]*embed/([A-Za-z0-9_-]+)[^>]*>\s*</iframe>\s*'
        r'</div>\s*'
        r'<figcaption>(.*?)</figcaption>\s*'
        r'</figure>',
        re.DOTALL)

    def repl(m):
        vid, cap = m.group(1), m.group(2).strip()
        return (f'<div class="ecoute-item"><span class="ecoute-nom">{cap}</span>'
                f'<span class="ecoute-url">youtu.be/{vid}</span></div>')

    return pat.sub(repl, text)


def strip_suite(text):
    """Retire la navigation précédent/suivant, inutile en PDF."""
    return re.sub(r'<div class="suite">.*?</div>\s*', "", text, flags=re.DOTALL)


def strip_no_pdf(text):
    """Retire les éléments marqués .no-pdf (ex. bouton de téléchargement web)."""
    return re.sub(r'<div class="[^"]*\bno-pdf\b[^"]*">.*?</div>\s*', "",
                  text, flags=re.DOTALL)


def toc_entries(lang):
    return "\n".join(
        f'        <li><a href="#{anchor}"><span class="toc-t">{title}</span></a></li>'
        for (_tpl, anchor, _suffix), title in zip(PAGE_ORDER, TOC_TITLES[lang]))


def build_html(lang="fr"):
    css = CSS.read_text(encoding="utf-8")
    today = date.today().strftime("%d/%m/%Y")
    cover = COVER[lang]
    anchors = anchors_for(lang)
    src = PAGES_ROOT if lang == "fr" else PAGES_ROOT / lang

    sections = []
    for i, (tpl, anchor, _suffix) in enumerate(PAGE_ORDER):
        raw = (src / tpl).read_text(encoding="utf-8")
        content = block("contenu", raw)
        content = resolve(content, anchors)
        content = videos_to_links(content)
        content = strip_suite(content)
        content = strip_no_pdf(content)
        cls = "page-blog" + (" first" if i == 0 else "")
        sections.append(f'<section class="{cls}" id="{anchor}">\n{content}\n</section>')

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="{cover['lang']}">
<head>
<meta charset="UTF-8">
<title>{cover['titre_html']}</title>
<style>
{css}

/* ===================== Surcharges spécifiques à l'impression ===================== */
@page {{ size: A4; margin: 16mm 15mm 18mm; }}

html, body {{
  background: #fff !important;
  background-image: none !important;
  font-size: 10.7pt;
  line-height: 1.55;
}}
.pdf-wrap {{ max-width: none; margin: 0; padding: 0; }}

/* Sauts de page entre chapitres */
.page-blog {{ break-before: page; page-break-before: always; padding-top: 0.2mm; }}
.page-blog.first {{ break-before: auto; page-break-before: auto; }}

/* Évite de couper titres et blocs au mauvais endroit */
h1, h2, h3 {{ break-after: avoid; page-break-after: avoid; }}
.encadre, .fiche, .figure-neume, .texte-latin, .lecteur-audio,
table.grille, .facsimile, .carte-neume, .biblio li {{
  break-inside: avoid; page-break-inside: avoid;
}}
h1 {{ font-size: 19pt; }}
h2 {{ font-size: 15pt; }}
h3 {{ font-size: 12.5pt; }}

/* Liens : couleur d'encre, lisibles en noir & blanc */
a {{ color: var(--rubrique) !important; text-decoration: none; }}

/* Grilles de cartes : plus compactes en papier */
.grille-cartes, .galerie-neumes {{ gap: 0.6rem; }}
.carte-lien {{ box-shadow: none; }}

/* Liste d'écoutes (remplace les vidéos) */
.videos-audio {{ display: block; margin: 0.4rem 0; }}
.ecoute-item {{
  display: flex; justify-content: space-between; gap: 1rem;
  padding: 0.2rem 0; border-bottom: 1px dotted var(--ligne);
  font-family: var(--sans); font-size: 0.82rem;
}}
.ecoute-nom {{ color: var(--encre); }}
.ecoute-url {{ color: var(--encre-douce); white-space: nowrap; }}

/* Le sélecteur de langue n'a pas de sens sur papier */
.choix-langue {{ display: none !important; }}

/* Allège les ombres/gradients coûteux en encre */
.encadre, .fiche, .carte-neume, .lecteur-audio, .figure-neume {{ box-shadow: none; }}

/* ---- Couverture ---- */
.cover {{
  break-after: page; page-break-after: always;
  min-height: 245mm; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center;
}}
.cover .emoji {{ font-size: 46pt; margin-bottom: 0.4rem; }}
.cover h1 {{
  font-size: 40pt; color: var(--rubrique); margin: 0 0 0.4rem;
  letter-spacing: 0.04em; border: 0;
}}
.cover .sub {{ font-size: 15pt; font-style: italic; color: var(--encre-douce); margin: 0 0 2rem; }}
.cover .desc {{ font-size: 12pt; max-width: 30rem; margin: 0 auto; }}
.cover .rule {{ width: 60mm; border: 0; border-top: 3px double var(--or); margin: 1.6rem auto; }}
.cover .meta {{ font-family: var(--sans); font-size: 9.5pt; color: var(--encre-douce); margin-top: 2rem; }}

/* ---- Sommaire ---- */
.toc-page {{ break-after: page; page-break-after: always; }}
.toc-page h1 {{ border: 0; }}
ol.toc {{ list-style: none; counter-reset: toc; padding: 0; margin: 1.5rem 0; }}
ol.toc li {{ counter-increment: toc; padding: 0.5rem 0; border-bottom: 1px solid var(--ligne); }}
ol.toc a {{ text-decoration: none; color: var(--encre) !important; font-size: 12.5pt; }}
ol.toc li::before {{
  content: counter(toc) ". "; color: var(--or); font-weight: 700;
  font-family: var(--sans); margin-right: 0.4rem;
}}
</style>
</head>
<body>
<div class="pdf-wrap">

  <div class="cover">
    <div class="emoji">📜🎵</div>
    <h1>Paléo</h1>
    <p class="sub">{cover['sous_titre']}</p>
    <hr class="rule">
    <p class="desc">{cover['desc']}</p>
    <p class="meta">{cover['meta']} · {today}</p>
  </div>

  <div class="toc-page">
    <h1>{cover['sommaire']}</h1>
    <ol class="toc">
{toc_entries(lang)}
    </ol>
  </div>

{body}

</div>
</body>
</html>
"""


def html_to_pdf(html_out, pdf_out):
    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        print("Chromium introuvable — HTML généré, PDF non produit.")
        return False

    base = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
            "--print-to-pdf-no-header", "--no-pdf-header-footer",
            "--virtual-time-budget=15000",
            f"--print-to-pdf={pdf_out}", html_out.as_uri()]

    for headless in ("--headless=new", "--headless"):
        cmd = [chromium, headless] + base
        res = subprocess.run(cmd, capture_output=True, text=True)
        if pdf_out.exists() and pdf_out.stat().st_size > 0:
            return True
        print(f"  (essai {headless}) code={res.returncode} {res.stderr.strip()[:200]}")
    return False


def build_lang(lang):
    src = PAGES_ROOT if lang == "fr" else PAGES_ROOT / lang
    missing = [tpl for tpl, _a, _s in PAGE_ORDER if not (src / tpl).exists()]
    if missing:
        print(f"[{lang}] gabarits manquants ({len(missing)}) — langue ignorée : "
              f"{', '.join(missing[:3])}…")
        return

    suffix = "" if lang == "fr" else f"-{lang}"
    html_out = DIST / f"paleo-blog{suffix}.html"
    pdf_out = DIST / f"paleo-blog{suffix}.pdf"

    html_out.write_text(build_html(lang), encoding="utf-8")
    print(f"[{lang}] HTML combiné : {html_out}")
    if html_to_pdf(html_out, pdf_out):
        kb = pdf_out.stat().st_size // 1024
        print(f"[{lang}] PDF généré   : {pdf_out}  ({kb} Ko)")
        # Copie dans public/assets pour le rendre téléchargeable depuis le site
        pub = ROOT / "public" / "assets" / pdf_out.name
        pub.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_out, pub)
        print(f"[{lang}] Copié pour le web : {pub}")
    else:
        print(f"[{lang}] Échec de la génération du PDF.")


def main():
    DIST.mkdir(exist_ok=True)
    langs = sys.argv[1:] or ["fr", "de", "en"]
    for lang in langs:
        if lang not in COVER:
            print(f"Langue inconnue : {lang} (attendu : fr, de, en)")
            continue
        build_lang(lang)


if __name__ == "__main__":
    main()
