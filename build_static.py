#!/usr/bin/env python3
"""
build_static.py — génère une version HTML statique (dossier preview/) à partir
des templates Twig, pour prévisualiser le blog dans un navigateur SANS Symfony.

Trois langues sont produites :
    preview/           → français (source)
    preview/de/        → allemand
    preview/en/        → anglais

Ce n'est PAS un moteur Twig complet : il ne gère que le sous-ensemble utilisé
par ce projet (extends, blocks titre / meta_description / head / contenu, set
nav_actif et set route_xx, path('route'), path(variable), asset(), et
l'opérateur ternaire sur nav_actif). Les templates restent la source de
vérité ; ce script n'est qu'un utilitaire de prévisualisation — mais comme
Dockerfile en fait un des étages du build de production (le résultat, servi
par nginx, EST le site en ligne), c'est aussi ici qu'on injecte les balises
SEO (canonical, hreflang, Open Graph, Twitter Card) et qu'on génère
sitemap.xml / robots.txt.

Usage :  python3 build_static.py
Puis ouvrez  preview/index.html  dans votre navigateur.
"""

import re
import shutil
import sys
from datetime import date
from pathlib import Path

# La sortie console peut être en latin-1 selon la locale : on force l'UTF-8
# pour que les messages accentués ne fassent pas planter le script.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
TPL = ROOT / "templates"
PAGES = TPL / "paleo"
OUT = ROOT / "preview"

# Domaine public du site, utilisé pour les URLs absolues (canonical, hreflang,
# Open Graph, sitemap) — voir SEO_LOCALE / page_url() plus bas.
SITE = "https://paleo.kreilos.fr"
SEO_LOCALE = {"fr": "fr_FR", "de": "de_DE", "en": "en_US"}

# Les onze pages du blog : (fichier template, fichier de sortie, suffixe de route)
# Le suffixe de route sert à construire les noms de routes Symfony :
#   français → paleo_<suffixe>        allemand → paleo_de_<suffixe>
#   anglais  → paleo_en_<suffixe>
PAGES_LIST = [
    ("index.html.twig",              "index.html",              "index"),
    ("histoire.html.twig",           "histoire.html",           "histoire"),
    ("notation.html.twig",           "notation.html",           "notation"),
    ("graduale-triplex.html.twig",   "graduale-triplex.html",   "triplex"),
    ("puer-natus-est.html.twig",     "puer-natus-est.html",     "puer"),
    ("viderunt-omnes.html.twig",     "viderunt-omnes.html",     "viderunt"),
    ("lux-fulgebit.html.twig",       "lux-fulgebit.html",       "lux"),
    ("victimae-paschalis.html.twig", "victimae-paschalis.html", "victimae"),
    ("alleluia-noel.html.twig",      "alleluia-noel.html",      "alleluia_noel"),
    ("alleluia-paques.html.twig",    "alleluia-paques.html",    "alleluia_paques"),
    ("glossaire.html.twig",          "glossaire.html",          "glossaire"),
    ("a-propos.html.twig",           "a-propos.html",           "apropos"),
]

# langue → (sous-dossier de templates, sous-dossier de sortie, gabarit)
LANGS = {
    "fr": ("",   "",   "base.html.twig"),
    "de": ("de", "de", "base.de.html.twig"),
    "en": ("en", "en", "base.en.html.twig"),
}


def page_url(lang, out_name):
    """URL absolue publique d'une page (canonical, hreflang, sitemap, OG)."""
    _tpl_dir, out_dir, _base = LANGS[lang]
    path = f"{out_dir}/{out_name}" if out_dir else out_name
    return f"{SITE}/{path}"


def route_name(lang, suffix):
    return f"paleo_{suffix}" if lang == "fr" else f"paleo_{lang}_{suffix}"


def route_table(current_lang):
    """route Symfony → chemin relatif, vu depuis une page de current_lang."""
    table = {}
    for lang, (_tpl_dir, out_dir, _base) in LANGS.items():
        for _tpl, out_name, suffix in PAGES_LIST:
            if lang == current_lang:
                target = out_name
            elif current_lang == "fr":
                target = f"{out_dir}/{out_name}"
            elif lang == "fr":
                target = f"../{out_name}"
            else:
                target = f"../{out_dir}/{out_name}"
            table[route_name(lang, suffix)] = target
    return table


