# Tableau de bord des marchés

Outil personnel pour **comprendre et anticiper** les grands mouvements des marchés : taux d'intérêt, inflation, énergie, croissance, dette, banques centrales, bourses, devises et risques géopolitiques. Ce n'est ni un outil de cotation en temps réel ni un outil de trading.

> Outil personnel d'information — pas un conseil en investissement.

- **Le site :** https://depgeor75-droid.github.io/tableau-marches/ (sur PC et sur GSM)
- **Hors ligne :** double-cliquez sur `index.html` dans le dossier du projet.

Les données sont **mises à jour automatiquement chaque matin** (vers 6 h 17 en hiver, 7 h 17 en été, heure belge) par un robot GitHub.

---

## 1. Lire l'état des données

- En haut à droite, une pastille : **vert** = tout est à jour ; **orange** = quelques séries en retard ; **rouge** = alerte.
- La page **Comprendre → État des données** (ou un clic sur la pastille) montre chaque série : statut, date de la dernière valeur, source.
  - *à jour* : tout va bien ;
  - *en retard* : la source n'a pas publié depuis longtemps (normal pour certaines, comme le FMI ou la dette trimestrielle) ;
  - *source en panne* : le téléchargement a échoué ; l'application garde et affiche les dernières bonnes valeurs ;
  - *source de secours* : une source de remplacement est utilisée ;
  - *non disponible* : aucune source gratuite et fiable n'existe (la raison est affichée).

**Une source en panne n'efface jamais de bonnes données.**

### E-mail d'échec de GitHub

Si une série **essentielle** est en panne trois matins de suite, ou en retard, le robot marque son exécution « en échec » et GitHub vous envoie un e-mail. Pour recevoir ces e-mails : sur github.com, photo de profil → **Settings** → **Notifications** → section **Actions** → cochez **Send notifications for failed workflows only**.

Que faire en cas d'e-mail ? Le plus souvent, rien : une source étrangère est temporairement indisponible et revient d'elle-même. Si le problème dure plus d'une semaine, ouvrez Claude Code dans le dossier du projet et écrivez : « Lis AVANCEMENT.md. Le robot de mise à jour échoue depuis plusieurs jours : diagnostique et corrige. »

## 2. Lancer une mise à jour manuelle

1. Dans l'application : **Comprendre → État des données → Mettre à jour maintenant** (la page GitHub du robot s'ouvre).
2. Cliquez sur **Run workflow** (à droite), puis sur le bouton vert **Run workflow**. Cela fonctionne aussi depuis l'application mobile GitHub.
3. Attendez 3 à 4 minutes, puis rechargez le site : la date « Données mises à jour le … » change.

### Mettre à jour la copie locale (usage hors ligne)

Double-cliquez sur **`mettre_a_jour_local.bat`** : il récupère les dernières données publiées par le robot. Ensuite, ouvrez `index.html`.

**Important :** une fois le robot en service, c'est **lui seul** qui enregistre les données. Ne lancez pas la collecte sur votre PC pour la publier : sinon, les deux versions se marchent dessus.

## 3. Utiliser l'application

- **Accueil :** 12 indicateurs clés, « Ce qui a bougé » cette semaine, jauges « conditions favorables à un QE ».
- **ⓘ** ouvre la fiche explicative de chaque indicateur (sigles expliqués, repères, pièges).
- **＋ Comparer** envoie un indicateur dans le **comparateur** : choisissez jusqu'à 6 indicateurs ; l'étoile ☆ désigne la référence.
  - Vert bleuté : les courbes bougent ensemble ; rouge orangé : en sens inverse ; gris : pas de lien fiable. L'épaisseur du trait indique la force du lien.
  - Le curseur de **décalage** teste si un indicateur en annonce un autre ; **Trouver le meilleur décalage** essaie tous les décalages.
  - Les boutons en haut appliquent des **comparaisons prêtes à l'emploi**.
- Pages thématiques : Taux, Inflation et anticipations, Croissance et dette, Banques centrales, Bourses, Énergie et ETF, Devises, Risques.

### Trois comparaisons à essayer

