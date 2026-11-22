# SPEC — Tableau de bord des marchés (v1)

> **Destinataire :** Claude Code
> **Demandeur :** Georgy (Belgique) — enseignant en économie et comptabilité, investisseur particulier, **non développeur**
> **Date :** 22 novembre 2026 — révision 2
> **Langue de travail :** français (interface, fiches, messages à Georgy, README, messages de commit)

---

## 0. Pour Georgy — comment lancer (à lire en premier)

1. Crée un dossier vide nommé `tableau-marches` sur ton PC et place ce fichier dedans.
2. Ouvre Claude Code dans ce dossier. S'il propose une mise à jour, accepte-la : les modèles récents exigent une version récente.
3. Tape `/model opus`, puis `/effort high` : la session principale tourne sur **Opus**, en effort « high » (abonnement Max). Ne choisis pas Fable ici : les agents l'appellent eux-mêmes, trois fois, aux moments clés (voir §1).
   - Fable est inclus dans l'abonnement Max jusqu'à la moitié de ta limite hebdomadaire. Si Claude Code t'annonce en cours de route que Fable « requires usage credits », cette part est épuisée : refuse, et écris-lui « Remplace fable par opus dans les agents. »
   - Si tu atteins trop souvent tes limites, tape `/model sonnet` pour la suite : plus économe, et suffisant pour l'écriture du code.
4. Écris : **« Lis SPEC_Tableau_de_bord_Marches.md et exécute-le de bout en bout. »**
5. Garde 5 minutes pour créer ta **clé gratuite FRED** quand Claude Code te le demandera (il te guidera pas à pas).

**Ce qui va se passer ensuite**
- Claude Code te demandera parfois une **autorisation** (installer un outil, publier sur GitHub) : accepte si la demande correspond à ce document.
- Il te demandera **une fois de le redémarrer**, tout au début, puis s'arrêtera **une fois pour te montrer une première version en ligne** (étape 3) : ouvre le lien sur ton GSM et dis-lui ce que tu en penses avant qu'il construise le reste.
- **Si la session s'interrompt** (limite d'utilisation atteinte, PC en veille, fenêtre fermée) : relance Claude Code dans le même dossier et écris **« Lis SPEC_Tableau_de_bord_Marches.md et AVANCEMENT.md, puis continue. »** Rien n'est perdu : l'avancement est noté à chaque étape.

À la fin, l'application est construite, testée, en ligne sur GitHub et mise à jour automatiquement chaque jour.

---

## 1. Modèles et agents — répartition pour économiser les ressources

**Principe :** le modèle de la session principale consomme le plus (il garde toute la conversation). On met donc en session principale un modèle solide mais moins gourmand que Fable (Opus), et on réserve **Fable en effort « extra » (`xhigh`)** aux trois moments où une erreur coûterait le plus cher : **valider le plan**, **relire le cœur des calculs** et **relire le résultat final**.

| Rôle | Modèle | Effort | Quand |
|---|---|---|---|
| Session principale (pilote + écriture du code) | Opus 5.5 (`/model opus`) | `high` (`/effort high`) | Tout le projet (repli : `/model sonnet` si les limites sont atteintes trop souvent) |
| `chercheur-sources` | Sonnet 5.5 | `medium` | Étape 1 : tester les sources de données, une famille par appel, en parallèle |
| `architecte` | **Fable 5.2** | **`xhigh`** | Étape 1 : valider le plan (`PLAN.md`) — et en **escalade** si un problème résiste à 2 tentatives |
| `redacteur-fiches` | Sonnet 5.5 | `high` | Étape 4 : rédiger les fiches explicatives |
| `relecteur` | **Fable 5.2** | **`xhigh`** | Étape 2 : revue des calculs · Étape 7 : relecture finale contre ce cahier des charges |

- Les alias `sonnet`, `opus`, `haiku` et `fable` désignent la version la plus récente que connaît la version installée de Claude Code : les numéros ci-dessus sont indicatifs. Le modèle réellement utilisé par un agent se vérifie avec `/tasks`.
- **Si Fable n'est pas disponible** (abonnement, ou crédits refusés par Georgy) : remplacer `model: fable` par `model: opus` dans les deux agents, sans changer l'effort, et le noter dans `AVANCEMENT.md`.
- Pas d'agent pour vérifier les données : `collect.py --verifier` imprime lui-même un rapport court (§6), ce qui est plus fiable et ne coûte rien.

**Action n° 1 de Claude Code :** créer `CLAUDE.md` et `AVANCEMENT.md` (§11), puis ces 4 fichiers dans `.claude/agents/`. Un dossier `agents` créé en cours de session n'est pris en compte qu'après un redémarrage : demander à Georgy de fermer puis de relancer Claude Code, et d'écrire la phrase de reprise du §0.

`.claude/agents/chercheur-sources.md`
```markdown
---
name: chercheur-sources
description: Teste et documente les sources de données gratuites d'une famille d'indicateurs du tableau de bord (code de série, profondeur d'historique, fraîcheur, source de secours, conditions de réutilisation). Utiliser pour chaque famille à l'étape 1.
model: sonnet
effort: medium
---
Tu reçois une famille d'indicateurs du fichier SPEC_Tableau_de_bord_Marches.md (§5).
Pour CHAQUE indicateur : teste réellement le code de série indiqué (appel API ou téléchargement),
note la date de la première et de la dernière observation, la fréquence, l'unité.
Si le code échoue ou si la série n'est plus mise à jour (dernière valeur trop ancienne pour sa fréquence),
cherche une alternative gratuite et fiable, teste-la, et documente-la.
N'invente jamais un code ni une donnée. Si rien de fiable n'existe, écris « non disponible » avec la raison.
Note aussi, pour chaque source : l'appel exact qui a fonctionné (adresse et paramètres, SANS la clé API),
les particularités du format (valeurs manquantes, en-têtes, encodage, trous dans la série) et les conditions
de réutilisation quand elles restreignent la publication des données sur un site public.
Écris le résultat dans docs/sources/<famille>.md : un tableau Markdown
id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique (oui / restreinte / inconnue) | remarque
suivi des appels exacts. N'écris jamais la clé API dans un fichier.
Dans ta réponse, rends seulement un résumé de 10 lignes au plus : séries OK, séries remplacées,
séries introuvables, points d'attention.
```

`.claude/agents/architecte.md`
```markdown
---
name: architecte
description: Valide et complète le plan technique du tableau de bord (PLAN.md) à partir du cahier des charges et des sources vérifiées ; appelé aussi en escalade quand un problème technique résiste à deux tentatives.
model: fable
effort: xhigh
---
Tu es l'architecte du projet. Lis SPEC_Tableau_de_bord_Marches.md et les fichiers de docs/sources/.
Produis ou corrige PLAN.md : choix de source par indicateur (principale + secours + raccord),
formats des fichiers de données, répartition des calculs entre Python et JavaScript (§4),
découpage des fichiers JS, algorithmes (transformations, percentiles, corrélation, corrélation glissante,
décalage), workflow GitHub Actions, découpage en lots (§11), risques et parades,
séries dont la rediffusion publique est restreinte ou douteuse.
Sois précis et concret : le plan sera exécuté par un autre modèle. Signale toute exigence du cahier
des charges impossible à tenir et propose la meilleure alternative.
Termine PLAN.md par « Questions pour Georgy » : 3 questions au plus, seulement celles dont la réponse
change le plan.
En escalade : diagnostique la cause racine et propose un correctif précis, sans réécrire tout le projet.
```

`.claude/agents/redacteur-fiches.md`
```markdown
---
name: redacteur-fiches
description: Rédige en français les fiches explicatives pédagogiques des indicateurs du tableau de bord, selon le modèle du §7 du cahier des charges.
model: sonnet
effort: high
---
Tu rédiges les fiches du §7 de SPEC_Tableau_de_bord_Marches.md pour la liste d'indicateurs reçue.
Public : adulte cultivé, non spécialiste. Français impeccable avec accents. Chaque sigle est expliqué
à sa première apparition. Phrases courtes, exemples concrets. Respecte strictement la structure et la
longueur du modèle (fiche VIX). Les repères chiffrés historiques doivent être vérifiés dans les données
collectées (data/) ou dans une source officielle ; si un repère n'est pas vérifiable, utilise les
percentiles historiques plutôt qu'un chiffre de mémoire.
Si une série a une particularité (mois manquant, historique court, source de secours, cours hors
dividendes), dis-le dans la fiche. À la fin de ta réponse, liste à part les affirmations dont tu n'es
pas certain, au lieu de les écrire dans les fiches : le relecteur les tranchera.
```

`.claude/agents/relecteur.md`
```markdown
---
name: relecteur
description: Relecture indépendante du projet contre le cahier des charges. Deux usages — « revue des calculs » après l'étape 2, « relecture finale » (checklist §12) une fois l'application terminée et en ligne.
model: fable
effort: xhigh
disallowedTools: Write, Edit
---
Tu n'as pas participé à la construction. Tu ne modifies aucun fichier : tu rends un rapport.

Revue des calculs : relis scripts/ (transformations, fusion, raccords, validation, résumé) et
js/stats.js contre les §6, §9 et §12 de SPEC_Tableau_de_bord_Marches.md. Lance les tests.
Recalcule à la main, à partir de data/, au moins : un glissement annuel, un écart, un percentile,
une corrélation en mode « Mouvements », un meilleur décalage. Cherche surtout les erreurs de sens :
signe du décalage, alignement des dates, trous dans les séries, valeurs nulles ou négatives.

Relecture finale : vérifie le projet contre la checklist du §12, point par point. Lance les tests,
ouvre les captures d'écran, contrôle quelques calculs à la main, relis TOUTES les fiches
(exactitude économique, accents, sigles expliqués), cherche la clé API dans le dépôt, dans data/
et dans l'historique git.

Ne signale QUE les écarts qui affectent l'exactitude, les exigences du cahier des charges ou
l'utilisabilité. Pas de préférences de style. Classe par gravité, avec le fichier et la ligne.
```

