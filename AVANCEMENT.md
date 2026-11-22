# Avancement du projet

Référence : SPEC_Tableau_de_bord_Marches.md, puis PLAN.md (plan de l'architecte, fait foi pour les choix techniques). Mettre ce fichier à jour à la fin de chaque étape.

## Étape en cours
Étape 2 — Collecte et cœur des calculs (lots 2a à 2d du PLAN §11).

## Fait
- Étape 0 : CLAUDE.md, AVANCEMENT.md, agents `.claude/agents/`, arborescence, git local (adresse « noreply »). Python 3.12, git, `gh` (connecté, droits `repo` + `workflow`), node 26 installés. Clé FRED dans `.env` (testée).
- Design : application Aedifica lue sans modification (dossier « Aedifica interface web » sur le Bureau ; dépôt `tableau-bord-actions`). Palette, cartes, boutons de période et style des graphiques repris dans `css/style.css`.
- Étape 1 : sources testées (`docs/sources/`, 10 fichiers) ; PLAN.md rédigé par l'architecte (Fable, xhigh).
- Déjà écrit : `js/stats.js` + tests node ; `scripts/commun.py`, `fusion.py`, `calculs.py`, `sources/fred.py`, `sources/sdmx.py` + tests pytest ; `css/style.css`, `js/outils.js` (regroupe format + dom + chargement), `index.html`, `config/evenements.yaml`, `lib/chart.umd.min.js` (4.5.0).

## Décisions
- Rediffusion (réponses de Georgy, 22/11/2026) : FRED → publier avec toutes les mentions exigées (usage personnel ; au pire, retour à une application locale) ; Yahoo et STOXX → publier avec mention ; FMI, BIS, Michigan, Banque du Japon → publier avec mention.
- Pas de redémarrage de Claude Code : les agents sont lancés avec modèle et effort choisis directement.
- JS : `js/outils.js` remplace les fichiers `format.js`, `dom.js`, `donnees.js` proposés par le plan.
- Voir PLAN.md §0 et §1 pour les autres décisions (Yahoo source unique, devises variante b, fichiers récents de 36 mois, etc.).

## Reste à faire
- Lot 2a-2c : config YAML, corrections §2 du plan, modules de sources, collect.py, resume.py, previsions.py, écriture, vérification, tests.
- Lot 2d : relecteur « revue des calculs ».
- Étape 3 : lot 1 en ligne + point d'arrêt Georgy. Puis étapes 4 à 8.

## Problèmes ouverts
- Événement du 5 nov. 2026 (krach des valeurs IA) : à proposer à Georgy au point d'arrêt.
- Avant le premier push : retirer de ce fichier tout chemin du PC.
