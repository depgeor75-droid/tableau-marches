# Avancement du projet

Référence : SPEC_Tableau_de_bord_Marches.md, puis PLAN.md (plan de l'architecte, fait foi pour les choix techniques). Mettre ce fichier à jour à la fin de chaque étape.

## Étape en cours
Étape 7 — relecture finale par le relecteur (Fable, xhigh) contre la checklist §12 ; puis corrections et remise (étape 8).

## Fait
- Étape 0 : CLAUDE.md, AVANCEMENT.md, agents `.claude/agents/`, arborescence, git local (adresse « noreply »). Python 3.12, git, `gh` (connecté, droits `repo` + `workflow`), node 26 installés. Clé FRED dans `.env` (testée).
- Design : application Aedifica lue sans modification (dossier « Aedifica interface web » sur le Bureau ; dépôt `tableau-bord-actions`). Palette, cartes, boutons de période et style des graphiques repris dans `css/style.css`.
- Étape 1 : sources testées (`docs/sources/`, 10 fichiers) ; PLAN.md rédigé par l'architecte (Fable, xhigh).
- Déjà écrit : `js/stats.js` + tests node ; `scripts/commun.py`, `fusion.py`, `calculs.py`, `sources/fred.py`, `sources/sdmx.py` + tests pytest ; `css/style.css`, `js/outils.js` (regroupe format + dom + chargement), `index.html`, `config/evenements.yaml`, `lib/chart.umd.min.js` (4.5.0).
- Étape 2 : collecte complète (scripts/collect.py, ecriture, resume, previsions, verifier, 13 modules de sources), 158 séries ok + 2 non disponibles justifiées (B11, D13_ZE) ; 94 tests pytest, 16 tests node ; revue des calculs par le relecteur (13 écarts, tous corrigés).
- Étape 3 : interface complète (Accueil, Comparateur, 8 pages thématiques avec blocs du lot 3, Comprendre, État des données) ; dépôt public https://github.com/depgeor75-droid/tableau-marches ; site https://depgeor75-droid.github.io/tableau-marches/ ; secret FRED_API_KEY ; workflow testé (push, exécution manuelle : collecte GitHub identique au local, 158 ok, aucune boucle) ; zéro erreur de console en file:// et en ligne (12 pages × PC/GSM).
- Étape 4 : 120 fiches (docs/fiches/*.json → js/fiches.js via scripts/fiches_vers_js.py) ; incertitudes des rédacteurs dans docs/fiches/incertitudes.md.
- Étapes 5-6 : README, mettre_a_jour_local.bat, événement du 5 nov. 2026 ; captures de toutes les pages PC/GSM du site public (docs/captures/), zéro erreur de console en ligne et en file://.

## Décisions
- Rediffusion (réponses de Georgy, 22/11/2026) : FRED → publier avec toutes les mentions exigées (usage personnel ; au pire, retour à une application locale) ; Yahoo et STOXX → publier avec mention ; FMI, BIS, Michigan, Banque du Japon → publier avec mention.
- Pas de redémarrage de Claude Code : les agents sont lancés avec modèle et effort choisis directement.
- JS : `js/outils.js` remplace les fichiers `format.js`, `dom.js`, `donnees.js` proposés par le plan.
- Voir PLAN.md §0 et §1 pour les autres décisions (Yahoo source unique, devises variante b, fichiers récents de 36 mois, etc.).

## Reste à faire
- Étape 7 : relecture finale et corrections ; étape 8 : remise à Georgy.

## Problèmes ouverts
- Aucun pour l'instant. (Point d'arrêt passé le 22/11/2026 : Georgy valide le design et le comparateur ; événement du 5 nov. 2026 ajouté.)