def block(name, text, default=""):
    """Retourne le contenu du bloc Twig {% block name %}...{% endblock %}."""
    m = re.search(r"{%\s*block\s+" + name + r"\s*%}(.*?){%\s*endblock\s*%}",
                  text, re.DOTALL)
    return m.group(1) if m else default


def twig_sets(text):
    """Récupère toutes les affectations {% set nom = 'valeur' %} d'une page."""
    return dict(re.findall(r"{%\s*set\s+(\w+)\s*=\s*'([^']*)'\s*%}", text))


def resolve_functions(text, nav_actif, routes, variables, asset_prefix):
    """Remplace path(), asset() et le ternaire sur nav_actif par leur valeur."""
    # ternaire :  {{ nav_actif == 'x' ? 'aria-current="page"' : '' }}
    def ternary(m):
        return 'aria-current="page"' if nav_actif == m.group(1) else ""
    text = re.sub(
        r"""{{\s*nav_actif\s*==\s*'([^']+)'\s*\?\s*'aria-current="page"'\s*:\s*''\s*}}""",
        ternary, text)

    # path('route')  ->  fichier.html
    text = re.sub(
        r"{{\s*path\(\s*'([^']+)'\s*\)\s*}}",
        lambda m: routes.get(m.group(1), "#" + m.group(1)),
        text)

    # path(variable)  ->  la variable contient un nom de route (sélecteur de langue)
    def path_var(m):
        route = variables.get(m.group(1), "")
        return routes.get(route, "#" + (route or m.group(1)))
    text = re.sub(r"{{\s*path\(\s*(\w+)\s*\)\s*}}", path_var, text)

    # asset('css/...') / asset('assets/...')  ->  chemin relatif
    text = re.sub(
        r"{{\s*asset\(\s*'([^']+)'\s*\)\s*}}",
        lambda m: asset_prefix + m.group(1),
        text)
    return text


def build_lang(lang, base_text):
    tpl_dir, out_dir, _base_name = LANGS[lang]
    src = PAGES / tpl_dir if tpl_dir else PAGES
    dest = OUT / out_dir if out_dir else OUT
    dest.mkdir(parents=True, exist_ok=True)

    routes = route_table(lang)
    asset_prefix = "" if lang == "fr" else "../"
    count = 0

    for tpl_name, out_name, _suffix in PAGES_LIST:
        page_file = src / tpl_name
        if not page_file.exists():
            print(f"  [!!] {lang}: {tpl_name} manquant - page ignoree")
            continue
        page = page_file.read_text(encoding="utf-8")

        variables = twig_sets(page)
        nav_actif = variables.get("nav_actif", "")

        titre = block("titre", page, "Paléo").strip()
        meta = block("meta_description", page).strip()
        head_extra = block("head", page).strip()
        contenu = block("contenu", page)

        html = base_text
        html = re.sub(r"{%\s*block\s+titre\s*%}.*?{%\s*endblock\s*%}",
                      lambda _: titre, html, flags=re.DOTALL)
        if meta:
            html = re.sub(r"{%\s*block\s+meta_description\s*%}.*?{%\s*endblock\s*%}",
                          lambda _: meta, html, flags=re.DOTALL)
        else:
            html = re.sub(r"{%\s*block\s+meta_description\s*%}(.*?){%\s*endblock\s*%}",
                          r"\1", html, flags=re.DOTALL)
        html = re.sub(r"{%\s*block\s+head\s*%}.*?{%\s*endblock\s*%}",
                      lambda _: head_extra, html, flags=re.DOTALL)
        html = re.sub(r"{%\s*block\s+contenu\s*%}.*?{%\s*endblock\s*%}",
                      lambda _: contenu, html, flags=re.DOTALL)

        # Canonical, hreflang (fr/de/en + x-default) et Open Graph/Twitter
        # Card, générés depuis les données déjà connues du script (aucune
        # édition de gabarit nécessaire, reste juste si des pages sont
        # ajoutées/retirées de PAGES_LIST).
        canonical = page_url(lang, out_name)
        alt_tags = "\n".join(
            f'    <link rel="alternate" hreflang="{al}" href="{page_url(al, out_name)}">'
            for al in ("fr", "de", "en")
        )
        alt_tags += (f'\n    <link rel="alternate" hreflang="x-default" '
                     f'href="{page_url("fr", out_name)}">')
        seo_tags = (
            f'    <link rel="canonical" href="{canonical}">\n'
            f'{alt_tags}\n'
            f'    <meta property="og:type" content="website">\n'
            f'    <meta property="og:site_name" content="Paléo">\n'
            f'    <meta property="og:locale" content="{SEO_LOCALE[lang]}">\n'
            f'    <meta property="og:title" content="{titre}">\n'
            f'    <meta property="og:description" content="{meta}">\n'
            f'    <meta property="og:url" content="{canonical}">\n'
            f'    <meta name="twitter:card" content="summary">\n'
            f'    <meta name="twitter:title" content="{titre}">\n'
            f'    <meta name="twitter:description" content="{meta}">\n'
        )
        html = html.replace("</head>", seo_tags + "</head>", 1)

        # commentaires Twig éventuels dans le contenu de page
        html = re.sub(r"{#.*?#}", "", html, flags=re.DOTALL)
        # affectations {% set ... %} résiduelles
        html = re.sub(r"{%\s*set\s+\w+\s*=\s*'[^']*'\s*%}\s*", "", html)

        html = resolve_functions(html, nav_actif, routes, variables, asset_prefix)

        (dest / out_name).write_text(html, encoding="utf-8")
        rel = f"{out_dir}/{out_name}" if out_dir else out_name
        print(f"  [ok] {rel}")
        count += 1
    return count