---

## 2. Contexte et objectif

Georgy veut un **outil personnel** pour **comprendre et anticiper** les grands mouvements des marchés : taux d'intérêt, inflation, énergie, croissance, dette, politique des banques centrales, bourses, devises, risques géopolitiques. Ce n'est **pas** un outil de cotation en temps réel ni de trading.

Ce qu'il doit pouvoir faire :
1. **Voir l'état actuel** de chaque indicateur et son historique (jusqu'à **30 ans** quand il existe).
2. **Comprendre** chaque indicateur grâce à une **fiche explicative claire**.
3. **Comparer** n'importe quels indicateurs sur un même graphique et **voir s'ils sont corrélés** (couleurs, épaisseur des traits, chiffre), y compris **avec un décalage dans le temps** (ex. : le pétrole annonce-t-il l'inflation 3 mois plus tard ?).
4. **Anticiper** : indicateurs avancés, anticipations des marchés, probabilités publiées (inflation, récession, taux).
5. Consulter l'application **sur PC et sur GSM**, **mise à jour automatiquement chaque jour**, avec possibilité de **mise à jour manuelle**.
6. **Exporter** les données (CSV) pour les faire analyser par Claude.

**Design :** Georgy a déjà une application Aedifica réalisée par Claude Code sur le **même compte GitHub**, dont il apprécie beaucoup le design. → Retrouve-la (`gh repo list --limit 100`, cherche « aedifica » sans tenir compte de la casse), **lis-la sans la modifier**, et **réutilise son identité visuelle** (palette, typographie, cartes, boutons de période, style des graphiques). Si tu ne la trouves pas, demande l'adresse à Georgy.

---

## 3. Règles absolues

1. **Aucune donnée inventée, simulée ou « d'exemple ».** Si une série n'est pas disponible, l'application affiche « non disponible » avec la raison. Jamais de chiffres de mémoire. **Un trou reste un trou** : pas d'interpolation ni de report silencieux d'une valeur manquante.
2. **Uniquement des sources gratuites.** Une seule clé obligatoire : **FRED** (gratuite). Toute autre clé (ex. EIA) est facultative et doit être demandée à Georgy.
3. **Aucune clé API dans le code ni dans le dépôt** (dépôt public). Clés en local dans `.env` (ignoré par git) et dans les **secrets GitHub**. Vérifier avant chaque `git push` (`git grep` sur la clé). Attention aux fuites indirectes : l'adresse d'un appel FRED contient la clé, donc **tout message d'erreur ou journal doit être nettoyé** avant d'être écrit dans `data/etat.js`, dans `docs/` ou dans la sortie du workflow.
4. **Interface 100 % en français**, accents corrects partout (é, è, ê, à, ù, ç, î, ô…), nombres au format belge (virgule décimale, espace pour les milliers : `1 234,56`), dates en français (`22 nov. 2026`), heures affichées en **heure belge** (`Europe/Brussels`) alors que GitHub travaille en UTC. S'appuyer sur `Intl.NumberFormat` et `Intl.DateTimeFormat` (`fr-BE`) plutôt que sur un formatage maison.
5. **Chaque sigle est expliqué** à sa première apparition (dans les fiches et les infobulles).
6. **L'application fonctionne hors ligne** en double-cliquant sur `index.html` (protocole `file://`) **et** en ligne sur GitHub Pages. Donc : pas de `fetch()` de fichiers locaux, pas de CDN au moment de l'exécution, bibliothèques copiées dans `lib/`.
7. **Une source qui tombe en panne ne doit jamais effacer de bonnes données** : on garde les dernières valeurs valides et on signale le retard.
8. **Ne pas toucher au dépôt Aedifica.**
9. Mention discrète en pied de page : « Outil personnel d'information — pas un conseil en investissement. »
10. **Le site est public : respecter les conditions de réutilisation des sources.** Ne pas publier une série dont le fournisseur interdit la rediffusion (cas vérifié : les indices ICE BofA diffusés par FRED, voir J6-J7). Citer la source de chaque série, ajouter les mentions exigées par les fournisseurs (ex. celle de l'API FRED, à vérifier sur leur site) et demander aux moteurs de recherche de ne pas indexer le site (`<meta name="robots" content="noindex">` + `robots.txt`). Les séries à rediffusion restreinte ou douteuse repérées à l'étape 1 sont listées dans `PLAN.md` ; Georgy tranche.
11. **Aucune donnée personnelle de Georgy dans le dépôt public** (nom complet, adresse e-mail, chemins de son PC). Vérifier que git signe les commits avec l'adresse « noreply » de GitHub ; sinon le lui proposer.

---

## 4. Architecture

```
tableau-marches/
├── index.html                  ← l'application (une seule page, navigation par onglets)
├── robots.txt                  ← demande de non-indexation (§3 règle 10)
├── css/style.css
├── js/
│   ├── app.js                  ← navigation, chargement des données, pages
│   ├── graphiques.js           ← graphiques (Chart.js)
│   ├── stats.js                ← fonctions de calcul PURES du comparateur (testables avec node)
│   ├── comparateur.js
│   └── fiches.js               ← contenu des fiches explicatives (statique)
├── lib/                        ← Chart.js 4 + adaptateur de dates, copiés localement
├── data/                       ← GÉNÉRÉ par le script, ne pas éditer à la main
│   ├── catalogue.js            ← liste des indicateurs + métadonnées
│   ├── etat.js                 ← date de mise à jour et statut de chaque série
│   ├── resume.js               ← tout ce qui est précalculé pour l'Accueil et les cartes (voir « Qui calcule quoi »)
│   ├── previsions.js           ← jeux particuliers : distributions SPF, prévisions FMI, courbe à terme
│   ├── <famille>_historique.js ← mensuel, depuis 1990, mois complets uniquement
│   ├── <famille>_recent.js     ← quotidien (ou natif), 24 derniers mois glissants
│   └── donnees_mensuelles.csv  ← export complet pour analyse (bouton « Télécharger »)
├── config/
│   ├── indicateurs.yaml        ← SOURCE UNIQUE DE VÉRITÉ : toutes les séries (voir §5-6)
│   ├── evenements.yaml         ← grands événements annotables sur les graphiques
│   └── saisie_manuelle.yaml    ← valeurs non automatisables (si nécessaire), documentées
├── scripts/
│   ├── collect.py              ← collecte + calculs + écriture de data/
│   ├── sources/                ← un module par source (fred.py, bce.py, eurostat.py, yahoo.py…)
│   ├── tests/                  ← pytest
│   └── requirements.txt
├── tests_js/                   ← tests node pour js/stats.js
├── docs/
│   ├── sources/                ← résultat de l'étape 1, un fichier par famille
│   └── captures/               ← captures PC et GSM de chaque page
├── .github/workflows/mise-a-jour.yml
├── PLAN.md
├── AVANCEMENT.md               ← journal d'avancement, mis à jour à chaque étape (§11)
├── CLAUDE.md                   ← règles courtes pour les futures sessions Claude Code
├── README.md                   ← en français, pour Georgy
├── .env.example
├── .gitattributes              ← `* text=auto eol=lf` (mêmes fins de ligne sous Windows et sur GitHub)
└── .gitignore                  ← .env, cache/, __pycache__/
```

**Format des fichiers de données** (chargés via des balises `<script>` injectées à la demande, ce qui fonctionne en `file://`) :
```js
window.DONNEES = window.DONNEES || {};
window.DONNEES["taux_recent"] = {
  "B1": { "dates": ["2024-11-22", ...], "valeurs": [4.41, ...] },
  ...
};
```
- Une paire de fichiers **par famille** (historique + récent) → seuls les petits fichiers modifiés sont enregistrés chaque jour, l'historique Git reste léger.
- Les valeurs mensuelles « historique » = **valeur de fin de mois** pour les séries de marché ; valeur publiée pour les séries officielles mensuelles/trimestrielles/annuelles.
- Chargement initial minimal : `catalogue.js`, `etat.js` et les données de l'Accueil ; le reste au clic. Objectif : Accueil affiché en moins de 2 s sur GSM en 4G.

**Qui calcule quoi** (une même formule n'existe qu'à un seul endroit) :
- **Python** calcule tout ce qui ne dépend pas d'un choix de l'utilisateur : transformations, variations sur 1 mois et 1 an, percentiles, mini-courbes, « ce qui a bougé », jauges, signaux d'inflation, statut QE/QT, probabilité de récession (règles au §6.1). Le résultat va dans `data/resume.js`, petit fichier chargé au démarrage : l'Accueil s'affiche sans charger les historiques.
- **JavaScript** (`js/stats.js`) calcule seulement ce qui dépend de la sélection dans le comparateur : base 100, corrélations, corrélation glissante, décalage.

**Écriture déterministe :** clés triées, arrondi fixe par série (4 chiffres après la virgule par défaut, réglable dans la config), UTF-8, fins de ligne LF. Relancer la collecte sans donnée nouvelle ne doit modifier aucun fichier de `data/` à part `etat.js` ; sinon l'historique Git gonfle et chaque mise à jour semble tout changer.

**Mois en cours et semaines :** les vues mensuelles ajoutent en dernier point la dernière valeur connue du mois en cours, marquée « provisoire », pour que le graphique et la carte affichent la même dernière valeur. Une valeur hebdomadaire est la dernière valeur de la semaine.

---

## 5. Catalogue des indicateurs

**Légende — Type :** `T` = taux ou pourcentage (axe en %, jamais converti en base 100) ; `N` = niveau ou prix (base 100 possible) ; `N*` = indice centré (zéro ou 100 = normal), affiché en valeur brute sur son propre axe, jamais en base 100.
**Priorité :** `E` = essentielle (une panne déclenche une alerte) ; `S` = secondaire.
**Codes :** les codes sont **indicatifs** → chacun doit être **testé** à l'étape 1. S'il échoue ou n'est plus mis à jour, trouver l'équivalent gratuit et le documenter.
**Profondeur :** collecter depuis le **1er janvier 1990** quand c'est possible (permet « 30 ans » et « Max »).
**Raccord de sources :** si une source donne l'historique et une autre les jours récents (ex. FRED + Yahoo), raccorder à la dernière date commune, vérifier l'écart au point de raccord (type N : < 2 % ; types T et N* : < 0,10 point ; sinon signaler), et indiquer les deux sources dans `etat.js`. Les jours récents venant de la source rapide sont **provisoires** : ils sont remplacés par la source principale dès qu'elle les publie. Ne jamais raccorder deux séries de nature ou de devise différentes (ex. `IWDA.AS` en euros et `URTH` en dollars) : dans ce cas le secours **remplace** la série entière, il ne la prolonge pas.
**Lignes regroupées :** une ligne qui couvre plusieurs pays ou variantes (E1, E3, B5, C8–C10, D13, H8…) donne **une série par pays ou variante**, avec un identifiant suffixé (`E1_US`, `E1_ZE`, `B5_2A`, `B5_10A`…).
**Jeux particuliers :** les distributions de probabilité (D5, D6), les prévisions du FMI (D7, E2) et la courbe à terme (D15) ne sont pas des séries temporelles simples : format dédié dans `data/previsions.js`, non sélectionnables dans le comparateur.
**Cours Yahoo :** clôture **non ajustée des dividendes** (`auto_adjust=False`, colonne `Close`), pour rester comparable aux indices boursiers, qui sont des indices de prix ; le dire dans les fiches des ETF (« hors dividendes »).
**Cas limites à prévoir dès le départ :**
- prix nul ou négatif (le WTI a clôturé sous zéro le 20 avril 2020) → valeur conservée, mais ni variation en % ni base 100 pour ce point ;
- mois non publié : l'IPC américain d'octobre 2025 n'a pas été publié (fermeture des services fédéraux), et le BLS ne publie donc pas non plus de glissement annuel pour octobre 2026. Pour C1-C2, ces deux points sont manquants, ce qui est expliqué dans la carte et dans la fiche. Le confirmer dans les données à l'étape 1 et vérifier si d'autres séries américaines ont le même trou.

### A — Taux directeurs (court terme)
| ID | Indicateur | Type | Source principale (code indicatif) | Secours | Prio |
|---|---|---|---|---|---|
| A1 | Taux directeur de la Fed (taux effectif des fonds fédéraux) | T | FRED `DFF` | FRED `FEDFUNDS` | E |
| A2 | Taux de dépôt de la BCE | T | FRED `ECBDFR` | BCE `FM.B.U2.EUR.4F.KR.DFR.LEV` | E |
| A3 | Euribor 3 mois (historique zone euro avant 1999) | T | FRED `IR3TIB01EZM156N` | BCE (jeu FM) | S |
| A4 | Taux directeur de la Banque d'Angleterre (Bank Rate) | T | Banque d'Angleterre (base IADB) `IUDBEDR` | FRED | E |
| A5 | Taux directeur de la Banque du Japon (taux au jour le jour) | T | FRED `IRSTCI01JPM156N` | Banque du Japon | E |
| A6 | Taux de référence chinois (LPR 1 an ; avant 2019 : taux de prêt à 1 an) | T | à rechercher (PBoC, FMI, FRED) | — | E |
| A7 | Taux directeur de la Banque nationale suisse | T | data.snb.ch | FRED `IR3TIB01CHM156N` | S |

### B — Taux longs (obligations d'État)
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| B1 | États-Unis 10 ans | T | FRED `DGS10` | — | E |
| B2 | États-Unis 2 ans | T | FRED `DGS2` | — | E |
| B3 | États-Unis 3 mois | T | FRED `DGS3MO` | — | S |
| B4 | Allemagne 10 ans (Bund) | T | Bundesbank, API statistique (quotidien) | FRED `IRLTLT01DEM156N` (mensuel, historique) | E |
| B5 | Zone euro 2 ans et 10 ans (courbe des États notés AAA, BCE) | T | BCE `YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y` / `SR_10Y` | — | E |
| B6 | Belgique 10 ans (OLO) | T | FRED `IRLTLT01BEM156N` | Eurostat `irt_lt_mcby_m` ; BNB | E |
| B7 | France 10 ans (OAT) | T | FRED `IRLTLT01FRM156N` | Eurostat | S |
| B8 | Italie 10 ans (BTP) | T | FRED `IRLTLT01ITM156N` | Eurostat | E |
| B9 | Royaume-Uni 10 ans (Gilt) | T | Banque d'Angleterre IADB (quotidien, à rechercher) | FRED `IRLTLT01GBM156N` | E |
| B10 | Japon 10 ans (JGB) | T | Ministère des Finances japonais (CSV quotidien) | FRED `IRLTLT01JPM156N` | E |
| B11 | Chine 10 ans | T | à rechercher (gratuit et fiable uniquement) | — | E |
| B12 | Suisse 10 ans | T | FRED `IRLTLT01CHM156N` | BNS | S |

**Calculés :** écart US 10 ans − 2 ans (ou FRED `T10Y2Y`) ; écart US 10 ans − 3 mois (FRED `T10Y3M`) ; écarts Italie − Allemagne, France − Allemagne, Belgique − Allemagne (en points de %).

### C — Inflation (glissement annuel en %)
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| C1 | États-Unis — IPC (indice des prix à la consommation) | T | FRED `CPIAUCSL` → glissement annuel | — | E |
| C2 | États-Unis — IPC hors énergie et alimentation (« sous-jacente ») | T | FRED `CPILFESL` → glissement annuel | — | S |
| C3 | États-Unis — PCE (indice des dépenses de consommation, mesure visée par la Fed) | T | FRED `PCEPI` → glissement annuel | — | E |
| C4 | États-Unis — PCE sous-jacent | T | FRED `PCEPILFE` → glissement annuel | — | S |
| C5 | Zone euro — IPCH (indice des prix harmonisé) | T | BCE `ICP.M.U2.N.000000.4.ANR` | Eurostat | E |
| C6 | Zone euro — IPCH sous-jacent | T | BCE `ICP.M.U2.N.XEF000.4.ANR` | Eurostat | E |
| C7 | Belgique — IPCH | T | BCE `ICP.M.BE.N.000000.4.ANR` | Eurostat | E |
| C8–C10 | Allemagne, France, Italie — IPCH | T | BCE `ICP.M.DE/FR/IT.N.000000.4.ANR` | Eurostat | S |
| C11 | Royaume-Uni — IPC | T | ONS (série `D7G7`) | FRED (OCDE) → glissement annuel | E |
| C12 | Japon — IPC | T | FRED (OCDE) ou Bureau des statistiques du Japon | — | E |
| C13 | Chine — IPC | T | FRED (OCDE) ou Bureau national des statistiques (NBS) | FMI | E |

### D — Anticipations et signaux avancés
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| D1 | États-Unis — inflation anticipée à 5 ans par les marchés (« point mort d'inflation ») | T | FRED `T5YIE` | — | E |
| D2 | États-Unis — inflation anticipée à 10 ans | T | FRED `T10YIE` | — | S |
| D3 | États-Unis — inflation anticipée « 5 ans dans 5 ans » | T | FRED `T5YIFR` | — | S |
| D4 | États-Unis — inflation attendue par les ménages (Université du Michigan) | T | FRED `MICH` | — | S |
| D5 | Zone euro — **distribution de probabilité** de l'inflation (Enquête de la BCE auprès des prévisionnistes professionnels, « SPF »), pour l'année en cours, N+1, N+2 et le long terme | T | Portail de données BCE (jeu `SPF`) | Fichiers publiés sur le site BCE ; à défaut `config/saisie_manuelle.yaml` (trimestriel) | E |
| D6 | États-Unis — distribution de probabilité (SPF de la Fed de Philadelphie) | T | Fichiers de la Fed de Philadelphie | — | S |
| D7 | Prévisions d'inflation du FMI (Fonds monétaire international, « Perspectives de l'économie mondiale ») — tous les pays du tableau | T | API FMI DataMapper `PCPIPCH` | — | E |
| D8 | États-Unis — prix à la production (glissement annuel) | T | FRED `PPIACO` (ou `PPIFIS`) | — | S |
| D9 | Zone euro — prix à la production industrielle (glissement annuel) | T | Eurostat `sts_inppd_m` | BCE | S |
| D10 | Indice des tensions sur les chaînes d'approvisionnement mondiales (Fed de New York, « GSCPI ») | N* | Fichier de la Fed de New York | — | E |
| D11 | États-Unis — salaire horaire moyen (glissement annuel) | T | FRED `CES0500000003` | — | S |
| D12 | Zone euro — salaires négociés (glissement annuel) | T | BCE (indicateur des salaires négociés) | — | S |
| D13 | Indicateurs avancés de l'OCDE (CLI) — US, zone euro, Chine, Japon, R.-U. | N* | API OCDE (Data Explorer) | FRED | S |
| D14 | **Probabilité de récession aux États-Unis dans 12 mois** (modèle de la Fed de New York fondé sur l'écart 10 ans − 3 mois) | T | Fichier de la Fed de New York | Calcul : P = Φ(−0,5333 − 0,6330 × écart), Φ = loi normale — **formule à vérifier sur le site de la Fed de NY** | E |
| D15 | Courbe à terme du pétrole (prix attendu dans 6 et 12 mois) | N | Yahoo, contrats mensuels Brent/WTI | Prévision EIA « STEO » (clé gratuite EIA, demander à Georgy) ; sinon « non disponible » | S |

`N*` = indice centré (zéro ou 100 = normal) : afficher en valeur brute sur son propre axe, pas en base 100.

**Calculés :** anticipation des taux de la Fed = US 2 ans − taux Fed (négatif → le marché anticipe des baisses) ; anticipation des taux BCE = zone euro AAA 2 ans − taux de dépôt BCE.

### E — Croissance et dette
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| E1 | Croissance du PIB réel (produit intérieur brut, glissement annuel, trimestriel) — US, zone euro, Chine, Japon, R.-U. | T | US : FRED `GDPC1` ; zone euro : Eurostat `namq_10_gdp` ; Japon, R.-U., Chine : FRED/OCDE ou instituts nationaux (à rechercher) | FMI | E |
| E2 | Prévisions de croissance du FMI (année en cours, N+1, N+2) — mêmes pays + Allemagne, France, Italie, Belgique | T | API FMI DataMapper `NGDP_RPCH` | — | E |
| E3 | Dette publique en % du PIB — US, zone euro, Allemagne, France, Italie, Belgique, Japon, Chine, R.-U. | T | **Comparaison entre pays : FMI `GGXWDG_NGDP` (même définition pour tous, annuel + prévisions)** ; détail trimestriel : Eurostat `gov_10q_ggdebt` (UE), FRED `GFDEGDQ188S` (US, dette fédérale) | — | E |
| E4 | Dette publique en montant (milliards en devise nationale + équivalent en euros) | N | Eurostat (UE), FRED `GFDEBTN` (US), autres : % du PIB × PIB nominal FMI | — | S |
| E5 | Solde budgétaire (déficit) en % du PIB — mêmes pays | T | FMI `GGXCNL_NGDP` | — | E |

### F — Banques centrales (QE / QT) et masse monétaire
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| F1 | Bilan de la Fed (total de l'actif) | N | FRED `WALCL` | — | E |
| F2 | Bilan de la BCE | N | FRED `ECBASSETSW` | BCE | E |
| F3 | Bilan de la Banque du Japon | N | FRED `JPNASSETS` | — | E |
| F4 | Bilan de la Banque d'Angleterre | N | Banque d'Angleterre (à rechercher) | — | S |
| F5 | Bilans en % du PIB (calculés, pour comparer les 4 banques) | T | calcul | — | E |
| F6 | États-Unis — masse monétaire M2 (niveau + croissance annuelle) | N/T | FRED `M2SL` | — | S |
| F7 | Zone euro — masse monétaire M3 (croissance annuelle) | T | BCE (jeu `BSI`, M3, taux de croissance annuel) | — | S |

**Calculé :** statut de chaque banque centrale d'après la variation du bilan sur 3 mois : « QE en cours » (hausse > 1 %), « QT en cours » (baisse > 1 %), « stable ». Seuils dans la config. Pour F5, PIB nominal = somme des 4 derniers trimestres, dans la devise du bilan (sources à identifier à l'étape 1).

### G — Indices boursiers (Yahoo Finance via `yfinance` ; secours Stooq)
| ID | Indice | Code Yahoo | Prio |
|---|---|---|---|
| G1 | BEL 20 (Bruxelles) | `^BFX` | E |
| G2 | S&P 500 (États-Unis) | `^GSPC` | E |
| G3 | Dow Jones | `^DJI` | S |
| G4 | Nasdaq Composite | `^IXIC` | E |
| G5 | Euro Stoxx 50 | `^STOXX50E` | E |
| G6 | DAX (Allemagne) | `^GDAXI` | S |
| G7 | CAC 40 (France) | `^FCHI` | S |
| G8 | FTSE 100 (Londres) | `^FTSE` | S |
| G9 | Nikkei 225 (Japon) | `^N225` | E |
| G10 | Shanghai Composite | `000001.SS` | E |
| G11 | CSI 300 (Chine) | `000300.SS` | S |
| G12 | Hang Seng (Hong Kong) | `^HSI` | E |
| G13 | MSCI World (via l'ETF iShares Core MSCI World) | `IWDA.AS` (secours `URTH`) | E |

Tous de type `N`. Si l'historique Yahoo est court (ex. Euro Stoxx 50), compléter avec Stooq.

**Risque connu :** Yahoo limite régulièrement les requêtes automatisées (erreur 429). Regrouper tous les codes en un seul appel, utiliser une version récente de `yfinance`, espacer les nouveaux essais, vérifier que Stooq reste accessible sans clé — et tester la collecte **depuis GitHub Actions** dès l'étape 3 (§11) : un serveur n'est pas toujours traité comme un PC personnel.

### H — Énergie, matières premières, valeurs refuges et ETF
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| H1 | Pétrole Brent | N | FRED `DCOILBRENTEU` (historique) + Yahoo `BZ=F` (jours récents) | Banque mondiale (« Pink Sheet », mensuel depuis 1960) | E |
| H2 | Pétrole WTI | N | FRED `DCOILWTICO` + Yahoo `CL=F` | Banque mondiale | S |
| H3 | Or | N | Yahoo `GC=F` | Banque mondiale (mensuel) | E |
| H4 | Gaz naturel Europe (TTF) | N | Yahoo `TTF=F` | Banque mondiale « Natural gas, Europe » | E |
| H5 | Gaz naturel États-Unis (Henry Hub) | N | Yahoo `NG=F` | Banque mondiale | S |
| H6 | Cuivre (thermomètre de l'activité industrielle) | N | Yahoo `HG=F` | Banque mondiale | S |
| H7 | ETF matières premières diversifiées | N | `DBC` | `GSG` | E |
| H8 | ETF pétrole | N | `USO` (+ `BNO` pour le Brent) | — | S |
| H9 | ETF or | N | `GLD` | — | S |
| H10 | ETF immobilier coté américain | N | `VNQ` | — | E |
| H11 | ETF immobilier coté européen | N | iShares European Property Yield (code à vérifier, ex. `IPRP.AS`) | autre ETF immobilier européen liquide | E |
| H12 | ETF obligations d'État US longues (20 ans et +) | N | `TLT` | — | E |
| H13 | ETF obligations d'État US 7-10 ans | N | `IEF` | — | S |
| H14 | ETF obligations d'État zone euro | N | iShares Core Euro Government Bond (code à vérifier, ex. `IEGA.AS`) | autre ETF équivalent | E |
| H15 | ETF obligations indexées sur l'inflation (US) | N | `TIP` | — | S |

### I — Devises
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| I1 | Euro / dollar (EUR/USD) — depuis 1999 | N | BCE `EXR.D.USD.EUR.SP00.A` (publié chaque jour) | FRED `DEXUSEU` | E |
| I2 | Dollar / yen (USD/JPY) | N | FRED `DEXJPUS` (historique) + BCE (jours récents, calcul croisé) | — | E |
| I3 | Dollar / yuan (USD/CNY) | N | FRED `DEXCHUS` + BCE | — | E |
| I4 | Livre sterling / dollar (GBP/USD) | N | FRED `DEXUSUK` + BCE | — | E |
| I5 | Dollar / franc suisse (USD/CHF) | N | FRED `DEXSZUS` + BCE | — | S |
| I6 | Indice du dollar (DXY) | N | Yahoo `DX-Y.NYB` | FRED `DTWEXBGS` | E |

**Attention :** les taux de change quotidiens de FRED sont publiés **une fois par semaine** → utiliser la BCE pour les jours récents. Variante plus stable, à trancher par l'architecte : BCE pour toute la période depuis 1999 (taux croisés via l'euro) et FRED seulement avant 1999, avec un raccord à date fixe.
**Calculés (vue depuis la Belgique) :** EUR/GBP, EUR/CHF, EUR/JPY, EUR/CNY.

### J — Risques, stress et géopolitique
| ID | Indicateur | Type | Source principale | Secours | Prio |
|---|---|---|---|---|---|
| J1 | VIX — « indice de la peur » américain | N* | FRED `VIXCLS` + Yahoo `^VIX` | — | E |
| J2 | VSTOXX — « indice de la peur » européen | N* | Yahoo `^V2TX` | site STOXX | E |
| J3 | Indice de risque géopolitique (GPR, Caldara et Iacoviello), mensuel et quotidien | N* | Fichiers sur matteoiacoviello.com (page GPR) | — | E |
| J4 | Indice de stress financier de la Fed de Saint-Louis (0 = normal) | N* | FRED `STLFSI4` | — | E |
| J5 | Indicateur composite de stress systémique de la BCE (CISS) | N* | BCE `CISS.D.U2.Z0Z.4F.EC.SS_CIN.IDX` | — | E |
| J6 | Tension sur le crédit des entreprises, États-Unis | T ou N* | **À rechercher.** Ne pas utiliser FRED `BAMLH0A0HYM2` (écart « haut rendement » ICE BofA) : 3 ans d'historique seulement depuis avril 2026, et rediffusion interdite par ICE. Pistes à tester : sous-indice « crédit » de l'indice des conditions financières de la Fed de Chicago (FRED `NFCICREDIT`) ; prime obligataire excédentaire (« EBP ») publiée par la Fed | sinon « non disponible » | S |
| J7 | Tension sur le crédit des entreprises, zone euro | T ou N* | **À rechercher.** Même restriction pour FRED `BAMLHE00EHYIOAS`. Piste : sous-indices du CISS sur le portail de données de la BCE | sinon « non disponible » | S |

### K — Valeurs suivies (liste modifiable)
Famille courte, définie dans `config/indicateurs.yaml`, pour tester des corrélations avec des actions : par défaut **Aedifica `AED.BR`**. Georgy pourra ajouter d'autres codes Yahoo. Type `N`, priorité `S`.

---

## 6. Collecte des données — `scripts/collect.py`

- **Python 3.11+**, dépendances dans `requirements.txt` (ex. `requests`, `pandas`, `yfinance`, `pyyaml`, `openpyxl`, `xlrd`). Pas de bibliothèque payante.
- **Pilotée par `config/indicateurs.yaml`**. Chaque entrée : `id`, `nom`, `nom_court`, `famille`, `type` (T/N/N*), `unite`, `pays`, `source`, `code`, `secours`, `frequence`, `transformation` (aucune / glissement_annuel / ecart / croise / pourcentage_pib / formule), `priorite`, `debut` (1990-01-01), `decimales`, `retard_max_jours` (facultatif), `fiche`.
- **Un module par source** dans `scripts/sources/` (FRED, BCE, Eurostat, FMI, Banque mondiale, Banque d'Angleterre, Bundesbank, Ministère des Finances japonais, Yahoo, Stooq, fichiers téléchargeables, saisie manuelle).
- **À chaque exécution, tout est retéléchargé** (le volume est petit), puis **fusionné** avec les données existantes :
  - série téléchargée avec succès → elle **remplace** l'ancienne (les révisions officielles sont ainsi prises en compte) ;
  - série en échec → elle garde ses anciennes valeurs ;
  - **garde-fou contre les réponses tronquées :** si la nouvelle série commence nettement plus tard que l'ancienne ou perd plus de 5 % de ses points, on garde l'ancienne et on signale l'anomalie.
- **Robustesse :** délai maximal par requête, 3 essais espacés, gestion d'erreur **série par série** (une panne ne bloque jamais les autres).
- **Portabilité** (Windows chez Georgy, Linux sur GitHub) : `encoding="utf-8"` explicite à chaque lecture et écriture de fichier, `ensure_ascii=False` pour le JSON, chemins construits avec `pathlib`, CSV en `utf-8-sig` (accents corrects dans Excel). Sans cela, les accents des fichiers générés sous Windows sont abîmés.
- **Validation** (`--verifier`) : dates triées et uniques, pas de valeurs aberrantes (saut anormal → signalé, pas supprimé), contrôle des raccords de sources, fraîcheur selon la fréquence. Une série est « en retard » quand sa dernière observation date de plus de : 5 jours ouvrables (quotidienne) ; 14 jours (hebdomadaire) ; 75 jours après la fin du mois observé (mensuelle) ; 4 mois après la fin du trimestre observé (trimestrielle) ; 15 mois après la fin de l'année observée (annuelle). Seuils dans la config, avec exception possible par série (`retard_max_jours`) pour les sources connues pour leur lenteur. La commande imprime un **rapport court** (30 lignes au plus : nombre de séries par statut, puis anomalies avec leur gravité) et sort avec un code d'erreur si une série essentielle est en erreur.
- **`data/etat.js`** : pour chaque série → dernière valeur, date, source utilisée (principale/secours), statut (`ok` / `en_retard` / `erreur` / `secours` / `non_disponible`), nombre d'échecs consécutifs, message en français (sans clé ni adresse d'appel complète, voir §3 règle 3).
- **Calculs** après téléchargement : glissements annuels, écarts, taux croisés, % du PIB, statut QE/QT, probabilité de récession si calculée, puis tout le contenu de `data/resume.js` (§6.1).
- **Export** `data/donnees_mensuelles.csv` : toutes les séries alignées en mensuel (une colonne par indicateur, séparateur `;`, virgule décimale, en-têtes en français) → ouvrable dans Excel et prêt pour une analyse par Claude.
- **Modes :** `python scripts/collect.py` (normal) · `--serie B4` (une seule série) · `--verifier` (contrôle sans téléchargement).
- Clés lues dans les variables d'environnement (`FRED_API_KEY`, éventuellement `EIA_API_KEY`), chargées depuis `.env` en local.

### 6.1 Règles de calcul communes (côté Python, résultats dans `data/resume.js`)

- **Glissement annuel :** valeur(t) ÷ valeur(même mois ou même trimestre, un an plus tôt) − 1, en appariant **par date** et non par nombre de lignes. Si l'une des deux valeurs manque, le point est manquant. Quand le dernier glissement n'est pas calculable, la carte affiche le dernier calculable, avec sa date et la raison.
- **Variations :** en points pour les types T et N* ; en % pour le type N (non calculée si une valeur est nulle ou négative).
- **Position dans l'historique (percentile) :**
  - types T et N* : rang de la dernière valeur dans l'historique mensuel disponible (30 ans au plus) ;
  - type N : rang de la **variation sur 12 mois**, pas du niveau — un indice boursier ou un bilan de banque centrale suit une tendance de fond et serait presque toujours « au plus haut » ; la carte l'indique alors clairement (« variation sur 1 an : 85ᵉ percentile depuis 1990 ») ;
  - toujours afficher la période réellement utilisée (« 85ᵉ percentile depuis 1999 ») ; moins de 10 ans d'historique → mention « historique court » ; moins de 5 ans → pas de percentile ;
  - libellés : < 10 très bas · 10-25 bas · 25-75 habituel · 75-90 élevé · > 90 très élevé.
- **« Ce qui a bougé » :** pour les séries quotidiennes, variation sur 5 jours ouvrables divisée par l'écart-type des variations sur 5 jours des 5 dernières années. On retient les 5 plus grands rapports en valeur absolue, s'ils dépassent 1,5 ; sinon « semaine calme ».
- **Direction d'un signal (▲ ▼ ▶) :** variation sur 3 mois comparée à la moitié de l'écart-type historique des variations sur 3 mois de la série ; en deçà → ▶ (stable).
- **Phrases sur les anticipations de taux :** « baisses anticipées » si l'écart est sous −0,25 point, « hausses anticipées » au-dessus de +0,25, « stabilité » entre les deux.
- Tous ces seuils sont dans la config, pas dans le code.

---

## 7. Fiches explicatives

Chaque indicateur (et chaque indicateur calculé) a une fiche, ouverte par le bouton **ⓘ** partout où l'indicateur apparaît (panneau latéral sur PC, plein écran sur GSM).

**Structure obligatoire** (≈ 120 à 200 mots) :
1. **Titre** : nom complet + sigle expliqué
2. **En une phrase**
3. **Ce que ça mesure**
4. **Comment c'est calculé** (simplement)
5. **Comment l'interpréter** : repères chiffrés vérifiés ; s'il n'existe pas de seuil reconnu, se baser sur la position dans l'historique (percentiles)
6. **Ce qui le fait bouger / ce qu'il influence** (avec liens cliquables vers les indicateurs liés)
7. **Piège à éviter**
8. **Pied de fiche** : fréquence, source, début de l'historique, date de la dernière valeur

**Modèle à suivre (ton, longueur, précision) :**

> **VIX — l'« indice de la peur » du marché américain**
> **En une phrase :** le VIX mesure l'ampleur des mouvements que les investisseurs attendent sur la bourse américaine au cours des 30 prochains jours.
> **Ce que ça mesure :** la volatilité attendue, c'est-à-dire l'intensité des variations à la hausse comme à la baisse de l'indice S&P 500. Le VIX ne dit pas si la bourse va monter ou baisser ; il dit si elle risque de beaucoup bouger.
> **Comment c'est calculé :** le CBOE (Chicago Board Options Exchange, la bourse des options de Chicago) le calcule en continu à partir des prix des options sur le S&P 500, des contrats qui servent notamment d'assurance contre une baisse. Plus les investisseurs paient cher pour se protéger, plus le VIX monte. Il s'exprime en % sur un an : un VIX de 20 signifie que le marché s'attend à des variations d'environ 20 % sur un an, soit à peu près 6 % sur un mois (20 ÷ √12).
> **Comment l'interpréter :** sous 15, calme (parfois excès de confiance) ; de 15 à 20, normal ; de 20 à 30, nervosité ; au-dessus de 30, peur ; au-dessus de 40, panique (il a dépassé 80 au pire de la crise de 2008 et en mars 2020).
> **Ce qui le fait bouger :** il monte presque toujours quand la bourse chute (lien inverse avec le S&P 500) et s'envole lors des chocs : faillites bancaires, pandémie, guerre. Un VIX très élevé a souvent coïncidé avec des points bas de la bourse, mais ce n'est pas une règle.
> **Piège à éviter :** le VIX ne prévoit pas la direction du marché, et il retombe souvent vite après un choc.
> *Quotidien · Source : CBOE via FRED (VIXCLS) · Depuis 1990.*

**Fiches « transversales »** à rédiger aussi : base 100, points de % vs %, glissement annuel, corrélation (et « corrélation ≠ causalité »), corrélation glissante, décalage, percentile, QE/QT, point mort d'inflation, courbe des taux, écart de taux (spread), ETF, contrat à terme (« future »), prix hors dividendes, seuil de fiabilité d'une corrélation.

**Particularités :** quand une série a une particularité connue (mois manquant, changement de définition, historique court, source de secours, cours hors dividendes), la fiche le dit dans « Piège à éviter » ou en pied de fiche. Le rédacteur liste à part les affirmations dont il n'est pas certain, au lieu de les écrire : le relecteur les tranchera.

---

## 8. L'application — pages et design

### 8.1 Principes de design
- Reprendre l'**identité visuelle de l'application Aedifica** (voir §2). Tableau de bord financier sobre, aéré, très lisible.
- **Responsive** : PC (≥ 1280 px) et GSM (≈ 390 px). Sur GSM : navigation par barre inférieure ou menu, cartes en une colonne, graphiques pleine largeur, légendes repliables.
- **Code couleur réservé :** 🟢 **vert / 🔴 rouge / gris** = **uniquement pour les corrélations** (§9). Les variations à la hausse ou à la baisse sont affichées avec des flèches ▲▼ en **couleur neutre** (une hausse n'est pas toujours une bonne nouvelle : inflation, VIX…). Choisir un vert et un rouge qui restent distincts pour un daltonien (par exemple un vert bleuté et un rouge orangé).
- **Accessibilité :** la couleur n'est jamais la seule information (chiffre et libellé toujours visibles), contrastes suffisants, navigation au clavier.
- Infobulles sur survol / appui long : valeur exacte, date, unité.
- Option « **Afficher les grands événements** » sur tous les graphiques (lignes verticales annotées depuis `config/evenements.yaml`, modifiable par Georgy). Contenu initial : crise asiatique (juil. 1997), crise russe et LTCM (août 1998), sommet de la bulle Internet (mars 2000), 11 septembre 2001, faillite de Lehman Brothers (15 sept. 2008), crise de la dette de la zone euro (mai 2010), « Whatever it takes » de Mario Draghi (26 juil. 2012), référendum du Brexit (23 juin 2016), krach du Covid (mars 2020), invasion de l'Ukraine (24 févr. 2022), faillite de la Silicon Valley Bank (10 mars 2023), débouclage des positions sur le yen (5 août 2024), annonce des droits de douane américains (2 avr. 2025). Y ajouter, dans une catégorie « banques centrales », les lancements des grands programmes de QE (Fed : nov. 2008, nov. 2010, sept. 2012, mars 2020 ; BCE : janv. 2015, mars 2020), utilisés par l'historique des jauges (§8.4). Vérifier toutes les dates à l'étape 1 et proposer à Georgy 1 à 3 événements marquants plus récents.
- Mémoriser les derniers choix (page, période, sélection du comparateur) dans le stockage local du navigateur, avec `try/catch` (ne jamais planter si indisponible).

### 8.2 Éléments communs
**Carte indicateur :** nom court + ⓘ · dernière valeur avec unité · date de la valeur (+ « publié chaque mois » si non quotidien) · variation sur 1 mois et 1 an (en points pour les types T et N*, en % pour le type N) · mini-courbe sur 1 an · **position dans l'historique** (« 85ᵉ percentile depuis 1999 — élevé », règles au §6.1) · bouton **＋ Comparer** · pastille d'alerte si la série est en retard. Toutes ces valeurs viennent de `data/resume.js`.

**Graphique de famille** (sur chaque page thématique) : cases à cocher dans la légende, boutons de période **1 M · 1 A · 5 A · 10 A · 30 A · Max**, axe % à gauche et axe des niveaux à droite si nécessaire, bouton « Ouvrir dans le comparateur ». Un bouton de période est **grisé, avec une infobulle**, quand la série aurait moins de 12 points sur cette période (ex. 1 M pour une série mensuelle, 1 A pour une série trimestrielle).

### 8.3 Pages (onglets)
1. **Accueil — vue d'ensemble**
   - 12 cartes clés : taux de la Fed, taux de la BCE, US 10 ans, Bund 10 ans, inflation zone euro, inflation US, Brent, gaz TTF, VIX, EUR/USD, S&P 500, BEL 20.
   - **Jauges de stress** zone euro et États-Unis (§8.4).
   - **« Ce qui a bougé »** : les 5 mouvements les plus inhabituels de la semaine (mesurés par rapport à la volatilité habituelle de chaque série, règle au §6.1).
   - Bandeau d'état : « Données mises à jour le … à … » (heure belge) + nombre de séries en retard (lien vers la page État des données).
2. **Comparateur** (§9)
3. **Taux** : directeurs (A), longs (B), écarts calculés, mini-courbe des taux US (3 mois / 2 ans / 10 ans) aujourd'hui vs il y a 1 an.
4. **Inflation et anticipations**
   - Inflation par pays (C).
   - **Probabilités** : histogramme de la distribution SPF BCE pour N+1 et N+2, avec la phrase « Les prévisionnistes donnent X % de chances que l'inflation de la zone euro soit sous 2 % en 2027 » (somme des classes concernées) ; idem SPF US si disponible.
   - **Probabilité de récession US à 12 mois** (D14), sous forme de jauge et de courbe.
   - **Ce que le marché anticipe pour les taux** : phrases générées à partir des écarts calculés (ex. « Le marché anticipe des baisses de taux de la Fed : le 2 ans est 0,6 point sous le taux directeur »), avec un lien externe vers l'outil CME FedWatch (probabilités des décisions de la Fed).
   - **Prévisions du FMI** : tableau inflation et croissance (année en cours, N+1, N+2).
   - **Lecture des signaux d'inflation** (zone euro et US séparément) : pour chaque signal (Brent sur 1 an, gaz TTF, prix à la production, GSCPI, inflation anticipée, salaires, anticipations des ménages), direction sur les 3 derniers mois (▲ ▼ ▶, règle au §6.1). Synthèse : « 5 signaux sur 7 orientés à la baisse → pression à la baisse sur l'inflation dans les prochains mois ». Mention obligatoire : « Indication, pas une prévision ».
5. **Croissance et dette** : tableau comparatif des pays (croissance, dette en % du PIB, déficit, prévisions FMI), graphique en barres de la dette en % du PIB, courbes historiques. Encadré explicatif : « Une dette élevée oblige l'État à emprunter beaucoup, ce qui tend à maintenir des taux longs élevés. »
6. **Banques centrales** : bilans (montants et % du PIB), badge **QE / QT / stable** par banque, masse monétaire, encadré pédagogique « QE et QT en 4 lignes ».
7. **Bourses** (G + K)
8. **Énergie, matières premières et ETF** (H)
9. **Devises** (I) — afficher les cours dans le sens « 1 € = … » quand c'est pertinent.
10. **Risques et géopolitique** (J) : GPR (mensuel + quotidien récent), VIX et VSTOXX, indices de stress, tension sur le crédit, jauges.
11. **Comprendre** :
    - **Schéma interactif des liens** (SVG) : énergie/pétrole → inflation → taux directeurs → taux longs → crédit, immobilier, bourse ; dette publique → taux longs ; QE/QT → taux longs ; géopolitique → pétrole, VIX, dollar, or. Chaque bloc cliquable mène à sa page.
    - Lexique (toutes les fiches transversales).
    - Mode d'emploi en 10 lignes.
    - **État des données** : tableau de toutes les séries (statut, dernière date, source), bouton **« Télécharger toutes les données (CSV) »**, lien **« Mettre à jour maintenant »** vers la page du workflow GitHub (voir §10).

### 8.4 Jauges « conditions favorables à un QE » (zone euro et États-Unis)
Score affiché sur 6, avec le détail de chaque condition (✓ / ✗) et une phrase d'explication.

| Condition | Zone euro | États-Unis |
|---|---|---|
| 1. Inflation sous 2 % ou en net recul (−0,5 point sur 3 mois) | IPCH | PCE |
| 2. Peur sur les marchés (au-dessus du 90ᵉ percentile sur 30 ans) | VSTOXX | VIX |
| 3. Stress financier (au-dessus du 90ᵉ percentile) | CISS | STLFSI |
| 4. Tensions sur la dette (écart Italie − Allemagne au-dessus du 75ᵉ percentile et en hausse de plus de 0,5 point sur 1 mois) | ✓ | — (remplacé par : US 10 ans en hausse de plus de 0,75 point sur 1 mois) |
| 5. Crédit sous tension (indicateur retenu pour J6-J7 au-dessus du 90ᵉ percentile) | J7 | J6 |
| 6. Taux directeur déjà bas (≤ 1 %) | taux de dépôt | taux de la Fed |

Lecture : 0-1 = faible, 2-3 = possible, 4-6 = élevé. Texte fixe sous la jauge : « Un QE est surtout décidé quand l'inflation est basse et les marchés sous stress. Avec une inflation élevée, la banque centrale a peu de marge, sauf intervention d'urgence ciblée (ex. : Banque d'Angleterre, sept. 2022). » Seuils et percentiles dans la config.

- **Percentiles :** calculés sur l'historique disponible de chaque série (30 ans au plus) ; la période utilisée est affichée dans le détail.
- **Condition non évaluable** (série absente, ou moins de 10 ans d'historique) : affichée « non évaluée ». Le score est alors donné sur le nombre de conditions évaluées (ex. 2/5) et se lit en proportion : moins d'un tiers = faible ; d'un tiers à moins de deux tiers = possible ; deux tiers ou plus = élevé.
- **Mention sous chaque jauge :** « Indicateur maison, aide à la lecture — pas un modèle validé. »
- **Historique du score** (lot 3) : courbe mensuelle du score depuis que 4 conditions au moins sont évaluables, avec les dates de lancement réelles des QE (§8.1). C'est le moyen le plus simple, pour Georgy, de juger si la jauge aurait été utile par le passé.

---

## 9. Comparateur et corrélations (cœur de l'application)

### 9.1 Sélection
- Liste de **tous** les indicateurs, groupés par famille, avec un champ de recherche et des cases à cocher. Maximum 6 courbes (au-delà, message explicatif).
- **Indicateur de référence** : marqué d'une étoile ☆ (par défaut le premier coché). Les couleurs de corrélation se calculent **par rapport à lui**.
- **Comparaisons prêtes à l'emploi** (boutons) : « Pétrole → inflation zone euro » · « Inflation vs taux BCE vs Bund » · « Bund vs immobilier coté européen » · « VIX vs S&P 500 » · « Dette et taux : Italie vs Allemagne » · « Bilan de la Fed vs Nasdaq » · « Dollar vs or » · « Gaz TTF vs inflation Belgique ». Chaque bouton applique une **configuration complète** définie dans la config : indicateurs, référence, période, mode de calcul, décalage initial. Exemple : « Pétrole → inflation zone euro » = référence inflation zone euro, Brent, mode « Rythmes annuels », 10 A. Sans cela, un bouton ouvert dans le mode par défaut peut afficher « pas de lien » là où le lien existe.
- Périodes : **1 M · 1 A · 5 A · 10 A · 30 A · Max** + choix libre de dates. Une période est grisée, avec une infobulle, si l'un des indicateurs choisis y aurait moins de 12 points.

### 9.2 Affichage des courbes
- Les indicateurs de **type N** peuvent être affichés en **base 100** (100 = première valeur de la période choisie) ; les **types T et N*** restent toujours dans leur unité, sur l'axe % ou sur leur propre axe. Bascule : « Valeurs réelles » / « Base 100 ».
- **Axes :** les séries de même unité partagent un axe ; 3 axes au plus. Si la sélection en exigeait davantage, refuser l'ajout avec un message clair (« Trop d'unités différentes : passez en base 100 ou retirez une courbe »).
- Fréquence d'affichage et de calcul selon la période : **1 M → quotidien** ; **1 A → hebdomadaire** ; **5 A et plus → mensuel** (fin de période). Si deux séries ont des fréquences différentes, aligner sur la plus lente (dernière valeur de chaque période).
- La courbe de référence est dessinée en **bleu foncé**, plus épaisse, avec l'étiquette « Référence ».
- **Reconnaître les courbes :** comme la couleur sert à la corrélation, chaque courbe porte son nom court en bout de trait, et le survol (ou l'appui) d'une ligne de la légende met sa courbe en évidence.

### 9.3 Calcul de la corrélation (dans `js/stats.js`, fonctions pures et testées)
- **Coefficient de Pearson** entre chaque courbe et la référence, sur les dates communes. Minimum **12 points communs**, sinon « trop peu de données ».
- **Trois modes**, chacun expliqué en une ligne dans l'interface :
  1. **« Mouvements »** (par défaut) : variations d'une période à l'autre (type N → variation en % ; types T et N* → variation en points). Évite les fausses corrélations dues à deux tendances de fond.
  2. **« Rythmes annuels »** : type N → variation sur 12 mois en % ; types T et N* → niveau. (Ex. : Brent sur 1 an vs inflation.) Les variations sur 12 mois se recouvrent d'un mois à l'autre, ce qui gonfle r : l'interface le dit en une ligne.
  3. **« Niveaux bruts »** : avec l'avertissement « deux séries qui montent toutes les deux depuis 30 ans paraissent liées sans l'être forcément ».
- **Lecture de r :** |r| < 0,2 → aucun lien · 0,2 à 0,4 → faible · 0,4 à 0,7 → modéré · ≥ 0,7 → fort. Signe + → « bougent ensemble » ; signe − → « bougent en sens inverse ».
- **Seuil de fiabilité :** avec peu de points, un r élevé peut être dû au hasard. Règle unique, partout où un r est affiché ou sert à colorer : si |r| < max(0,2 ; 2 ÷ √n), où n est le nombre de points utilisés, le lien est classé « pas de lien fiable » (gris). Repères : n = 12 → 0,58 ; n = 26 → 0,39 ; n = 36 → 0,33 ; n = 60 → 0,26 ; n ≥ 100 → 0,2.
- **Fuseaux horaires :** en quotidien, les bourses d'Asie, d'Europe et d'Amérique ne clôturent pas à la même heure, ce qui affaiblit artificiellement leurs corrélations. Si la sélection mélange ces zones en vue 1 M, afficher une note d'une ligne qui conseille la vue 1 A (hebdomadaire).

### 9.4 Codage visuel (demande expresse de Georgy)
- 🟢 **Vert** = les courbes bougent **ensemble** (r positif).
- 🔴 **Rouge** = elles bougent **en sens inverse** (r négatif).
- ⚫ **Gris** = **pas de lien fiable** (|r| sous le seuil de fiabilité du §9.3).
- **Épaisseur du trait = force du lien** : gris 1,5 px ; faible 2 px (couleur pâle) ; modéré 3 px ; fort 4,5 px (couleur saturée).
- **Corrélation glissante dans le temps :** chaque segment de courbe est coloré selon la corrélation calculée sur une fenêtre mobile : **26 points** en hebdomadaire (vue 1 A), **24 points** en mensuel sur 5 A, **36 points** en mensuel sur 10 A et plus (valeurs dans la config). Le seuil de fiabilité s'applique à chaque fenêtre : avec des fenêtres plus courtes, les couleurs changeraient surtout au gré du hasard. Pour la même raison, pas de corrélation glissante en vue 1 M (une vingtaine de points) : on y affiche seulement le r global. Avant que la fenêtre soit complète : gris pointillé. Technique suggérée : options `segment.borderColor` / `segment.borderWidth` de Chart.js 4.
- **Bande de corrélation** sous le graphique : une ligne par indicateur, un ruban coloré du rouge au vert au fil du temps (lecture immédiate des périodes).
- **Légende** : pour chaque indicateur, le r global de la période (ex. « r = +0,78 — lien fort »), en chiffres **et** en mots.

### 9.5 Décalage dans le temps (pour anticiper)
- Pour chaque indicateur non-référence : curseur de **décalage de −24 à +24 mois** (adapter l'unité à la fréquence), limité à un tiers de la période affichée. Un décalage de +k signifie : « la valeur de l'indicateur au temps t est comparée à la référence au temps t + k », donc **l'indicateur précède la référence de k mois**. La courbe est visuellement décalée et r est recalculé. Pour décaler, utiliser les données de l'indicateur situées hors de la période affichée quand elles existent, afin de garder le même nombre de points.
- Bouton **« Trouver le meilleur décalage »** : calcule r pour chaque décalage, dans le mode en cours, affiche un petit graphique « r selon le décalage » et une phrase : « Le Brent semble précéder l'inflation de la zone euro d'environ 3 mois (r = +0,74). Ce lien statistique ne prouve pas une cause. »
  - N'annoncer un décalage que si le r obtenu dépasse le seuil de fiabilité **et** dépasse d'au moins 0,10 le r sans décalage ; sinon : « Aucun décalage ne ressort nettement. »
  - En essayant des dizaines de décalages, on finit toujours par trouver un chiffre flatteur : la phrase reste prudente (« semble précéder »), et le graphique permet de voir si le pic est net ou s'il s'agit d'un plateau.
  - Bouton indisponible en mode « Niveaux bruts » (résultat trompeur avec des séries à tendance).

### 9.6 Avec 3 indicateurs ou plus
Petit **tableau des corrélations** (chaque paire, cases colorées vert/rouge/gris avec le chiffre).

### 9.7 Export pour analyse par Claude
Bouton **« Exporter cette comparaison »** : télécharge un CSV des séries affichées (alignées, avec le mode choisi) + copie dans le presse-papiers un résumé texte (indicateurs, période, mode, r global, meilleur décalage), prêt à coller dans une conversation avec Claude. Si le navigateur refuse la copie, afficher le résumé dans une zone de texte à copier à la main.

Rappel permanent, discret, sous le graphique : « Corrélation ne veut pas dire causalité. »

---

## 10. Mise à jour automatique et mise en ligne (GitHub)

- **Compte :** celui déjà connecté à `gh` (celui qui héberge l'application Aedifica) → vérifier avec `gh auth status`.
- **Dépôt public** `tableau-marches` (nécessaire pour GitHub Pages gratuit) → les règles 10 et 11 du §3 s'appliquent.
- **Secret GitHub** `FRED_API_KEY` (et `EIA_API_KEY` si utilisée), créé avec `gh secret set` à partir du `.env` local, sans jamais afficher la clé.
- **Workflow `.github/workflows/mise-a-jour.yml`** nommé « Mise à jour des données » :
  - Déclencheurs : `schedule: cron "17 5 * * *"` (UTC → 6 h 17 en hiver, 7 h 17 en été, heure belge : la veille est clôturée sur tous les marchés) ; `workflow_dispatch` (bouton manuel) ; `push` sur `main` (redéploiement après une modification du code).
  - `permissions` : `contents: write`, `pages: write`, `id-token: write`. `concurrency` pour éviter deux exécutions simultanées ; `timeout-minutes: 30`. Utiliser les versions majeures actuelles des actions officielles (les vérifier, ne pas les citer de mémoire).
  - Étapes : récupérer le dépôt → installer Python (avec cache pip) → `collect.py` → `collect.py --verifier` → **commit uniquement si des fichiers de `data/` ont changé** (message : « Mise à jour des données — JJ/MM/AAAA ») → `git pull --rebase` puis `git push` → déployer sur **GitHub Pages par GitHub Actions** (`actions/upload-pages-artifact` + `actions/deploy-pages`, source Pages = « GitHub Actions », à activer via `gh api`).
  - Un commit poussé par le workflow avec le jeton par défaut ne relance pas le workflow : il n'y a donc pas de boucle. Le vérifier lors du premier test.
  - Les données réussies sont **toujours publiées**. Tout à la fin, le run est marqué **en échec** (→ e-mail de GitHub à Georgy, à condition que ses notifications Actions soient actives : l'expliquer dans le README) seulement si une série **essentielle** est en `erreur` depuis 3 exécutions planifiées de suite (compteur dans `etat.js`) ou `en_retard` au sens du §6. Une série `non_disponible` ne déclenche jamais d'alerte.
  - Les commits quotidiens gardent le workflow actif (GitHub désactive les tâches planifiées d'un dépôt public après 60 jours sans activité) : le vérifier et le documenter dans le README.
- **Dès la première mise en ligne (étape 3) :** comparer, série par série, la collecte faite par GitHub Actions avec la collecte locale. Une source qui répond sur le PC de Georgy peut refuser un serveur (Yahoo surtout) : mieux vaut le découvrir avant de construire le reste. Si une source essentielle échoue depuis GitHub, basculer sur son secours ou en chercher une autre.
- **Après chaque mise en ligne, vérifier réellement :** lancer `gh workflow run`, suivre avec `gh run watch`, puis contrôler que le site public affiche la nouvelle date de mise à jour.
- **Mise à jour manuelle par Georgy**, à expliquer dans le README et dans la page « Comprendre » :
  1. Dans l'application : lien « Mettre à jour maintenant » → page GitHub du workflow → bouton **Run workflow** (fonctionne aussi depuis l'application mobile GitHub).
  2. Pour rafraîchir la copie locale (usage hors ligne) : `git pull`, ou un double-clic sur un petit script prévu pour cela, adapté au système de Georgy (ex. `mettre_a_jour_local.bat` sous Windows).
- **Une seule main écrit dans `data/` :** une fois le workflow en service, le robot GitHub est le seul à enregistrer des données. En local, faire `git pull` avant de travailler et ne pas pousser de données collectées sur le PC ; sinon les deux se marchent dessus et Georgy se retrouve avec des conflits git qu'il ne peut pas résoudre.

---

## 11. Déroulé du travail

**Fil conducteur : mettre en ligne tôt une tranche mince mais complète, puis élargir.** Les principaux risques (sources qui se comportent autrement depuis un serveur GitHub, affichage en `file://`, rendu sur GSM, design) ne se voient qu'une fois la chaîne entière en place : mieux vaut les découvrir à l'étape 3 qu'à la fin.

**Journal d'avancement.** Tenir `AVANCEMENT.md` à jour à la fin de chaque étape (étape en cours, ce qui est fait, ce qui reste, décisions prises, problèmes ouverts) et faire un commit git local à chaque étape. Une session interrompue doit pouvoir reprendre avec ce seul fichier et ce cahier des charges, sans l'historique de la conversation.

**Étape 0 — Préparation**
- Créer `AVANCEMENT.md` et `CLAUDE.md`. Ce dernier reste court (10 à 15 lignes) : en tête, « Au début de chaque session, lire AVANCEMENT.md ; la référence est SPEC_Tableau_de_bord_Marches.md », puis les règles clés (interface en français, aucune donnée inventée, clé jamais écrite dans un fichier, le robot GitHub seul écrit dans `data/`) et les commandes utiles.
- Créer les agents (§1) et demander le redémarrage.
- Vérifier Python, git, `gh`, node ; s'il en manque un, guider Georgy pour l'installer, une commande à la fois. Retrouver et étudier l'application Aedifica (design).
- **Guider Georgy pour la clé FRED** (message simple, étape par étape) : créer un compte sur fredaccount.stlouisfed.org → « API Keys » → « Request API Key » (usage : « tableau de bord personnel ») → coller la clé quand tu la demandes. L'enregistrer dans `.env`.

**Étape 1 — Sources et plan**
- Lancer `chercheur-sources` **en parallèle, une famille par appel** → `docs/sources/<famille>.md`.
- Appeler `architecte` (Fable, xhigh) → `PLAN.md`.
- **Ne déranger Georgy que pour :** un indicateur essentiel impossible (lui présenter le remplaçant proposé en 2 lignes), les séries dont la rediffusion publique pose question (§3 règle 10), et les « Questions pour Georgy » du plan (3 au plus). Sinon, continuer.

**Étape 2 — Collecte et cœur des calculs**
- Implémenter `scripts/` pour toutes les familles, ainsi que `js/stats.js`, avec leurs tests (§12). Lancer une collecte complète puis `collect.py --verifier`. Corriger jusqu'à : toutes les séries essentielles en `ok` ou `secours` (ou `non_disponible` justifié).
- Produire le rapport de couverture : indicateur, source, début de l'historique, dernière date.
- Appeler `relecteur` en mode « revue des calculs », puis corriger les écarts signalés. Une erreur de calcul trouvée ici coûte dix fois moins cher qu'à la fin.

**Étape 3 — Première version en ligne (lot 1)**
- Construire : Accueil (cartes, « ce qui a bougé », bandeau d'état — les jauges viendront au lot 3), Comparateur complet, page Taux, État des données, avec l'identité visuelle Aedifica.
- Mettre en ligne (§10) : dépôt, secret, Pages, workflow, exécution manuelle de test. Vérifier la collecte **depuis GitHub Actions** et le site public **sur la vue GSM**.
- **Point d'arrêt (le seul du projet) :** donner à Georgy le lien et deux captures (PC, GSM), et lui demander en 3 lignes si le design et le comparateur lui conviennent. Attendre sa réponse, intégrer ses remarques, puis continuer sans autre interruption.

**Étape 4 — Fiches** : `redacteur-fiches` (Sonnet, high), par lots de familles → `js/fiches.js`.

**Étape 5 — Reste de l'application**
- **Lot 2 :** les autres pages thématiques, cartes, graphiques de famille, exports, page « Comprendre » (lexique, mode d'emploi).
- **Lot 3 :** probabilités (SPF, récession), jauges QE et leur historique, lecture des signaux d'inflation, prévisions du FMI, schéma interactif des liens, courbe à terme du pétrole.

**Étape 6 — Tests** (§12) et **captures d'écran** de chaque page en PC (1440 × 900) et GSM (390 × 844), avec Playwright en mode sans interface → `docs/captures/`. Les examiner et corriger tout défaut visuel. Relancer le workflow et vérifier le site public.

**Étape 7 — Relecture** : `relecteur` en mode « relecture finale » (Fable, xhigh), puis corrections des écarts signalés.

**Étape 8 — Remise à Georgy** (§13).

**Escalade :** si un problème technique résiste à **2 tentatives** de la session principale, appeler `architecte` pour un diagnostic avant de continuer.

**Si le temps ou le quota manque**, l'ordre de priorité est : (1) exactitude des données et des calculs, (2) comparateur, (3) Accueil et pages thématiques, (4) fiches, (5) lot 3. Mieux vaut un lot 3 absent et annoncé comme tel dans la remise qu'un lot 3 approximatif.

---

## 12. Tests et définition de « terminé »

**Tests automatiques**
- `pytest` : glissement annuel (y compris avec un mois manquant : le point reste manquant), écarts, taux croisés, % du PIB, percentiles (types T et N), valeur nulle ou négative, fusion avec conservation des anciennes données en cas de panne, garde-fou contre une réponse tronquée, contrôle des raccords, détection des retards.
- `pytest`, robustesse : **aucune clé dans les fichiers écrits** (simuler une erreur réseau dont le message contient l'adresse d'appel avec la clé, puis vérifier `etat.js` et la sortie) ; **écriture déterministe** (deux exécutions sur les mêmes données donnent des fichiers identiques, hors `etat.js`) ; accents conservés dans les fichiers générés.
- `node --test` sur `js/stats.js` : base 100 ; corrélation (séries identiques → r = 1 ; opposées → r = −1 ; indépendantes → r ≈ 0) ; seuil de fiabilité ; corrélation glissante ; **détection du décalage** (une série synthétique décalée de 3 mois doit être retrouvée à +3) ; alignement de fréquences différentes ; traitement des types T, N et N* dans chaque mode.
- Zéro erreur dans la console du navigateur, sur chaque page, en `file://` **et** sur le site en ligne.

**Checklist finale (le relecteur la vérifie point par point)**
- [ ] Toutes les familles A à K présentes ; chaque série essentielle disponible ou justifiée « non disponible ».
- [ ] Aucune donnée inventée ni interpolée ; chaque série a sa source et sa date dans « État des données ».
- [ ] Une fiche par indicateur, conforme au modèle ; sigles expliqués ; accents corrects ; particularités des séries mentionnées.
- [ ] Périodes 1 M / 1 A / 5 A / 10 A / 30 A / Max fonctionnelles partout, ou grisées avec explication quand la série a trop peu de points.
- [ ] Comparateur : base 100 réservée au type N ; vert/rouge/gris + épaisseur ; seuil de fiabilité ; corrélation glissante ; bande de corrélation ; décalage ; meilleur décalage ; tableau des corrélations ; boutons prêts à l'emploi avec leur configuration ; export.
- [ ] Jauges QE, probabilités (SPF, récession), anticipations de taux, lecture des signaux d'inflation, prévisions FMI — ou, pour un élément du lot 3 non livré, mention claire dans la remise.
- [ ] Vert/rouge réservés aux corrélations ; variations en couleur neutre.
- [ ] Lisible et utilisable sur GSM ; design cohérent avec l'application Aedifica.
- [ ] Fonctionne hors ligne en double-cliquant sur `index.html`.
- [ ] Workflow quotidien opérationnel, testé par une exécution manuelle ; collecte vérifiée **depuis GitHub Actions** ; site public à jour.
- [ ] Aucune clé dans le dépôt, dans `data/`, dans l'historique git ni dans les journaux du workflow.
- [ ] Aucune série à rediffusion interdite publiée ; sources citées ; site non indexé ; aucune donnée personnelle de Georgy dans le dépôt.
- [ ] README en français, clair pour un non-développeur ; `AVANCEMENT.md` et `CLAUDE.md` à jour.

---

## 13. Remise à Georgy (message final, en français simple)

1. Le **lien** de l'application (et le chemin de `index.html` en local).
2. **Comment lire l'état des données** et quoi faire en cas d'alerte ou d'e-mail d'échec de GitHub.
3. **Comment lancer une mise à jour manuelle** (3 étapes).
4. Les indicateurs **non disponibles** ou **remplacés**, et pourquoi ; les éléments du lot 3 éventuellement non livrés.
5. Une suggestion de **3 comparaisons à essayer** en premier.
6. Comment demander une **analyse par Claude** (bouton d'export + exemple de question).
7. **Ce qu'il peut régler lui-même sans toucher au code** (dossier `config/` : valeurs suivies, événements, seuils), avec un exemple.