1. **VIX vs S&P 500** (bouton prêt à l'emploi) : la peur monte quand la bourse baisse.
2. **Pétrole → inflation zone euro**, puis **Trouver le meilleur décalage** sur le Brent : le pétrole annonce-t-il l'inflation ?
3. **Dette et taux : Italie vs Allemagne** : l'écart de taux suit-il la dette ?

### Demander une analyse à Claude

- Dans le comparateur : **Exporter cette comparaison** télécharge un fichier CSV et copie un résumé dans le presse-papiers. Collez le résumé dans une conversation avec Claude (et joignez le CSV), par exemple : « Voici une comparaison entre le Brent et l'inflation de la zone euro. Le lien te paraît-il solide ? Qu'est-ce qui pourrait l'expliquer ? »
- Toutes les données en mensuel : **État des données → Télécharger toutes les données (CSV)** (s'ouvre dans Excel ; séparateur « ; », virgule décimale).

## 4. Ce que vous pouvez régler vous-même (dossier `config/`)

Modifiez le fichier sur github.com (crayon ✏️ → **Commit changes**) : le site se met à jour en quelques minutes. Les modifications de données d'actions s'appliquent à la collecte suivante.

- **`config/indicateurs.yaml`**, famille K « Valeurs suivies » : ajoutez une action avec son code Yahoo Finance. Exemple, à ajouter sous la ligne d'Aedifica :
  ```yaml
  - {id: K2, nom: "UCB (action, Euronext Bruxelles)", nom_court: "UCB", famille: K, code: "UCB.BR"}
  ```
- **`config/evenements.yaml`** : les grands événements affichés sur les graphiques (option « Afficher les grands événements »). Ajoutez une ligne avec la date, un libellé court et un détail.
- **`config/reglages.yaml`** : tous les seuils (fraîcheur des données, seuils des jauges, fenêtres de corrélation…).
- **`config/comparaisons.yaml`** : les comparaisons prêtes à l'emploi du comparateur.

## 5. Sources et mentions légales

Chaque série cite sa source dans sa fiche, sous les graphiques et dans « État des données » : FRED® (Banque fédérale de réserve de Saint-Louis), BCE, Eurostat, Banque des règlements internationaux (BIS), OCDE, FMI, Banque d'Angleterre, Bundesbank, Ministère des Finances du Japon, ONS, Banques fédérales de réserve de New York et de Philadelphie, Réserve fédérale (prime de crédit), Caldara et Iacoviello (risque géopolitique), Yahoo Finance, STOXX.

This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis. Les utilisateurs sont tenus par les [conditions d'utilisation de l'API FRED](https://fred.stlouisfed.org/docs/api/terms_of_use.html).

Usage personnel et non commercial ; le site demande aux moteurs de recherche de ne pas l'indexer. Si un fournisseur de données le demande, les séries concernées peuvent être retirées (ou l'application gardée en local seulement).

## 6. Pour les curieux (fonctionnement technique)

- `scripts/collect.py` télécharge toutes les séries (une par source dans `scripts/sources/`), calcule glissements annuels, écarts, percentiles, jauges… et écrit `data/`. Commandes : `python scripts/collect.py` · `--serie B4` · `--verifier` · `--sortie cache/essai` (essai local sans toucher à `data/`).
- `config/indicateurs.yaml` est la source unique de vérité des séries ; `PLAN.md` décrit les choix techniques ; `AVANCEMENT.md` le journal du projet.
- Tests : `python -m pytest scripts/tests -q` et `node --test tests_js/`. Captures et contrôle de la console : `python scripts/captures.py`.
- Le robot (`.github/workflows/mise-a-jour.yml`) tourne chaque matin, enregistre les données s'il y a du nouveau et publie le site. Ces enregistrements quotidiens gardent le robot actif (GitHub suspend les tâches planifiées d'un dépôt sans activité pendant 60 jours).
- La clé FRED n'est jamais écrite dans le dépôt : elle est dans le fichier local `.env` et dans les secrets GitHub. `python scripts/verifier_cle.py` le vérifie avant chaque envoi.