def write_sitemap():
    """sitemap.xml listant les 36 pages (12 x fr/de/en), avec les variantes
    de langue en <xhtml:link> pour chaque URL (recommandé par Google pour
    les sites multilingues)."""
    today = date.today().isoformat()
    entries = []
    for _tpl, out_name, _suffix in PAGES_LIST:
        for lang in LANGS:
            url = page_url(lang, out_name)
            alt_links = "\n".join(
                f'      <xhtml:link rel="alternate" hreflang="{al}" '
                f'href="{page_url(al, out_name)}"/>'
                for al in LANGS
            )
            entries.append(
                f"  <url>\n"
                f"    <loc>{url}</loc>\n"
                f"{alt_links}\n"
                f'      <xhtml:link rel="alternate" hreflang="x-default" '
                f'href="{page_url("fr", out_name)}"/>\n'
                f"    <lastmod>{today}</lastmod>\n"
                f"  </url>"
            )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n"
        "</urlset>\n"
    )
    (OUT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"  [ok] sitemap.xml ({len(PAGES_LIST) * len(LANGS)} URLs)")


def write_robots():
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )
    (OUT / "robots.txt").write_text(txt, encoding="utf-8")
    print("  [ok] robots.txt")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # copie des assets (CSS, images, audio)
    shutil.copytree(ROOT / "public" / "css", OUT / "css")
    if (ROOT / "public" / "assets").exists():
        shutil.copytree(ROOT / "public" / "assets", OUT / "assets")

    total = 0
    for lang, (_tpl_dir, _out_dir, base_name) in LANGS.items():
        base_file = TPL / base_name
        if not base_file.exists():
            print(f"  [!!] gabarit {base_name} absent - langue {lang} ignoree")
            continue
        # On retire d'abord les commentaires Twig {# ... #} : le commentaire
        # d'en-tête du gabarit contient du texte ressemblant à des balises
        # ({% block titre %}…) qui piégerait les substitutions suivantes.
        base_text = re.sub(r"{#.*?#}", "", base_file.read_text(encoding="utf-8"),
                           flags=re.DOTALL)
        total += build_lang(lang, base_text)

    write_sitemap()
    write_robots()

    print(f"\nOK — {total} pages générées dans {OUT}/")
    print(f"Ouvrez : {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
