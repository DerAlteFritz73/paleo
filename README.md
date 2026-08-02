# Paléo — blog de vulgarisation sur les neumes et le chant grégorien

Ébauche d'un mini-site Symfony (Twig) qui explique l'écriture des neumes du
chant grégorien à un public non initié, à partir de six chants du
*Graduale Triplex* :

1. **Puer natus est** — introït du jour de Noël (chant neumatique) ;
2. **Viderunt omnes** — graduel de Noël (chant mélismatique) ;
3. **Lux fulgebit** — introït de l'aurore de Noël (nuances de durée) ;
4. **Victimæ paschali laudes** — séquence de Pâques (chant syllabique / strophique) ;
5. **Alleluia. Dies sanctificatus** — Alleluia du jour de Noël (le jubilus) ;
6. **Alleluia. Pascha nostrum** — Alleluia du jour de Pâques (comparaison des modes).

Le site existe en **trois langues** — français, allemand, anglais — soit onze
pages par langue, reliées par un sélecteur FR · DE · EN dans l'en-tête.

## Arborescence fournie

```
public/
  css/style.css              ← feuille de style (thème « manuscrit », responsive, mode sombre)
  assets/img/                ← déposez ici vos fac-similés (voir plus bas)
src/
  Controller/PaleoController.php   ← une route par page
templates/
  base.html.twig             ← gabarit français (en-tête, menu, pied de page)
  base.de.html.twig          ← gabarit allemand
  base.en.html.twig          ← gabarit anglais
  paleo/
    index.html.twig          ← introduction générale
    histoire.html.twig       ← « Vous avez dit grégorien ? » (histoire, sources)
    notation.html.twig       ← les bases (portée, clés, neumes + schémas SVG)
    graduale-triplex.html.twig ← les trois écritures superposées
    puer-natus-est.html.twig
    viderunt-omnes.html.twig
    lux-fulgebit.html.twig
    victimae-paschalis.html.twig
    alleluia-noel.html.twig      ← Alleluia. Dies sanctificatus
    alleluia-paques.html.twig    ← Alleluia. Pascha nostrum
    glossaire.html.twig
    de/                      ← les mêmes onze pages, en allemand
    en/                      ← les mêmes onze pages, en anglais
```

Les gabarits `de/` et `en/` sont des **traductions du contenu** : la structure
HTML (schémas SVG, tableaux, iframes, classes CSS) y est identique à celle du
français. Si vous modifiez la structure d'une page française, reportez la même
modification dans les deux autres langues.

## Intégration dans un projet Symfony

1. Copiez `templates/paleo/` et `base.html.twig` dans votre dossier `templates/`.
   Si vous avez déjà un `base.html.twig`, renommez celui-ci (p. ex. `paleo_base.html.twig`)
   et adaptez le `{% extends %}` de chaque page.
2. Copiez `src/Controller/PaleoController.php` dans votre `src/Controller/`.
3. Copiez `public/css/style.css` dans votre `public/css/`.
   La feuille est appelée via `{{ asset('css/style.css') }}` → pensez à
   `composer require symfony/asset` si le composant n'est pas installé.
4. Vérifiez que le routing par attributs est activé (`config/routes.yaml` avec
   `App\Controller` en `type: attribute`), puis visitez `/`.

Les routes suivent une convention simple : `paleo_xxx` en français,
`paleo_de_xxx` sous `/de/`, `paleo_en_xxx` sous `/en/`. Chaque page déclare, en
tête de fichier, les variables `route_fr` / `route_de` / `route_en` que le
sélecteur de langue du gabarit passe à `path()`.

Les liens de navigation utilisent `path('paleo_xxx')`. Si vous prévisualisez les
templates **hors** Symfony, remplacez temporairement `path('paleo_xxx')` et
`asset(...)` par des URL en dur.

## Prévisualiser sans Symfony (version statique)

Un script convertit les templates Twig en HTML statique pour un aperçu immédiat
dans le navigateur :

```bash
python3 build_static.py       # génère le dossier preview/ (33 pages : fr, de, en)
```

Ouvrez ensuite `preview/index.html` (l'allemand est dans `preview/de/`,
l'anglais dans `preview/en/`). Pour que les liens et les vidéos fonctionnent
bien (certains navigateurs bloquent les iframes ouvertes en `file://`), servez le
dossier plutôt que d'ouvrir le fichier directement :

```bash
cd preview && python3 -m http.server 8000
# puis http://localhost:8000/
```

> `preview/` est **généré** : ne l'éditez pas à la main, modifiez les templates
> Twig puis relancez le script. La source de vérité reste `templates/`.

## Version imprimable (PDF)

Un second script assemble les onze pages d'une langue en un seul document et
le convertit en PDF A4 avec Chromium en mode « headless » :

```bash
python3 build_pdf.py          # français  → dist/paleo-blog.pdf     (37 pages)
python3 build_pdf.py de       # allemand  → dist/paleo-blog-de.pdf  (39 pages)
python3 build_pdf.py en       # anglais   → dist/paleo-blog-en.pdf  (37 pages)
```

Chaque PDF est aussi recopié dans `public/assets/`, où le bouton de
téléchargement de la page d'accueil va le chercher. Après toute modification de
contenu, relancez les trois langues et ajustez si besoin le nombre de pages
annoncé sous le bouton (`.hero-pdf-note`).

## Écouter les chants (vidéos YouTube)

Chaque page de chant intègre plusieurs interprétations via des iframes
`youtube-nocookie.com` (mode sans cookie de suivi). Si votre projet Symfony
applique une **politique de sécurité de contenu (CSP)**, autorisez ces sources,
par exemple :

```
frame-src https://www.youtube-nocookie.com https://www.youtube.com;
```

Le dossier `public/assets/audio/` reste disponible si vous préférez héberger vos
propres fichiers MP3 (l'ancien lecteur `<audio>` est facile à réintroduire).

## Insérer les fac-similés

Le contenu ne reproduit **aucune** image du *Graduale Triplex* (droits réservés).
Chaque page comporte un bloc `.facsimile` en pointillés : c'est l'emplacement où
insérer votre propre scan/photo, ou un renvoi vers un manuscrit numérisé en accès
libre (par ex. e-codices pour Saint-Gall / Einsiedeln, Gallica / bibliothèques
pour Laon 239). Déposez les images dans `public/assets/img/` et remplacez le bloc
par une balise `<img>` (l'exemple est donné dans chaque page).

## Points de vigilance / pistes d'amélioration

- **Exactitude musicale** : les commentaires « syllabe par syllabe » sont
  volontairement prudents et pédagogiques. Avant publication, faites-les relire
  par un·e chantre ou un·e spécialiste, et calez-les sur l'édition exacte que vous
  reproduisez.
- **Audio** : ajouter un lecteur (enregistrement de chaque chant) renforcerait
  beaucoup la pédagogie.
- **Accessibilité** : les schémas SVG ont un `role="img"` + `aria-label` ; pensez
  à vérifier les contrastes si vous modifiez la palette.
- **Enregistrements manquants** : les deux pages Alleluia et la section
  « Exemples musicaux » de la page d'histoire contiennent un commentaire Twig
  avec le gabarit d'iframe à remplir — aucun identifiant de vidéo n'a été
  inventé.
- **Traductions** : elles sont à relire par un locuteur natif avant publication,
  en particulier le vocabulaire technique (neume, épisème, *litteræ
  significativæ*), dont les usages varient d'une école à l'autre.
