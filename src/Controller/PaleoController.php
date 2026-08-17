<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Contrôleur du blog « Paléo » (neumes & chant grégorien).
 *
 * Chaque page est une simple vue statique : on rend le template Twig
 * correspondant. Les noms de routes (paleo_index, paleo_notation, …) sont
 * ceux utilisés par path() dans templates/base.html.twig — ne les renommez
 * pas sans mettre le gabarit à jour.
 *
 * NB : nécessite symfony/framework-bundle et twig. Les attributs de route
 * (#[Route]) requièrent PHP 8.0+ et Symfony 6.2+ ; pour une version plus
 * ancienne, remplacez-les par des annotations ou une config YAML.
 */
class PaleoController extends AbstractController
{
    #[Route('/', name: 'paleo_index')]
    public function index(): Response
    {
        return $this->render('paleo/index.html.twig');
    }

    #[Route('/vous-avez-dit-gregorien', name: 'paleo_histoire')]
    public function histoire(): Response
    {
        return $this->render('paleo/histoire.html.twig');
    }

    #[Route('/les-bases', name: 'paleo_notation')]
    public function notation(): Response
    {
        return $this->render('paleo/notation.html.twig');
    }

    #[Route('/graduale-triplex', name: 'paleo_triplex')]
    public function triplex(): Response
    {
        return $this->render('paleo/graduale-triplex.html.twig');
    }

    #[Route('/puer-natus-est', name: 'paleo_puer')]
    public function puer(): Response
    {
        return $this->render('paleo/puer-natus-est.html.twig');
    }

    #[Route('/viderunt-omnes', name: 'paleo_viderunt')]
    public function viderunt(): Response
    {
        return $this->render('paleo/viderunt-omnes.html.twig');
    }

    #[Route('/lux-fulgebit', name: 'paleo_lux')]
    public function lux(): Response
    {
        return $this->render('paleo/lux-fulgebit.html.twig');
    }

    #[Route('/victimae-paschali', name: 'paleo_victimae')]
    public function victimae(): Response
    {
        return $this->render('paleo/victimae-paschalis.html.twig');
    }

    #[Route('/alleluia-dies-sanctificatus', name: 'paleo_alleluia_noel')]
    public function alleluiaNoel(): Response
    {
        return $this->render('paleo/alleluia-noel.html.twig');
    }

    #[Route('/alleluia-pascha-nostrum', name: 'paleo_alleluia_paques')]
    public function alleluiaPaques(): Response
    {
        return $this->render('paleo/alleluia-paques.html.twig');
    }

    #[Route('/glossaire', name: 'paleo_glossaire')]
    public function glossaire(): Response
    {
        return $this->render('paleo/glossaire.html.twig');
    }

    #[Route('/a-propos', name: 'paleo_apropos')]
    public function apropos(): Response
    {
        return $this->render('paleo/a-propos.html.twig');
    }

    /* ------------------------------------------------------------------ */
    /* Version allemande — templates/paleo/de/, routes paleo_de_*          */
    /* ------------------------------------------------------------------ */

    #[Route('/de/', name: 'paleo_de_index')]
    public function deIndex(): Response
    {
        return $this->render('paleo/de/index.html.twig');
    }

    #[Route('/de/was-heisst-gregorianisch', name: 'paleo_de_histoire')]
    public function deHistoire(): Response
    {
        return $this->render('paleo/de/histoire.html.twig');
    }

    #[Route('/de/grundlagen', name: 'paleo_de_notation')]
    public function deNotation(): Response
    {
        return $this->render('paleo/de/notation.html.twig');
    }

    #[Route('/de/graduale-triplex', name: 'paleo_de_triplex')]
    public function deTriplex(): Response
    {
        return $this->render('paleo/de/graduale-triplex.html.twig');
    }

    #[Route('/de/puer-natus-est', name: 'paleo_de_puer')]
    public function dePuer(): Response
    {
        return $this->render('paleo/de/puer-natus-est.html.twig');
    }

    #[Route('/de/viderunt-omnes', name: 'paleo_de_viderunt')]
    public function deViderunt(): Response
    {
        return $this->render('paleo/de/viderunt-omnes.html.twig');
    }

    #[Route('/de/lux-fulgebit', name: 'paleo_de_lux')]
    public function deLux(): Response
    {
        return $this->render('paleo/de/lux-fulgebit.html.twig');
    }

    #[Route('/de/victimae-paschali', name: 'paleo_de_victimae')]
    public function deVictimae(): Response
    {
        return $this->render('paleo/de/victimae-paschalis.html.twig');
    }

    #[Route('/de/alleluia-dies-sanctificatus', name: 'paleo_de_alleluia_noel')]
    public function deAlleluiaNoel(): Response
    {
        return $this->render('paleo/de/alleluia-noel.html.twig');
    }

    #[Route('/de/alleluia-pascha-nostrum', name: 'paleo_de_alleluia_paques')]
    public function deAlleluiaPaques(): Response
    {
        return $this->render('paleo/de/alleluia-paques.html.twig');
    }

    #[Route('/de/glossar', name: 'paleo_de_glossaire')]
    public function deGlossaire(): Response
    {
        return $this->render('paleo/de/glossaire.html.twig');
    }

    #[Route('/de/ueber-die-autorin', name: 'paleo_de_apropos')]
    public function deApropos(): Response
    {
        return $this->render('paleo/de/a-propos.html.twig');
    }

    /* ------------------------------------------------------------------ */
    /* Version anglaise — templates/paleo/en/, routes paleo_en_*           */
    /* ------------------------------------------------------------------ */

    #[Route('/en/', name: 'paleo_en_index')]
    public function enIndex(): Response
    {
        return $this->render('paleo/en/index.html.twig');
    }

    #[Route('/en/what-is-gregorian-chant', name: 'paleo_en_histoire')]
    public function enHistoire(): Response
    {
        return $this->render('paleo/en/histoire.html.twig');
    }

    #[Route('/en/the-basics', name: 'paleo_en_notation')]
    public function enNotation(): Response
    {
        return $this->render('paleo/en/notation.html.twig');
    }

    #[Route('/en/graduale-triplex', name: 'paleo_en_triplex')]
    public function enTriplex(): Response
    {
        return $this->render('paleo/en/graduale-triplex.html.twig');
    }

    #[Route('/en/puer-natus-est', name: 'paleo_en_puer')]
    public function enPuer(): Response
    {
        return $this->render('paleo/en/puer-natus-est.html.twig');
    }

    #[Route('/en/viderunt-omnes', name: 'paleo_en_viderunt')]
    public function enViderunt(): Response
    {
        return $this->render('paleo/en/viderunt-omnes.html.twig');
    }

    #[Route('/en/lux-fulgebit', name: 'paleo_en_lux')]
    public function enLux(): Response
    {
        return $this->render('paleo/en/lux-fulgebit.html.twig');
    }

    #[Route('/en/victimae-paschali', name: 'paleo_en_victimae')]
    public function enVictimae(): Response
    {
        return $this->render('paleo/en/victimae-paschalis.html.twig');
    }

    #[Route('/en/alleluia-dies-sanctificatus', name: 'paleo_en_alleluia_noel')]
    public function enAlleluiaNoel(): Response
    {
        return $this->render('paleo/en/alleluia-noel.html.twig');
    }

    #[Route('/en/alleluia-pascha-nostrum', name: 'paleo_en_alleluia_paques')]
    public function enAlleluiaPaques(): Response
    {
        return $this->render('paleo/en/alleluia-paques.html.twig');
    }

    #[Route('/en/glossary', name: 'paleo_en_glossaire')]
    public function enGlossaire(): Response
    {
        return $this->render('paleo/en/glossaire.html.twig');
    }

    #[Route('/en/about-the-author', name: 'paleo_en_apropos')]
    public function enApropos(): Response
    {
        return $this->render('paleo/en/a-propos.html.twig');
    }
}
