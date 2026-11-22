# PLAN — Tableau de bord des marchés

Plan technique de l'architecte, 22 novembre 2026. Référence : `SPEC_Tableau_de_bord_Marches.md`.
Les appels exacts, formats et pièges de chaque source sont dans `docs/sources/<famille>.md` : ce plan y renvoie et ne les répète pas. Il ne donne que les décisions.

Vérifié en ligne ce jour : versions des actions GitHub (§10), conditions de l'API FRED et mentions légales de FRED, conditions d'usage des données du FMI, statut « Copyrighted: Citation Required » de `VIXCLS`, `MICH`, `IRSTCI01JPM156N`. Non vérifiable par un robot (page en 403) : conditions des statistiques de la BIS et de STOXX → à relire dans un navigateur avant la mise en ligne.

---

## 0. Décisions majeures

1. **Yahoo est la source unique des familles G, K, de H3-H15, de I6 et des « jours récents » de H1, H2, J1.** Stooq est bloqué (épreuve anti-robot) : aucun secours automatique pour les indices boursiers. C'est le premier risque du projet (technique depuis GitHub Actions, et juridique) → test dès l'étape 3, question 1 pour Georgy.
2. **Devises : variante (b).** BCE pour tout depuis 1999 (CNY : 2000-01-13), FRED seulement avant, raccord à date fixe.
3. **Moins de dépendance à FRED quand la source d'origine est gratuite et sans clé** : A2 et F2 à la BCE, B6-B8 à Eurostat (complet depuis 1990, licence claire). FRED reste la source d'environ 35 séries.
4. **Les conditions actuelles de FRED interdisent d'enregistrer et de redistribuer ses données sans accord écrit** (§5.1). Le projet entier repose sur l'enregistrement dans `data/` : on affiche les mentions exigées et on demande l'accord ; Georgy choisit entre mettre en ligne tout de suite ou attendre la réponse → question 2.
5. **Raccord de deux sources : refusé (et signalé) quand l'écart dépasse le seuil**, au lieu d'être seulement signalé : un saut de 3,9 % ajouté au WTI serait un faux mouvement.
6. **Fichiers « récent » : 36 mois** au lieu de 24 (paramètre `recent_mois`), sinon la vue 1 A du comparateur n'a pas assez de recul pour le mode « Rythmes annuels », la corrélation glissante et le décalage.
7. **Axe des x linéaire en millisecondes, graduations maison, pas d'adaptateur de dates : confirmé.** `lib/` ne contient que `chart.umd.min.js` (4.5.0). Trois précautions au §9.3.
8. **Fraîcheur : exceptions chiffrées par série** (§4) ; sans elles, la règle générale déclencherait de fausses alertes chaque trimestre (PIB, dette) et à chaque fête chinoise.
9. **Sur `push`, le workflow redéploie sans collecter.** La collecte ne tourne que sur `schedule` et `workflow_dispatch`.
10. **Jeux lents interrogés une fois par semaine** (FMI, SPF, EBP) : le FMI interdit le téléchargement automatisé en masse.
11. **Texte des phrases en JavaScript, chiffres en Python** : `resume.js` ne contient que des nombres et des codes ; l'heure et les statuts « en retard » ne sont que dans `etat.js`.

---

## 1. Exigences impossibles ou modifiées

| Exigence du cahier des charges | Constat | Décision |
|---|---|---|
| Secours Stooq (famille G), complément Euro Stoxx 50 avant 2007 | Stooq renvoie une épreuve JavaScript anti-robot ; on ne la contourne pas | G en source unique Yahoo ; G5 « depuis 2007 » ; panne → anciennes valeurs + alerte |
| B11 Chine 10 ans (essentiel) | Aucune source gratuite, fiable et documentée | `non_disponible`, raison affichée ; à signaler à Georgy (§13) |
| G11 CSI 300 | L'indice ne renvoie qu'un point chez Yahoo | Remplacé par l'ETF `510300.SS` (depuis 2012), nommé « ETF CSI 300 », si Yahoo est publié ; sinon `non_disponible` |
| D13 zone euro | L'OCDE ne publie plus de CLI pour la zone euro | `D13_ZE` = `non_disponible` ; ajout de `D13_DE` et `D13_G4E` (4 grandes économies européennes, dont le R.-U.) |
| C5-C10 depuis 1990 | L'IPCH commence en janvier 1997 | « depuis 1997 », pas de raccord avec l'OCDE (série rétropolée arrêtée) |
| Codes BCE `ICP…4.ANR` | Arrêtés en décembre 2025 | Jeu `HICP`, clé en `4D0`, série prise en entier |
| API FMI DataMapper | Hors service | API SDMX `api.imf.org` (WEO : forme 3.0 ; IPC : forme 2.1) |
| J2 Yahoo `^V2TX` | Introuvable | Fichier `h_v2tx.txt` du site STOXX |
| A6, A7, F4 | Pas de source nationale exploitable | BIS (`WS_CBPOL`, `WS_CBTA`) |
| C12 Japon | OCDE et FRED/OCDE arrêtés en 2021 | FMI (`CPI`), glissement publié |
| Raccord H1-H2 FRED + Yahoo | Comptant contre contrat à terme : écart de 0,2 % (Brent) à 3,9 % (WTI) ; FRED livre ces prix par lots hebdomadaires | Raccord refusé au-delà de 2 % (§7.4) ; tolérance de fraîcheur de 12 jours, utile quand FRED est seul |
| Phrase « X % de chances que l'inflation soit sous 2 % » (SPF BCE) | La classe « 1,8 à 2,2 % » chevauche 2 % | Trois chiffres : « sous 1,8 % », « proche de 2 % (1,8 à 2,2 %) », « au-dessus de 2,2 % ». SPF américaine : « sous 2 % » exact |
| D6 distribution de l'inflation américaine | Le fichier ne contient que l'inflation sous-jacente (IPC et PCE) | Afficher l'IPC sous-jacent, le dire |
| `robots.txt` | Sur un site de projet GitHub Pages il n'est pas à la racine du domaine : les moteurs l'ignorent | Le garder, mais la protection réelle est `<meta name="robots" content="noindex, nofollow">` dans `index.html`. Le dépôt GitHub lui-même reste indexable |
| `lib/` : adaptateur de dates | Inutile avec un axe linéaire | Non installé |
| Fichiers « récent » de 24 mois | Trop court pour la vue 1 A (§0, point 6) | 36 mois, réglable |
| IPC américain : `CPIAUCSL` | Série désaisonnalisée : son glissement diffère du chiffre officiel (calculé sur l'indice brut) | `CPIAUCNS` et `CPILFENS` à tester à l'étape 2 ; sinon garder les codes du cahier des charges et le dire dans la fiche |
| Mini-courbe « sur 1 an » | 5 points pour une série trimestrielle, 2 pour une annuelle | 1 an (J, S, M) ; 3 ans (T) ; 10 ans (A) ; la carte affiche la durée |
| Historique depuis 1990 | Débuts réels plus tardifs : A2 1999, A3 1994, A6 1996, B5 2004, B9 1993-11, D1-D3 2003, F1 2002-12, F3 1998, G1 1991, G3 1992, G10 1997, G13 2009, H4 2017, J2 1999, J4 1993-12 | Afficher « depuis AAAA » (percentile et pied de fiche) ; aucun raccord entre séries de nature différente |

---

## 2. Corrections au code déjà écrit

Les 12 tests JS et les 12 tests pytest passent ; les fonctions sont justes dans leur sens (signe du décalage, appariement par date). À corriger ou compléter, chaque point avec son test :

| n° | Fichier | Problème | Correctif |
|---|---|---|---|
| C1 | `js/stats.js` `aligner` | La grille est l'union des périodes présentes. Si **toutes** les séries choisies manquent la même période (ex. C1 et C2 : octobre 2025), la période disparaît : la variation « d'une période à l'autre » enjambe alors deux mois et un décalage de k indices ne vaut plus k mois | Pour S, M, T, A : grille **régulière** de la première à la dernière clé (ajouter `periodeSuivante(cle, frequence)`), avec `null` aux périodes vides. Pour J : garder l'union. Test : deux séries mensuelles avec le même mois absent → la grille contient ce mois, les deux variations voisines sont `null`, le décalage +3 est toujours retrouvé |
| C2 | `js/stats.js` `correlationGlissante` | Une fenêtre presque vide (12 paires sur 36) est acceptée | Paramètre `couverture_min` (0,8) : fenêtre ignorée (`null`) si moins de 80 % de paires valides |
| C3 | `js/stats.js` | Manquent : `fenetreGlissante(frequence, nbPoints)` (26 / 24 / 36, depuis les réglages), `decalageMax(frequence, nbPoints)`, `prolongerGrille(dates, frequence, k)` (périodes futures pour dessiner une courbe décalée) | Ajouts purs, testés |
| C4 | `scripts/fusion.py` `raccorder` | Les jours de la source rapide sont ajoutés même quand l'écart dépasse le seuil | Si `alerte` : retourner la série principale seule, aucune date provisoire, et le message. Le test existant reste valable ; ajouter `provisoires == []` |
| C5 | `scripts/fusion.py` `SEUILS_DEFAUT` | « 4 mois » = 120 jours : du 30 juin au 30 octobre il y a 122 jours → fausse alerte la veille de chaque publication de PIB | `T: 125` ; seuils lus dans `config/reglages.yaml`. La fraîcheur se juge sur la **dernière observation brute** de la source, pas sur la dernière valeur transformée (sinon C1 serait « en retard » : son glissement d'octobre 2026 n'existera jamais) |
| C6 | `scripts/calculs.py` `score_mouvement` | Recule de 5 **lignes** : faux pour les séries 7 jours sur 7 (`DFF`) ou à trous | Reculer de 7 jours calendaires avec `valeur_a_date(…, tolérance 4 jours)`, au numérateur comme dans l'historique |
| C7 | `scripts/calculs.py` `direction` | Compare l'indice `i − 3` : faux pour une série trimestrielle (D12) | Chercher la valeur à la date « − 3 mois » par clé (`ajouter_mois(d, -3)`) ; fonctionne en mensuel et en trimestriel |
| C8 | `scripts/calculs.py` `percentile_carte` | Classe la dernière valeur de l'historique mensuel, pas la valeur de la carte | Paramètre `valeur_courante` : T et N* → dernière valeur de la carte ; N → variation sur 1 an de la carte. Distribution = mois complets. Affichage borné à 1–99 |
| C9 | `scripts/commun.py` `ecrire_js` | Tout sur une ligne : chaque mise à jour réécrit une ligne de plusieurs centaines de Ko | Une ligne **par série** (objet de premier niveau : une clé par ligne, triées). `lire_js` reste valable |
| C10 | `scripts/commun.py` `telecharger` | Attente fixe de 4 s puis 8 s : insuffisant pour l'ONS et le FMI (429) | Paramètre `attente` par source (`config/sources.yaml`) : ONS 30 s, FMI 20 s, OCDE 10 s |
| C11 | `scripts/sources/sdmx.py` `normaliser_periode` | `2026-W46` → lundi ; le bilan de la BCE est daté du vendredi | Paramètre `jour_semaine` (5 pour `ILM`) |
| C12 | `scripts/sources/fred.py` | Le secours `fredgraph.csv` relève de la collecte automatisée hors API, que les mentions légales de FRED interdisent sans accord | Désactivé par défaut (`fred.secours_csv: non` dans `config/sources.yaml`) ; une clé refusée doit apparaître comme une erreur, pas être masquée |
| C13 | `scripts/calculs.py` `mois_complets` | — | Ne l'appliquer qu'aux séries J et S ; les séries officielles M, T, A sont enregistrées telles que publiées |

---

## 3. Configuration (`config/`)

| Fichier | Contenu |
|---|---|
| `indicateurs.yaml` | Source unique de vérité : familles, séries, séries calculées, auxiliaires, jeux particuliers, 12 cartes de l'Accueil |
| `reglages.yaml` | Tous les seuils (§8.6) |
| `sources.yaml` | Par source : libellé, mention, lien, `publier` (oui / non), `attente`, `cadence_jours` |
| `comparaisons.yaml` | Les 8 comparaisons prêtes à l'emploi (§9.5) |
| `evenements.yaml` | Existe |
| `saisie_manuelle.yaml` | Vide au départ (D5 passe par l'API) |

Schéma d'une entrée de `indicateurs.yaml` (champs du §6 du cahier des charges, plus quatre blocs facultatifs) :

```yaml
defauts: {debut: "1990-01-01", decimales: 2, decimales_stockage: 4, priorite: S, transformation: aucune}
familles:
  B: {nom: "Taux longs", page: taux, fichier: taux}
indicateurs:
  - id: H1
    nom: "Pétrole Brent (prix au comptant)"
    nom_court: "Brent"
    famille: H
    type: N            # T | N | N*
    unite: "USD/baril"
    pays: MONDE
    frequence: J       # J | S | M | T | A
    source: fred
    code: DCOILBRENTEU
    facteur: 1         # multiplicateur d'unité (ex. 0.001 : millions → milliards)
    avant:   {source: …, code: …, jusqua: "AAAA-MM-JJ"}     # préfixe historique, coupure à date fixe
    rapide:  {source: yahoo, code: "BZ=F"}                   # jours récents provisoires
    secours: {source: banque_mondiale, code: "Crude oil, Brent", mode: remplace, frequence: M, unite: "USD/baril", note: "moyenne mensuelle"}
    transformation: aucune   # aucune | glissement_annuel | ecart | croise | pourcentage_pib | formule
    formule: null            # pour les séries calculées : voir §4
    priorite: E
    decimales: 2             # affichage
    retard_max_jours: 10
    zone_horaire: null       # AM | EU | AS (note « fuseaux » du comparateur)
    groupe_mouvement: petrole
    mouvement: oui           # candidat à « Ce qui a bougé »
    fiche: H1                # plusieurs séries peuvent partager une fiche (E1_US … → E1)
    raison: null             # texte affiché si non_disponible
```

Un `id` sert de clé partout (fichiers de données, adresse, stockage local) : lettres, chiffres et `_` uniquement. Pour la famille K, des valeurs par défaut au niveau de la famille (source yahoo, type N, priorité S, fréquence J, fiche `K`) permettent à Georgy d'ajouter une ligne de trois champs (`id`, `nom`, `code`).

---

## 4. Tableau des séries

**Lecture.** `type · prio · fréq.` : type T / N / N* ; priorité E / S ; fréquence J quotidienne, S hebdomadaire, M mensuelle, T trimestrielle, A annuelle. `transf.` : — = aucune ; ga = `glissement_annuel`. `unité · déc.` : `pt` = point de % ; `déc.` = décimales d'affichage (stockage : 4, sauf mention). `retard` = `retard_max_jours` (vide = règle générale). `redif.` : L = libre avec mention de la source ; M = droits de tiers, publier avec la mention exigée (§5) ; R = restreinte, décision de Georgy (§5).
**Modes de secours.** `prolonge` : même nature, n'ajoute que les dates postérieures à la dernière valeur enregistrée, après contrôle de l'écart. `remplace` : nature différente, remplace la série entière après 5 échecs planifiés consécutifs (§7.5).
**Débuts** : tous à `1989-01-01` pour les séries transformées en glissement annuel, `1990-01-01` sinon ; le début réel est constaté dans les données.

### A — Taux directeurs (fichier `taux`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| A1 | Taux de la Fed | T · E · J | fred : `DFF` | — | — | % · 2 | | L |
| A2 | Taux de dépôt BCE | T · E · J | bce : `FM/B.U2.EUR.4F.KR.DFR.LEV`, option `escalier` (§7.3) | secours fred : `ECBDFR` (prolonge) | — | % · 2 | | L |
| A3 | Euribor 3 mois | T · S · M | bce : `FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA` | — | — | % · 2 | | M |
| A4 | Taux de la Banque d'Angleterre | T · E · J | boe : `IUDBEDR` | secours bis : `WS_CBPOL/D.GB` (prolonge ; clé à tester à l'étape 2) | — | % · 2 | | L |
| A5 | Taux au jour le jour, Japon | T · E · M | fred : `IRSTCI01JPM156N` | secours boj : `FM01/STRDCLUCON`, moyenne des mois complets (prolonge) | — | % · 2 | | M |
| A6 | Taux de référence chinois (LPR 1 an) | T · E · M | bis : `WS_CBPOL/M.CN` | — | — | % · 2 | 100 | M |
| A7 | Taux de la BNS | T · S · M | bis : `WS_CBPOL/M.CH` | — | — | % · 2 | 100 | M |

### B — Taux longs et écarts (fichier `taux`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| B1 | US 10 ans | T · E · J | fred : `DGS10` | — | — | % · 2 | | L |
| B2 | US 2 ans | T · E · J | fred : `DGS2` | — | — | % · 2 | | L |
| B3 | US 3 mois | T · S · J | fred : `DGS3MO` | — | — | % · 2 | | L |
| B4 | Bund 10 ans | T · E · J | bundesbank : `BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A` | avant (fin de mois, 1990-01 à 1997-07, historique mensuel seulement) : même clé en `M.` ; secours fred : `IRLTLT01DEM156N` (remplace, M) | — | % · 2 | | L |
| B5_2A | Zone euro 2 ans (AAA) | T · E · J | bce : `YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y` | — | — | % · 2 | | L |
| B5_10A | Zone euro 10 ans (AAA) | T · E · J | bce : `YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y` | — | — | % · 2 | | L |
| B6 | Belgique 10 ans (OLO) | T · E · M | eurostat : `irt_lt_mcby_m`, geo=BE | secours fred : `IRLTLT01BEM156N` (prolonge) | — | % · 2 | | L |
| B7 | France 10 ans (OAT) | T · S · M | eurostat : `irt_lt_mcby_m`, geo=FR | secours fred : `IRLTLT01FRM156N` (prolonge) | — | % · 2 | | L |
| B8 | Italie 10 ans (BTP) | T · E · M | eurostat : `irt_lt_mcby_m`, geo=IT | secours fred : `IRLTLT01ITM156N` (prolonge) | — | % · 2 | | L |
| B9 | Royaume-Uni 10 ans (Gilt) | T · E · J | boe : `IUDMNPY` (depuis 1993-11, pas de raccord avant) | secours fred : `IRLTLT01GBM156N` (remplace, M) | — | % · 2 | | L |
| B10 | Japon 10 ans (JGB) | T · E · J | mof_japon : colonne `10Y` de `jgbcme_all.csv` + `jgbcme.csv` | secours fred : `IRLTLT01JPM156N` (remplace, M) | — | % · 2 | 10 | L |
| B11 | Chine 10 ans | T · E · — | `non_disponible` — raison : « aucune source gratuite et fiable avec historique (FRED, FMI, Yahoo, ChinaBond testés) » | — | | | | |
| B12 | Suisse 10 ans | T · S · M | fred : `IRLTLT01CHM156N` | — | — | % · 2 | | M |
| X_DE10A_M | (auxiliaire) Allemagne 10 ans, moyenne mensuelle | T · — · M | eurostat : `irt_lt_mcby_m`, geo=DE | secours fred : `IRLTLT01DEM156N` (prolonge) | — | | | L |
| BC_10A2A | Écart US 10 ans − 2 ans | T · S · J | fred : `T10Y2Y` | secours calcul `B1 − B2` (prolonge) | ecart | pt · 2 | | L |
| BC_10A3M | Écart US 10 ans − 3 mois | T · S · J | fred : `T10Y3M` | secours calcul `B1 − B3` (prolonge) | ecart | pt · 2 | | L |
| BC_IT_DE | Écart Italie − Allemagne | T · S · M | calcul `B8 − X_DE10A_M` | — | ecart | pt · 2 | | L |
| BC_FR_DE | Écart France − Allemagne | T · S · M | calcul `B7 − X_DE10A_M` | — | ecart | pt · 2 | | L |
| BC_BE_DE | Écart Belgique − Allemagne | T · S · M | calcul `B6 − X_DE10A_M` | — | ecart | pt · 2 | | L |

Les trois écarts européens sont mensuels (moyennes mensuelles des deux côtés, même source) : c'est la seule comparaison homogène. Un appel Eurostat pour BE, FR, IT, DE.

### C — Inflation (fichier `inflation`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| C1 | Inflation US (IPC) | T · E · M | fred : `CPIAUCNS` (à tester ; sinon `CPIAUCSL`) | — | ga | % · 1 | | L |
| C2 | Inflation US sous-jacente (IPC) | T · S · M | fred : `CPILFENS` (à tester ; sinon `CPILFESL`) | — | ga | % · 1 | | L |
| C3 | Inflation US (PCE) | T · E · M | fred : `PCEPI` | — | ga | % · 1 | | L |
| C4 | Inflation US sous-jacente (PCE) | T · S · M | fred : `PCEPILFE` | — | ga | % · 1 | | L |
| C5 | Inflation zone euro | T · E · M | bce : `HICP/M.U2.N.000000.4D0.ANR` | secours eurostat : `prc_hicp_minr`, geo=EA, coicop18=TOTAL, unit=RCH_A (prolonge) | — | % · 1 | | L |
| C6 | Inflation sous-jacente zone euro | T · E · M | bce : `HICP/M.U2.N.XEF000.4D0.ANR` | secours eurostat : idem, coicop18=TOT_X_NRG_FOOD (prolonge) | — | % · 1 | | L |
| C7 | Inflation Belgique | T · E · M | bce : `HICP/M.BE.N.000000.4D0.ANR` | secours eurostat : geo=BE (prolonge) | — | % · 1 | | L |
| C8 | Inflation Allemagne | T · S · M | bce : `HICP/M.DE.N.000000.4D0.ANR` | secours eurostat : geo=DE | — | % · 1 | | L |
| C9 | Inflation France | T · S · M | bce : `HICP/M.FR.N.000000.4D0.ANR` | secours eurostat : geo=FR | — | % · 1 | | L |
| C10 | Inflation Italie | T · S · M | bce : `HICP/M.IT.N.000000.4D0.ANR` | secours eurostat : geo=IT | — | % · 1 | | L |
| C11 | Inflation Royaume-Uni | T · E · M | ons : `d7g7/mm23` | secours fmi : `CPI/GBR.CPI._T.YOY_PCH_PA_PT.M` (prolonge) | — | % · 1 | | L |
| C12 | Inflation Japon | T · E · M | fmi : `CPI/JPN.CPI._T.YOY_PCH_PA_PT.M` | — | — | % · 1 | 110 | M |
| C13 | Inflation Chine | T · E · M | ocde : `OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/CHN.M.N.CPI.PA._T.N.GY` | secours fmi : `CPI/CHN.CPI._T.YOY_PCH_PA_PT.M` (prolonge) | — | % · 1 | 90 | L |

C1-C2 : le glissement est manquant en octobre 2025 et en octobre 2026 (indice d'octobre 2025 jamais publié). La carte affiche le dernier glissement calculable avec sa date et la raison (§6.3, champ `note`).

### D — Anticipations et signaux avancés (fichier `inflation`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| D1 | Inflation anticipée US 5 ans | T · E · J | fred : `T5YIE` | — | — | % · 2 | | L |
| D2 | Inflation anticipée US 10 ans | T · S · J | fred : `T10YIE` | — | — | % · 2 | | L |
| D3 | Inflation anticipée US 5 ans dans 5 ans | T · S · J | fred : `T5YIFR` | — | — | % · 2 | | L |
| D4 | Inflation attendue par les ménages US | T · S · M | fred : `MICH` | — | — | % · 1 | | M |
| D5 | Distribution SPF zone euro | jeu `spf_bce` (§6.5) · E | bce : `SPF/Q.U2.HICP..<horizon>.Q.AVG` | page BCE `table_3_<enquête>` ; `saisie_manuelle.yaml` | | | 135 | L |
| D5_LT | Inflation attendue à long terme, zone euro (SPF) | T · S · T | bce : `SPF/Q.U2.HICP.POINT.LT.Q.AVG` (à tester ; sinon abandonner la série) | — | — | % · 2 | 135 | L |
| D6 | Distribution SPF États-Unis | jeu `spf_us` · S | fichier : `prob.xlsx` (Fed de Philadelphie), onglet `PRCCPI` | — | | | 135 | L |
| D7 | Prévisions d'inflation du FMI | jeu `fmi` · E | fmi : WEO `PCPIPCH` | — | | | 230 | M |
| D8 | Prix à la production US | T · S · M | fred : `PPIACO` | — | ga | % · 1 | | L |
| D9 | Prix à la production zone euro | T · S · M | eurostat : `sts_inppd_m` (`M.PRC_PRR_DOM.B-E36.NSA.PCH_SM.EA20`) | — | — | % · 1 | 90 | L |
| D10 | Tensions d'approvisionnement (GSCPI) | N* · E · M | fichier : `gscpi_data.xlsx` (Fed de New York) | — | — | écart-type · 2 | | L |
| D11 | Salaire horaire US | T · S · M | fred : `CES0500000003` | — | ga | % · 1 | | L |
| D12 | Salaires négociés zone euro | T · S · T | bce : `INW/Q.U2.N.INWR.000000.4F0.GY.IX` | — | — | % · 1 | 160 | L |
| D13_US | Indicateur avancé OCDE — États-Unis | N* · S · M | ocde : `OECD.SDD.STES,DSD_STES@DF_CLI/USA.M.LI...AA...H` | secours fred : `USALOLITOAASTSAM` (prolonge) | — | indice · 2 | | L |
| D13_CN | … Chine | N* · S · M | idem, `CHN` | secours fred : `CHNLOLITOAASTSAM` (prolonge) | — | indice · 2 | | L |
| D13_JP | … Japon | N* · S · M | idem, `JPN` | — | — | indice · 2 | | L |
| D13_UK | … Royaume-Uni | N* · S · M | idem, `GBR` | — | — | indice · 2 | | L |
| D13_DE | … Allemagne | N* · S · M | idem, `DEU` | — | — | indice · 2 | | L |
| D13_G4E | … 4 grandes économies européennes | N* · S · M | idem, `G4E` | — | — | indice · 2 | | L |
| D13_ZE | … zone euro | N* · S · — | `non_disponible` — raison : « l'OCDE ne publie plus cet indicateur pour la zone euro ; voir Allemagne et 4 grandes économies européennes » | | | | | |
| D14 | Probabilité de récession US à 12 mois | T · E · M | fichier : `allmonth.xls` (Fed de New York), feuille `rec_prob` | secours calcul depuis fred `GS10` et `TB3MS` (§8.5, prolonge) | formule | % · 1 | | L |
| D15 | Courbe à terme du pétrole | jeu `courbe_petrole` · S | yahoo : contrats mensuels Brent `BZ<lettre><aa>.NYM` | sinon `non_disponible` (clé EIA facultative) | | | | R |
| DC_FED | Anticipation des taux de la Fed | T · S · J | calcul `B2 − A1` | — | ecart | pt · 2 | | L |
| DC_BCE | Anticipation des taux de la BCE | T · S · J | calcul `B5_2A − A2` | — | ecart | pt · 2 | | L |

D14 : la série est datée du **mois de l'écart observé** t et vaut `Rec_prob(t + 12 mois) × 100` (dans le fichier, la probabilité est inscrite sur la ligne du mois visé : dernière valeur 12,4 % sur la ligne 2027-10, écart d'octobre 2026). Ne pas afficher la ligne datée d'aujourd'hui dans le fichier : c'est la prévision d'il y a un an.
Un appel OCDE pour tous les pays de D13 ; un appel BCE par clé.

### E — Croissance et dette (fichier `croissance`)

Suffixes d'identifiant et codes pays : `_US` `USA`, `_ZE` zone euro (`G163` au FMI, `EA21` à Eurostat, à défaut `EA20`, la même composition partout), `_DE` `DEU`, `_FR` `FRA`, `_IT` `ITA`, `_BE` `BEL`, `_JP` `JPN`, `_CN` `CHN`, `_UK` `GBR`. « (9) » = une série pour chacun de ces neuf suffixes.

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| E1_US | Croissance US | T · E · T | fred : `GDPC1` | secours ocde : flux QNA, `USA` (prolonge) | ga | % · 1 | 135 | L |
| E1_ZE | Croissance zone euro | T · E · T | eurostat : `namq_10_gdp`, unit=CLV_PCH_SM, s_adj=SCA, na_item=B1GQ | — | — | % · 1 | 135 | L |
| E1_JP | Croissance Japon | T · E · T | ocde : `OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_G20,1.1`, `JPN`, B1GQ, GY | secours fred : `JPNRGDPEXP` + ga (prolonge) | — | % · 1 | 150 | L |
| E1_UK | Croissance Royaume-Uni | T · E · T | ons : `abmi/pn2` | secours ocde : `GBR` (prolonge) | ga | % · 1 | 150 | L |
| E1_CN | Croissance Chine | T · E · T | ocde : idem, `CHN` | — | — | % · 1 | | L |
| E2 | Prévisions de croissance du FMI | jeu `fmi` · E | fmi : WEO `NGDP_RPCH` | — | | | 230 | M |
| E3_US … E3_UK (9) | Dette publique, % du PIB — <pays> | T · E · A | fmi : WEO `GGXWDG_NGDP`, années ≤ dernière année observée | — | — | % du PIB · 1 | 230 (édition) | M |
| E3T_BE, E3T_DE, E3T_FR, E3T_IT, E3T_ZE | Dette trimestrielle, % du PIB — <pays> | T · S · T | eurostat : `gov_10q_ggdebt`, unit=PC_GDP, sector=S13, na_item=GD | — | — | % du PIB · 1 | 230 | L |
| E3T_US | Dette fédérale US, % du PIB | T · S · T | fred : `GFDEGDQ188S` | — | — | % du PIB · 1 | 200 | L |
| E4_ZE, E4_DE, E4_FR, E4_IT, E4_BE | Dette publique — <pays> | N · S · T | eurostat : `gov_10q_ggdebt`, unit=MIO_EUR, facteur 0,001 | — | — | Md € · 0 | 230 | L |
| E4_US | Dette fédérale US | N · S · T | fred : `GFDEBTN`, facteur 0,001 | — | — | Md $ · 0 | 200 | L |
| E4_JP, E4_CN, E4_UK | Dette publique — <pays> | N · S · A | calcul `E3_xx × X_NGDP_xx ÷ 100 ÷ 1e9` | — | formule | Md ¥ / yuans / £ · 0 | 230 | M |
| E4_US_EUR, E4_JP_EUR, E4_CN_EUR, E4_UK_EUR | Dette publique en euros — <pays> | N · S · T ou A | calcul `E4_xx ÷ cours BCE (devise par euro) du dernier jour de la période` (I1, IC_EURJPY, IC_EURCNY, IC_EURGBP) | — | formule | Md € · 0 | | comme l'entrée |
| E5_US … E5_UK (9) | Solde budgétaire, % du PIB — <pays> | T · E · A | fmi : WEO `GGXCNL_NGDP`, années ≤ dernière année observée | — | — | % du PIB · 1 | 230 (édition) | M |
| PIBN_US | (auxiliaire) PIB nominal US | — · — · T | fred : `GDP` (annualisé : **moyenne** de 4 trimestres) | — | | Md $ | 135 | L |
| PIBN_ZE | (auxiliaire) PIB nominal zone euro | — · — · T | eurostat : `namq_10_gdp`, unit=CP_MEUR, s_adj=SCA, facteur 0,001 (**somme** de 4 trimestres) | — | | Md € | 170 | L |
| PIBN_JP | (auxiliaire) PIB nominal Japon | — · — · T | fred : `JPNNGDP` (annualisé : **moyenne**) | — | | Md ¥ | 150 | M |
| PIBN_UK | (auxiliaire) PIB nominal R.-U. | — · — · T | ons : `ybha/pn2`, facteur 0,001 (**somme**) | — | | Md £ | 150 | L |
| X_NGDP_JP, X_NGDP_CN, X_NGDP_UK | (auxiliaires) PIB nominal annuel | — · — · A | fmi : WEO `NGDP` | — | | unités de monnaie | | M |

E3T_US et E4_US portent sur la dette **fédérale** : ne jamais les tracer sur la même courbe que E3_US (toutes administrations) sans le dire ; la fiche l'explique. Les prévisions (années > dernière année observée) vont dans `previsions.js`, pas dans les séries. Un appel FMI par indicateur, tous pays ensemble.

### F — Banques centrales (fichier `banques`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| F1 | Bilan de la Fed | N · E · S | fred : `WALCL`, facteur 0,001 | — | — | Md $ · 0 | | L |
| F2 | Bilan de la BCE | N · E · S | bce : `ILM/W.U2.C.T000000.Z5.Z01`, facteur 0,001, date = vendredi de la semaine | secours fred : `ECBASSETSW`, facteur 0,001 (prolonge) | — | Md € · 0 | 21 | L |
| F3 | Bilan de la Banque du Japon | N · E · M | fred : `JPNASSETS`, facteur 0,1 | — | — | Md ¥ · 0 | | M |
| F4 | Bilan de la Banque d'Angleterre | N · S · M | bis : `WS_CBTA`, `GB`, FREQ=M, UNIT_MEASURE=XDC, TRANSFORMATION=B | — | — | Md £ · 0 | 170 | M |
| F5_FED | Bilan de la Fed, % du PIB | T · E · T | calcul : F1 fin de trimestre ÷ PIBN_US sur 4 trimestres × 100 | — | pourcentage_pib | % du PIB · 1 | | L |
| F5_BCE | Bilan de la BCE, % du PIB | T · E · T | calcul : F2 ÷ PIBN_ZE | — | pourcentage_pib | % du PIB · 1 | | L |
| F5_BOJ | Bilan de la Banque du Japon, % du PIB | T · S · T | calcul : F3 ÷ PIBN_JP | — | pourcentage_pib | % du PIB · 1 | | M |
| F5_BOE | Bilan de la Banque d'Angleterre, % du PIB | T · S · T | calcul : F4 ÷ PIBN_UK | — | pourcentage_pib | % du PIB · 1 | | M |
| F6 | Masse monétaire M2 US | N · S · M | fred : `M2SL` | — | — | Md $ · 0 | | L |
| F6_GA | Croissance de M2 US | T · S · M | calcul : ga de F6 | — | ga | % · 1 | | L |
| F7 | Croissance de M3 zone euro | T · S · M | bce : `BSI/M.U2.Y.V.M30.X.I.U2.2300.Z01.A` | — | — | % · 1 | | L |

### G — Bourses et K — Valeurs suivies (fichier `bourses`)

Tous : type N, fréquence J, source yahoo (clôture non ajustée), `transf.` aucune, unité « points » (devise pour G11, G13, K1), 0 décimale pour les indices et 2 pour G11, G13, K1, `redif.` R. Un seul appel groupé avec les familles H, I6, J1.

| id | nom_court | prio | code Yahoo | zone | retard | remarque |
|---|---|---|---|---|---|---|
| G1 | BEL 20 | E | `^BFX` | EU | | depuis 1991-04 |
| G2 | S&P 500 | E | `^GSPC` | AM | | |
| G3 | Dow Jones | S | `^DJI` | AM | | depuis 1992 |
| G4 | Nasdaq Composite | E | `^IXIC` | AM | | |
| G5 | Euro Stoxx 50 | E | `^STOXX50E` | EU | | depuis 2007-03 |
| G6 | DAX | S | `^GDAXI` | EU | | indice dividendes réinvestis : le dire dans la fiche |
| G7 | CAC 40 | S | `^FCHI` | EU | | |
| G8 | FTSE 100 | S | `^FTSE` | EU | | |
| G9 | Nikkei 225 | E | `^N225` | AS | 10 | |
| G10 | Shanghai Composite | E | `000001.SS` | AS | 14 | fêtes chinoises : 6 jours ouvrables sans cotation |
| G11 | ETF CSI 300 | S | `510300.SS` | AS | 14 | ETF en yuans, pas l'indice ; depuis 2012 |
| G12 | Hang Seng | E | `^HSI` | AS | 10 | |
| G13 | MSCI World (ETF, en euros) | E | `IWDA.AS` | EU | | hors dividendes ; remplaçant manuel `URTH` (USD), jamais raccordé |
| K1 | Aedifica | S | `AED.BR` | EU | | hors dividendes |

### H — Énergie, matières premières, ETF (fichier `energie`)

Tous : type N, fréquence J, `transf.` aucune, 2 décimales (H3 : 0 ; H6 : 3).

| id | nom_court | prio | source : code | complément / secours | unité | retard | redif. |
|---|---|---|---|---|---|---|---|
| H1 | Brent | E | fred : `DCOILBRENTEU` | rapide yahoo : `BZ=F` ; secours banque_mondiale : `Crude oil, Brent` (remplace, M) | USD/baril | 12 | L (+ R pour les jours Yahoo) |
| H2 | WTI | S | fred : `DCOILWTICO` | rapide yahoo : `CL=F` ; secours banque_mondiale : `Crude oil, WTI` (remplace, M) | USD/baril | 12 | L (+ R) |
| H3 | Or | E | yahoo : `GC=F` | secours banque_mondiale : `Gold` (remplace, M) | USD/once | | R |
| H4 | Gaz TTF (Europe) | E | yahoo : `TTF=F` | secours banque_mondiale : `Natural gas, Europe` (remplace, M, USD/mmbtu) | EUR/MWh | | R |
| H5 | Gaz Henry Hub (US) | S | yahoo : `NG=F` | secours banque_mondiale : `Natural gas, US` (remplace, M) | USD/mmbtu | | R |
| H6 | Cuivre | S | yahoo : `HG=F` | secours banque_mondiale : `Copper` (remplace, M, USD/tonne) | USD/livre | | R |
| H7 | ETF matières premières | E | yahoo : `DBC` | remplaçant manuel `GSG` | USD | | R |
| H8_USO | ETF pétrole WTI | S | yahoo : `USO` | — | USD | | R |
| H8_BNO | ETF pétrole Brent | S | yahoo : `BNO` | — | USD | | R |
| H9 | ETF or | S | yahoo : `GLD` | — | USD | | R |
| H10 | ETF immobilier US | E | yahoo : `VNQ` | — | USD | | R |
| H11 | ETF immobilier européen | E | yahoo : `IPRP.AS` | remplaçant manuel `IPRP.L` (pence) | EUR | | R |
| H12 | ETF obligations US 20 ans et + | E | yahoo : `TLT` | — | USD | | R |
| H13 | ETF obligations US 7-10 ans | S | yahoo : `IEF` | — | USD | | R |
| H14 | ETF obligations d'État zone euro | E | yahoo : `IEGA.AS` | remplaçant manuel `SEGA.L` (GBP) | EUR | | R |
| H15 | ETF obligations indexées US | S | yahoo : `TIP` | — | USD | | R |

« Remplaçant manuel » : même fournisseur, donc inutile en cas de panne de Yahoo ; il sert si un code disparaît (on change `code` dans la config). Le fichier de la Banque mondiale n'est téléchargé que lorsqu'un secours est actif. Avant de l'utiliser pour le Brent, recouper sa dernière valeur avec la moyenne mensuelle de `DCOILBRENTEU` (écart > 5 % → secours refusé).

### I — Devises (fichier `devises`)

Un appel BCE : `EXR/D.USD+JPY+CNY+GBP+CHF.EUR.SP00.A`. Tous : type N, fréquence J, `redif.` L (sauf I6).

| id | nom_court | prio | source : code | complément / secours | transf. | déc. |
|---|---|---|---|---|---|---|
| I1 | EUR/USD | E | bce : `EXR` USD | secours fred : `DEXUSEU` (prolonge) | — | 4 |
| IC_EURGBP | EUR/GBP | S | bce : `EXR` GBP | — | — | 4 |
| IC_EURCHF | EUR/CHF | S | bce : `EXR` CHF | — | — | 4 |
| IC_EURJPY | EUR/JPY | S | bce : `EXR` JPY | — | — | 2 |
| IC_EURCNY | EUR/CNY | S | bce : `EXR` CNY (depuis 2000-01-13) | — | — | 4 |
| I2 | USD/JPY | E | calcul `IC_EURJPY ÷ I1` | avant fred : `DEXJPUS` jusqu'au 1998-12-31 ; secours fred : `DEXJPUS` (prolonge) | croise | 2 |
| I3 | USD/CNY | E | calcul `IC_EURCNY ÷ I1` | avant fred : `DEXCHUS` jusqu'au 2000-01-12 ; secours fred : `DEXCHUS` (prolonge) | croise | 4 |
| I4 | GBP/USD | E | calcul `I1 ÷ IC_EURGBP` | avant fred : `DEXUSUK` jusqu'au 1998-12-31 ; secours fred : `DEXUSUK` (prolonge) | croise | 4 |
| I5 | USD/CHF | S | calcul `IC_EURCHF ÷ I1` | avant fred : `DEXSZUS` jusqu'au 1998-12-31 ; secours fred : `DEXSZUS` (prolonge) | croise | 4 |
| I6 | Indice du dollar (DXY) | E | yahoo : `DX-Y.NYB` (R) | secours fred : `DTWEXBGS` (remplace : « indice large du dollar (Fed) », depuis 2006) | — | 2 |

Raccord fixe : écart mesuré une fois au premier jour BCE (tous < 2 % d'après `docs/sources/I_devises.md` ; USD/JPY 1,15 %) et consigné dans `etat.js`. Aucune valeur n'est ajustée.

### J — Risques (fichier `risques`)

| id | nom_court | type · prio · fréq. | source : code | complément / secours | transf. | unité · déc. | retard | redif. |
|---|---|---|---|---|---|---|---|---|
| J1 | VIX | N* · E · J | fred : `VIXCLS` | rapide yahoo : `^VIX` | — | points · 2 | | M (+ R pour les jours Yahoo) |
| J2 | VSTOXX | N* · E · J | fichier : `h_v2tx.txt` (stoxx.com) | — | — | points · 2 | | R |
| J3 | Risque géopolitique (GPR, mensuel) | N* · E · M | fichier : `data_gpr_export.xls`, colonne `GPR` | — | — | indice · 0 | | L |
| J3_Q | Risque géopolitique (quotidien) | N* · S · J | fichier : `data_gpr_daily_recent.xls`, colonne `GPRD` | — | — | indice · 0 | 12 | L |
| J4 | Stress financier US (Fed de Saint-Louis) | N* · E · S | fred : `STLFSI4` | — | — | indice · 2 | 21 | L |
| J5 | Stress systémique zone euro (CISS) | N* · E · J | bce : `CISS/D.U2.Z0Z.4F.EC.SS_CIN.IDX` (stockage : 6 décimales) | — | — | indice · 3 | 10 | L |
| J6 | Écart de crédit des entreprises US | T · S · M | fichier : `ebp_csv.csv` (Fed), colonne `gz_spread` | secours fred : `NFCICREDIT` (remplace, S, N*) | — | pt · 2 | 100 | L |
| J6_EBP | Prime de crédit excédentaire US (EBP) | N* · S · M | même fichier, colonne `ebp` | — | — | pt · 2 | 100 | L |
| J7 | Tensions obligataires zone euro (composante du CISS) | N* · S · J | bce : `CISS/D.U2.Z0Z.4F.EC.SS_BMN.CON` (stockage : 6 décimales) | — | — | indice · 3 | 10 | L |

J7 est une approximation (contribution du marché obligataire au CISS), pas un écart de crédit pur : le nom et la fiche le disent. J6 et J7 servent à la condition 5 des jauges.

### Jeux particuliers (`data/previsions.js`, non sélectionnables dans le comparateur)

| jeu | contenu | source | cadence | « en retard » si |
|---|---|---|---|---|
| `spf_bce` | D5 : distributions année en cours, N+1, N+2, long terme | bce : `SPF/Q.U2.HICP...Q.AVG` (classe et horizon vides, dernière enquête ; à défaut une requête par horizon) | 7 jours | dernière enquête > 135 jours |
| `spf_us` | D6 : distribution IPC sous-jacent, année en cours et suivante | fichier `prob.xlsx`, onglet `PRCCPI` | 7 jours | > 135 jours |
| `fmi` | D7, E2 + dette et solde prévus | fmi : WEO, `PCPIPCH`, `NGDP_RPCH`, `GGXWDG_NGDP`, `GGXCNL_NGDP` | 7 jours | édition > 230 jours |
| `courbe_petrole` | D15 : Brent, échéances de 1 à 12 mois | yahoo : contrats mensuels, liste recalculée chaque jour | chaque jour | cours > 5 jours ouvrables |

---

## 5. Rediffusion publique : séries restreintes ou douteuses

### 5.1 FRED — point à trancher avant la mise en ligne

Lu ce jour sur `fred.stlouisfed.org/legal/` et `…/docs/api/terms_of_use.html` :
- obligation d'afficher la phrase de non-approbation (texte exact recopié dans `docs/sources/C_inflation.md`, phrase commençant par « This product uses the FRED® API ») et, puisque d'autres personnes peuvent voir l'application, un lien vers les conditions d'utilisation de l'API ;
- « FRED » ne doit pas figurer dans le nom de domaine ; ne pas laisser entendre que l'outil est approuvé ; ne pas retirer les mentions de droits ;
- les séries « Copyrighted: Citation Required » (`VIXCLS`, `MICH`, séries OCDE, `JPNASSETS`, `JPNNGDP`, `NFCICREDIT`) peuvent être utilisées avec citation de la source et de FRED ; les séries « Pre-approval required » ne le peuvent pas (aucune n'est utilisée) ;
- **mais la liste des interdictions sans accord écrit comprend le fait d'enregistrer, de mettre en cache ou d'archiver du contenu FRED, de le fournir à des tiers ou de l'intégrer à une base de données**, ainsi que la collecte automatisée par robot (l'API étant le canal prévu).

Conséquence : l'architecture imposée par le cahier des charges (données enregistrées dans un dépôt public) n'est pas clairement couverte par les conditions de FRED, même pour des données d'origine publique. Élément favorable : le résumé de ces mêmes conditions range parmi les usages permis le fait de créer une application à partir d'une partie des données de FRED, par l'API gratuite. Deux lectures possibles :
- **stricte (règle 10 du cahier des charges prise à la lettre)** : demander l'accord écrit de FRED et attendre sa réponse avant le premier `git push` public ; le travail local (étape 2) continue pendant ce temps ;
- **pragmatique (recommandée)** : mettre en ligne avec toutes les mentions, envoyer la demande d'accord en parallèle, retirer les séries FRED si la réponse est négative.

Dans les deux cas : (1) Georgy envoie une courte demande à FRED (texte à préparer par la session principale : outil personnel, non commercial, non indexé, une trentaine de séries, sources citées) ; (2) le secours `fredgraph.csv` est désactivé (C12) ; (3) en cas de refus, les séries d'origine publique sont reprises une à une à leur source (Trésor américain, Fed, BLS, BEA, EIA), chantier distinct, et `STLFSI4` devient `non_disponible`. → Question 2.

### 5.2 Tableau par fournisseur

| Fournisseur | Séries | Ce que disent les conditions | Recommandation |
|---|---|---|---|
| **Yahoo Finance** | G1-G13, K1, H3-H15, I6, jours récents de H1, H2, J1, jeu D15 | Collecte automatisée sans permission et réutilisation commerciale interdites ; les indices appartiennent en outre à leurs fournisseurs | **Georgy tranche (question 1).** Recommandé : publier avec mention « Source : Yahoo Finance — cours de clôture, hors dividendes », usage personnel non commercial, site non indexé. C'est une zone grise, pas une autorisation |
| **STOXX** | J2 (VSTOXX) | Conditions illisibles par un robot ; indice sous licence | Même décision que Yahoo (question 1). Si refus : ne publier que le dérivé nécessaire à la jauge (condition 2 vraie / fausse), calculé dans le workflow sans enregistrer la série |
| **Cboe via FRED** | J1 (VIX) | « Copyrighted: Citation Required » | Publier avec mention « Source : Chicago Board Options Exchange (Cboe), indice VIX, via FRED » |
| **Université du Michigan via FRED** | D4 | Idem ; FRED la diffuse avec un mois de délai | Publier avec mention « Source : Université du Michigan, Surveys of Consumers, via FRED » |
| **Banque du Japon, Cabinet Office via FRED** | F3, PIBN_JP (donc F5_BOJ), secours E1_JP | Idem | Publier avec mention de l'organisme et de FRED |
| **OCDE via FRED** | A5, B12, secours B4, B6-B10, D13 | Idem | Publier avec mention « Source : OCDE, via FRED » |
| **Fed de Chicago via FRED** | secours J6 (`NFCICREDIT`) | Idem | Secours seulement ; mention |
| **FMI** | C12, jeu `fmi` (D7, E2), E3, E5, E4_JP/CN/UK, secours C11, C13 | Publication et redistribution permises avec citation « Source : Fonds monétaire international, <base>, <lien> » ; transformation à signaler ; réutilisation commerciale sur autorisation ; téléchargement automatisé en masse interdit sans permission | Publier avec mention. WEO interrogé une fois par semaine, un appel par indicateur. Signaler « calcul à partir de » pour E4 (question 3) |
| **BIS** | A6, A7, F4 (donc F5_BOE), secours A4 | Usage des statistiques permis s'il n'est pas trompeur et ne suggère pas d'approbation ; redistribution non commerciale permise (page des statistiques non relue : 403) | Publier avec mention « Source : Banque des règlements internationaux (BIS) » ; relire `bis.org/terms_statistics.htm` dans un navigateur (question 3). Si refus : A6 et F4 `non_disponible`, A7 via `data.snb.ch` depuis 2000 |
| **EMMI (Euribor) via BCE** | A3 | Moyenne mensuelle publiée par la BCE, taux propriété de l'EMMI | Publier avec mention « Source : BCE (données EMMI) » ; série secondaire, à retirer au moindre doute |
| **Banque mondiale** | secours H1-H6 | CC BY 4.0 probable, non confirmé pour le fichier précis | Secours seulement ; mention « Banque mondiale, Commodity Price Data (The Pink Sheet) » |
| **Banque d'Angleterre, Ministère des Finances japonais** | A4, B9, B10 | Réutilisation avec mention ; conditions exactes non relues | Publier avec mention ; relire les deux pages avant la mise en ligne |
| **Fed de Saint-Louis** | J4 (`STLFSI4`) | Série propre à FRED ; statut non relu | Publier avec mention ; lire le statut sur la page de la série |
| **ICE BofA** | — | Rediffusion interdite | Non utilisé |

Libres avec mention de la source : BCE, Eurostat (CC BY 4.0), Bundesbank, ONS (OGL v3), OCDE (API directe), Fed de New York, Fed de Philadelphie, Fed (fichier EBP), GPR (citer Caldara et Iacoviello, 2022, *American Economic Review* 112(4), et la date de téléchargement). Données du domaine public américain (Fed, Trésor, BLS, BEA, EIA) : libres à leur source, mais reçues ici par FRED, donc sous la réserve du §5.1.

### 5.3 Mise en œuvre

- `config/sources.yaml` porte, par source : `mention` (texte affiché), `lien`, `publier`. Si `publier: non`, les séries de cette source ne sont pas téléchargées ; elles deviennent `non_disponible` (raison : « rediffusion non autorisée par le fournisseur »), sauf si un secours publiable existe (il devient la série). Un test pytest vérifie qu'aucune série d'une source non publiée n'apparaît dans `data/`.
- La mention de chaque série figure dans `catalogue.js` (champ `mention`), est affichée en pied de fiche, sous chaque graphique (« Sources : … ») et dans « État des données ».
- Page « Comprendre » : bloc « Sources et mentions légales » avec la phrase FRED (en anglais, suivie de sa traduction), le lien vers les conditions de l'API FRED, la citation GPR, la mention « calculs de l'auteur » pour les séries transformées (BCE et FMI le demandent).
- Retirer une série déjà publiée ne l'efface pas de l'historique git : en cas de demande d'un fournisseur, il faudra réécrire l'historique. Raison de plus pour trancher avant le premier `git push`.

---

## 6. Formats de `data/`

Les nombres des exemples de cette section illustrent la forme des fichiers ; ce ne sont pas des données.

### 6.1 Fichiers

| Fichier | Clé `window.DONNEES[…]` | Chargé | Change |
|---|---|---|---|
| `etat.js` | `etat` | au démarrage, en premier | à chaque exécution |
| `catalogue.js` | `catalogue` | au démarrage | quand la config ou un début d'historique change |
| `resume.js` | `resume` | au démarrage | quand une donnée change |
| `previsions.js` | `previsions` | pages Inflation, Croissance | chaque trimestre ou semestre, D15 chaque jour |
| `<fichier>_historique.js` | `<fichier>_historique` | au clic | en général une fois par mois par série |
| `<fichier>_recent.js` | `<fichier>_recent` | au clic | chaque jour |
| `donnees_mensuelles.csv` | — | lien de téléchargement | quand un mois complet change |

`<fichier>` ∈ `taux` (A, B), `inflation` (C, D), `croissance` (E), `banques` (F), `bourses` (G, K), `energie` (H), `devises` (I), `risques` (J). Les auxiliaires (`X_…`, `PIBN_…`) ne sont pas enregistrés (§7.6).

### 6.2 Séries

```js
window.DONNEES = window.DONNEES || {};
window.DONNEES["taux_historique"] = {
"A1":{"dates":["1990-01-01","1990-02-01"],"valeurs":[8.23,8.24]},
"B1":{"dates":["1990-01-01"],"valeurs":[8.43]}
};
```

- Une ligne par série, clés triées, pas de `null` : une date absente est un trou.
- **`_historique`** : toutes les séries du fichier. Dates au **premier jour de la période** (`AAAA-MM-01` ; trimestre `AAAA-01/04/07/10-01` ; année `AAAA-01-01`). Séries J et S : dernière observation de chaque mois **complet**. Séries M, T, A : valeurs telles que publiées.
- **`_recent`** : seulement les séries J et S, dates réelles d'observation, `recent_mois` (36) derniers mois.
- Position sur l'axe du temps : toujours la **fin de période** (`Stats.clePeriode`), pour que le point de fin novembre d'une série quotidienne et la valeur « novembre » d'une série mensuelle coïncident.
- Point provisoire du mois en cours : il n'est pas dans `_historique` ; le JavaScript l'ajoute depuis `resume.cartes[id]` (`date`, `valeur`) quand le mois de cette date est postérieur au dernier mois de l'historique, et le dessine en point creux avec la mention « provisoire ».

### 6.3 `resume.js`

```js
window.DONNEES["resume"] = {
"donnees_au": "2026-11-20",            // date la plus récente parmi les séries quotidiennes (pas l'horloge)
"cartes": {
  "B1": {
    "valeur": 5.04, "date": "2026-11-19",
    "provisoire_depuis": null,         // date du premier jour venu de la source rapide, sinon null
    "var_1m": 0.21, "var_1a": 0.64,    // points (T, N*) ou % (N) ; null si non calculable
    "mini": {"pas": "S", "duree": "1 an", "dates_fin": "2026-11-22", "valeurs": [4.41, null, 4.44]},
    "percentile": {"valeur": 85, "libelle": "élevé", "depuis": "1996", "base": "niveau", "court": false},
    "note": null                       // code de particularité, ex. "ga_base_manquante:2026-10"
  }
},
"bouge": {"du": "2026-11-13", "au": "2026-11-20", "calme": false,
  "liste": [{"id": "J1", "variation": 7.45, "rapport": 3.2, "depuis": "2026-11-13", "jusqua": "2026-11-20"}]},
"anticipations": {"fed": {"ecart": -0.6, "date": "2026-11-19", "lecture": "baisses"}, "bce": {"ecart": 0.62, "date": "2026-11-19", "lecture": "hausses"}},
"courbe_us": {"date": "2026-11-19", "points": {"3M": 4.34, "2A": 4.76, "10A": 5.04},
  "il_y_a_1_an": {"date": "2025-11-19", "points": {"3M": 3.9, "2A": 3.6, "10A": 4.1}}},
"qe_qt": {"F1": {"statut": "QT", "variation_3m": -1.8, "date": "2026-11-18", "date_reference": "2026-08-19"}},
"recession": {"probabilite": 12.4, "mois_ecart": "2026-10", "mois_vise": "2027-10", "ecart": 0.98, "origine": "fichier"},
"signaux": {"ZE": {"liste": [{"cle": "brent_1a", "id": "H1", "fleche": "▼", "variation": -8.1, "seuil": 6.2, "date": "2026-10-01"}],
  "hausse": 1, "baisse": 4, "stable": 1, "non_evalues": 1, "synthese": "baisse"}, "US": {}},
"jauges": {"ZE": {"score": 2, "evaluees": 6, "lecture": "possible",
  "conditions": [{"n": 1, "ok": false, "id": "C5", "valeur": 4.0, "date": "2026-10-01", "variation_3m": 0.4, "percentile": null, "depuis": null}],
  "historique": {"debut": "2000-01-01", "scores": [1, 1, 2], "evaluees": [5, 5, 6]}}, "US": {}},
"pays": {"US": {"croissance": {"valeur": 2.07, "date": "2026-07-01"}, "dette": {"valeur": 124.4, "annee": 2025},
  "deficit": {"valeur": -7.9, "annee": 2025}, "dette_montant": {"valeur": 39462, "devise": "USD", "en_euros": 36420, "date": "2026-04-01"}}}
};
```

- `percentile` sans valeur : `{"valeur": null, "raison": "historique_court"}`. `base` vaut `niveau` (T, N*) ou `variation_12m` (N).
- `mini` : séries J → une valeur par semaine (dernière de la semaine), 53 points ; S → 53 ; M → 13 ; T → 13 (3 ans) ; A → 11 (10 ans). `null` = trou.
- `lecture` ∈ `baisses` / `hausses` / `stabilite` ; `statut` ∈ `QE` / `QT` / `stable` ; `synthese` ∈ `baisse` / `hausse` / `partage` ; `ok` ∈ `true` / `false` / `null` (non évaluée). Les phrases sont composées en JavaScript à partir de ces codes.
- Rien dans ce fichier ne dépend de l'heure d'exécution.

### 6.4 `etat.js` et `catalogue.js`

```js
window.DONNEES["etat"] = {
"genere_le": "2026-11-22T05:31:07Z",     // UTC ; affiché en heure belge par le JavaScript
"declencheur": "schedule",                // schedule | workflow_dispatch | local
"comptes": {"ok": 150, "secours": 2, "en_retard": 3, "erreur": 1, "non_disponible": 3},
"alerte": {"declenchee": false, "motifs": []},
"sources": {"fmi_weo": {"dernier_appel": "2026-11-16"}},
"series": {
  "H1": {"statut": "ok", "valeur": 92.4, "date": "2026-11-20", "date_source": "2026-11-17",
         "source": "FRED (EIA) + Yahoo Finance", "role": "principale+rapide", "echecs": 0,
         "raccord": {"date": "2026-11-17", "ecart": 0.22, "alerte": null},
         "message": "3 jours récents provisoires (contrat à terme)"}
},
"jeux": {"spf_bce": {"statut": "ok", "date": "2026-10-30", "echecs": 0, "message": ""}}
};
```

- `statut` ∈ `ok` / `en_retard` / `erreur` / `secours` / `non_disponible` ; `role` ∈ `principale` / `principale+rapide` / `secours`. Tout `message` passe par `commun.nettoyer()`.
- `echecs` = nombre d'exécutions **planifiées** consécutives en erreur (§7.7).

```js
window.DONNEES["catalogue"] = {
"familles": [{"id": "B", "nom": "Taux longs", "page": "taux", "fichier": "taux"}],
"indicateurs": {"B1": {"nom": "…", "nom_court": "US 10 ans", "famille": "B", "fichier": "taux", "type": "T",
  "unite": "%", "pays": "US", "frequence": "J", "decimales": 2, "priorite": "E", "source": "FRED (Trésor américain)",
  "mention": "…", "lien_source": "…", "debut": "1990-01-02", "fiche": "B1", "calcule": false,
  "zone_horaire": "AM", "particularite": null, "raison": null}},
"jeux": {"spf_bce": {"nom": "…", "mention": "…"}},
"accueil": ["A1", "A2", "B1", "B4", "C5", "C1", "H1", "H4", "J1", "I1", "G2", "G1"],
"comparaisons": [],        // copie de config/comparaisons.yaml
"evenements": [],          // copie de config/evenements.yaml
"reglages": {}             // sous-ensemble de reglages.yaml utile au JavaScript (fenêtres, seuils de r, périodes)
};
```

### 6.5 `previsions.js`

```js
window.DONNEES["previsions"] = {
"spf_bce": {"enquete": "2026-Q4",
  "classes": [{"code": "TN0_8", "min": null, "max": -0.8}, {"code": "F1_8T2_2", "min": 1.8, "max": 2.2}, {"code": "F4_8", "min": 4.8, "max": null}],
  "horizons": [{"cle": "2027", "annee": 2027, "probabilites": [0.1, 0.3], "moyenne": 2.6, "reponses": 51,
                "sous_1_8": 11.3, "proche_de_2": 15.5, "au_dessus_de_2_2": 73.1}]},
"spf_us": {"enquete": "2026-Q4", "mesure": "IPC sous-jacent (T4 sur T4)",
  "classes": [{"min": 4.0, "max": null}],
  "horizons": [{"cle": "annee_en_cours", "annee": 2026, "probabilites": [1.7, 6.7], "sous_2": 2.0}]},
"fmi": {"edition": "2026-10", "publiee_le": "2026-10-13", "derniere_annee_observee": 2025,
  "annees": [2025, 2026, 2027, 2028], "pays": ["US", "ZE", "DE", "FR", "IT", "BE", "JP", "CN", "UK"],
  "inflation": {"US": [2.9, 3.65, 2.83, 2.11]}, "croissance": {}, "dette": {}, "solde": {}},
"courbe_petrole": {"statut": "ok", "produit": "Brent", "date": "2026-11-20", "unite": "USD/baril",
  "comptant": {"valeur": 89.95, "contrat": "BZ=F"},
  "points": [{"echeance": "2027-01", "contrat": "BZF27.NYM", "prix": 92.57}],
  "dans_6_mois": {"echeance": "2027-05", "prix": 84.37}, "dans_12_mois": {"echeance": "2027-11", "prix": 78.08}}
};
```

- SPF BCE : ne garder que `FCT_SOURCE=AVG`, exclure `FCT_BREAKDOWN=POINT` de l'histogramme (c'est `moyenne`), ne garder que les classes de la grille de la dernière enquête ; contrôle : somme des probabilités entre 99 et 101, sinon jeu en `erreur`.
- Dans `fmi`, la première année du tableau est la dernière année observée ; les suivantes sont des prévisions. `derniere_annee_observee` vient de `LATEST_ACTUAL_ANNUAL_DATA` ; à défaut : année de publication − 1.
- `courbe_petrole` : échéance « dans 6 mois » = contrat dont le mois de livraison est le mois courant + 6 ; s'il manque, prendre le plus proche à ± 1 mois, sinon `null`. Contrat du mois écoulé exclu.

### 6.6 `donnees_mensuelles.csv`

`utf-8-sig`, séparateur `;`, virgule décimale, fins de ligne LF. Colonne 1 `Mois` (`AAAA-MM`), puis une colonne par série publiée, dans l'ordre du catalogue, en-tête `nom_court (unité) [id]`. Mois complets seulement. Une valeur trimestrielle est placée sur le dernier mois du trimestre, une valeur annuelle sur décembre. Cellule vide = pas de valeur.

---

## 7. Collecte (`scripts/`)

### 7.1 Modules

| Module | Rôle |
|---|---|
| `collect.py` | Orchestration et ligne de commande |
| `commun.py`, `fusion.py`, `calculs.py` | Existent (corrections §2) |
| `config.py` | Lecture et validation des YAML (ids uniques, champs obligatoires, formules résolues, pas de cycle) |
| `resume.py` | Construction de `resume.js` (cartes, « ce qui a bougé », jauges, signaux, QE/QT, tableau des pays) |
| `previsions.py` | Jeux particuliers |
| `ecriture.py` | Découpage historique / récent, catalogue, état, CSV |
| `verifier.py` | Validation, rapport court, règle d'alerte |
| `verifier_cle.py` | Recherche de la clé avant `git push` (§10.3) |
| `captures.py` | Playwright (étape 6) |
| `sources/fred.py`, `sources/sdmx.py` | Existent |
| `sources/bce.py`, `bis.py`, `ocde.py`, `fmi.py` | Appels SDMX, s'appuient sur `sdmx.py` ; `fmi.py` lit aussi le SDMX-JSON 3.0 (années non triées : passer par l'index) |
| `sources/eurostat.py` | JSON-stat |
| `sources/boe.py`, `bundesbank.py`, `mof_japon.py`, `boj.py`, `ons.py` | Un fichier par institut ; `boe.py` détecte la page HTML « Object moved » |
| `sources/yahoo.py` | Un appel groupé `yfinance`, clôture non ajustée, puis rattrapage code par code |
| `sources/banque_mondiale.py` | Lit la page, en extrait le lien du classeur, puis la feuille `Monthly Prices` |
| `sources/fichiers.py` | GSCPI, probabilité de récession, SPF de Philadelphie, GPR (2 fichiers), EBP, VSTOXX |
| `sources/manuel.py` | `saisie_manuelle.yaml` |

Chaque module expose `telecharger(demandes) -> {id: série | ErreurSource}` : une demande groupée qui échoue met en échec chacune de ses séries, jamais les autres sources. Lire les `.xls` avec `xlrd` et les `.xlsx` avec `openpyxl` directement (pas de `pandas.read_excel`). `requirements.txt` : `requests`, `pyyaml`, `yfinance` (version testée 1.8), `pandas`, `openpyxl`, `xlrd`, `pytest` ; versions figées à celles testées en local. `requirements-dev.txt` : `playwright`.

### 7.2 Ligne de commande

`python scripts/collect.py` · `--serie ID` · `--verifier` (rapport, code 1 si une série essentielle est en `erreur`) · `--alerte` (code 1 seulement selon la règle du §7.7) · `--declencheur schedule|workflow_dispatch|local` (défaut `local`) · `--sortie DOSSIER` (défaut `data/` ; **en local, une fois le robot en service, toujours `--sortie cache/essai`**) · `--forcer ID` (accepte une série que le garde-fou refuse) · `--couverture` (écrit `docs/couverture.md`).

### 7.3 Enchaînement

1. Config, `.env`, lecture de `data/` existant et de l'état précédent.
2. Téléchargements par source (ordre : BCE, Eurostat, FRED avec 0,3 s entre appels, instituts, fichiers, OCDE, BIS, FMI, Yahoo en dernier, puis un second essai Yahoo en fin d'exécution pour les codes en échec). Sources à `cadence_jours` : sautées si le dernier appel réussi est trop récent (statut et compteur inchangés).
3. Par série : facteur d'unité → bloc `avant` → bloc `rapide` (raccord, §7.4) → secours si la source principale a échoué (§7.5) → transformation.
4. Séries calculées, dans l'ordre des dépendances.
5. Fusion avec l'existant et garde-fou, séparément pour l'historique mensuel et pour le récent.
6. Validation, fraîcheur, statuts.
7. `resume`, `previsions`, `catalogue`, CSV, `etat` ; écriture déterministe.

Option `escalier` (A2) : la source ne donne que les dates de changement ; la série quotidienne prend, chaque jour ouvrable du premier changement à la date d'exécution, le dernier taux en vigueur. C'est la définition d'un taux directeur, pas une interpolation. Ne pas prolonger au-delà de la date d'exécution même si la source annonce un changement futur.

### 7.4 Raccords

- **Mobile (`rapide`)** : `fusion.raccorder` à la dernière date commune. Écart ≥ seuil (N : 2 % ; T, N* : 0,10 point) → **raccord refusé**, série principale seule, message dans `etat.js`, statut inchangé. Sinon les jours rapides sont ajoutés, `provisoire_depuis` est renseigné, et la carte dit « provisoire » (pour H1-H2 : « contrat à terme »).
- **Fixe (`avant`)** : coupure à la date `jusqua` ; l'écart est mesuré le premier jour où les deux sources existent, consigné, jamais corrigé.
- Séries raccordées et « Ce qui a bougé » : le score est calculé **entièrement sur la source rapide** (elle a plus de 5 ans d'historique : `BZ=F`, `CL=F`, `^VIX`), pour ne jamais mesurer un mouvement à cheval sur deux sources.

### 7.5 Secours

- `prolonge` : dès le premier échec de la source principale. Ajoute les dates postérieures à la dernière valeur enregistrée, après contrôle de l'écart à la dernière date commune (mêmes seuils ; au-delà : rien n'est ajouté). Statut `secours`. Au retour de la source principale, tout est remplacé par elle.
- `remplace` : après `secours.remplace_apres_echecs` (5) échecs planifiés consécutifs. La série entière, son unité, sa fréquence et sa note viennent du secours ; `catalogue.js` reflète le changement ; statut `secours`. Retour automatique à la source principale dès qu'elle répond.
- Sans secours : anciennes valeurs conservées, statut `erreur`, puis `en_retard` selon la fraîcheur.

### 7.6 Fusion, séries calculées, auxiliaires

- Le dépôt ne contient pas l'historique quotidien complet : le garde-fou compare donc, pour chaque série, le **nouvel historique mensuel à l'ancien** et le **nouveau récent à l'ancien**.
- Une série calculée n'est recalculée que si **toutes** ses entrées ont été obtenues aujourd'hui ; sinon elle garde ses valeurs et hérite du statut de l'entrée fautive. Les auxiliaires ne sont pas enregistrés. Une série calculée ne déclenche jamais d'alerte par elle-même.
- Les statistiques qui demandent 5 ans de données quotidiennes (« ce qui a bougé ») ne portent que sur les séries obtenues aujourd'hui ; l'entrée `cartes[id]` d'une série en échec est reprise telle quelle de l'ancien `resume.js`.

### 7.7 Fraîcheur et alerte

- Règle générale : J 5 jours ouvrables ; S 14 jours ; M 75 jours après la fin du mois ; T 125 jours après la fin du trimestre ; A 15 mois. Exceptions : colonne `retard` du §4 (jours calendaires après la fin de la période observée). Toujours sur `date_source` = dernière date de la série assemblée (principale + jours rapides), **avant** transformation.
- Compteur `echecs` : +1 si la série est en `erreur` lors d'une exécution `schedule` ; remis à 0 à chaque succès, quel que soit le déclencheur ; inchangé lors d'un échec manuel.
- `--alerte` sort en code 1 si une série (ou un jeu) de priorité E, non calculée, est en `erreur` avec `echecs ≥ 3`, ou `en_retard`. `non_disponible` et `secours` n'alertent jamais.
- Rapport de `--verifier` (30 lignes au plus) : une ligne de comptage par statut, puis les anomalies triées par gravité (`ALERTE` essentielle en erreur ou en retard, `ATTENTION` secondaire, raccord refusé, réponse tronquée, `INFO` saut anormal : variation supérieure à 10 écarts-types de la série).

---

## 8. Calculs

### 8.1 Qui calcule quoi

| Python (résultats dans `resume.js`, `previsions.js`, séries) | JavaScript |
|---|---|
| Unités, glissements annuels, écarts, croisés, % du PIB, dette en euros | Rééchantillonnage à la fréquence de la vue, alignement |
| Variations 1 mois et 1 an, percentiles, mini-courbes | Base 100 |
| « Ce qui a bougé », directions ▲▼▶, signaux d'inflation | Transformations par mode, r, seuil de fiabilité, classement |
| Statut QE/QT, jauges et leur historique | Corrélation glissante, bande, tableau des corrélations |
| Probabilité de récession (secours), agrégats des distributions SPF | Décalage, meilleur décalage |
| Fraîcheur, statuts, alerte | Composition des phrases, formats `fr-BE`, heure belge |

Aucune de ces formules n'existe des deux côtés. Seule exception assumée : la variation sur 12 mois existe en Python (séries enregistrées, cartes) et dans `stats.js` (mode « Rythmes annuels », à la fréquence de la vue) ; le relecteur vérifie leur accord sur une série mensuelle.

### 8.2 Cartes

- Dernière valeur : dernière observation de la série enregistrée (provisoire comprise). Série en glissement annuel dont la dernière observation brute n'a pas de glissement : afficher le dernier calculable et `note = "ga_base_manquante:<mois>"` ou `"ga_valeur_manquante:<mois>"`.
- Variations : `calculs.variations_1m_1a` sur la série native ; N avec une valeur ≤ 0 → `null`.
- Percentile (C8) : distribution = historique mensuel des mois complets, 30 ans au plus ; moins de 10 ans → `court` ; moins de 5 ans → pas de percentile. Pour N, la distribution est celle des variations sur 12 mois et la durée se compte sur cette distribution.

### 8.3 « Ce qui a bougé »

Candidats : séries J avec `mouvement: oui`, obtenues aujourd'hui, dont la dernière date est à moins de 7 jours de `donnees_au`. Exclus : famille A, J3_Q, séries calculées en doublon (IC_…, E4_…). Rapport = variation sur 7 jours calendaires ÷ écart-type des variations sur 7 jours des 5 dernières années (C6). On garde le plus grand rapport de chaque `groupe_mouvement` (`actions_us` G2-G4 ; `actions_europe` G1, G5-G8 ; `actions_asie` G9-G12 ; `petrole` H1, H2, H8 ; `or` H3, H9 ; `taux_us` B1-B3, H12, H13, BC_10A2A, BC_10A3M, DC_FED ; `taux_europe` B4, B5_2A, B5_10A, B9, H14, DC_BCE ; `inflation_us` D1-D3, H15 ; `dollar` I1, I6 ; les autres séries forment chacune leur groupe), puis les 5 plus grands au-dessus de 1,5. Aucun : `calme: true`. Le regroupement est un ajout au cahier des charges : sans lui les cinq lignes seraient cinq indices d'actions.

### 8.4 Signaux, QE/QT, jauges

- **Direction** (C7) : variation sur 3 mois comparée à 0,5 écart-type des variations historiques sur 3 mois.
- **Signaux d'inflation** :

| clé | zone euro | États-Unis | mesure |
|---|---|---|---|
| `brent_1a` | H1 | H2 | glissement annuel du niveau mensuel, direction en points |
| `gaz` | H4 | H5 | niveau, direction en % |
| `prix_production` | D9 | D8 | direction en points |
| `gscpi` | D10 | D10 | direction en points |
| `inflation_anticipee` | D5_LT (non évalué si la série n'existe pas) | D1 | direction en points |
| `salaires` | D12 | D11 | direction en points |
| `menages` | non évalué (aucune série) | D4 | direction en points |

  Synthèse : `baisse` si plus de la moitié des signaux évalués sont ▼, `hausse` si plus de la moitié sont ▲, sinon `partage`.
- **QE/QT** : dernière observation du bilan (F1-F4) comparée à l'observation trois mois plus tôt (tolérance 10 jours) ; > +1 % → `QE` ; < −1 % → `QT` ; sinon `stable`. La date de l'observation est affichée (F4 a 4 mois de retard).
- **% du PIB (F5)** : pour chaque trimestre q où le PIB des 4 derniers trimestres existe en entier, bilan = dernière observation du trimestre q. Aucun report d'un PIB ancien. Contrôle (test non bloquant) : écart inférieur à 2 points avec le ratio BIS `XDF_R_B1GQ` cité dans `docs/sources/F_banques_centrales.md`.
- **Jauges** : conditions du §8.4 du cahier des charges, avec ZE : C5, J2, J5, BC_IT_DE, J7, A2 ; US : C3, J1, J4, B1, J6, A1. Percentiles sur l'historique mensuel, 30 ans au plus, 10 ans au moins sinon « non évaluée ».
- **Historique des jauges** : pour chaque fin de mois t, chaque condition est évaluée avec les seules données connues à t ; le percentile est pris sur la fenêtre **qui se termine en t** (30 ans au plus, 10 ans au moins). Jamais sur l'historique complet : la courbe serait faussée par la connaissance du futur. Test dédié.

### 8.5 Probabilité de récession (secours de D14)

`BEY = 100 × 365 × d ÷ (360 − 91 × d)` avec `d = TB3MS ÷ 100` ; écart = `GS10 − BEY` ; `P(t + 12 mois) = Φ(−0,5333 − 0,6330 × écart(t))`. Vérifié sur le point d'octobre 2026 (4,05 → 4,1487 ; P = 12,4 %). Test : reproduire toute la colonne `Rec_prob` du fichier à 0,01 point près ; si le test échoue, pas de secours.

### 8.6 `config/reglages.yaml`

```yaml
recent_mois: 36
fraicheur: {J: 5, S: 14, M: 75, T: 125, A: 450}
garde_fou: {perte_max: 0.05, debut_plus_tard_jours: 45}
raccord: {N_pourcent: 2.0, T_points: 0.10}
secours: {remplace_apres_echecs: 5}
alerte: {echecs_planifies: 3}
percentile: {annees_max: 30, annees_court: 10, annees_min: 5, bornes: [10, 25, 75, 90]}
mouvement: {jours: 7, annees: 5, seuil: 1.5, nombre: 5}
direction: {mois: 3, part_ecart_type: 0.5}
anticipations: {seuil_points: 0.25}
qe_qt: {mois: 3, seuil_pourcent: 1.0}
jauges: {inflation_cible: 2.0, recul_3m: -0.5, percentile_stress: 90, percentile_ecart: 75,
         hausse_ecart_1m: 0.5, hausse_us10_1m: 0.75, taux_bas: 1.0, annees_min: 10, conditions_min_historique: 4}
saut_anormal: {ecarts_types: 10}
comparateur:
  max_courbes: 6
  points_min: 12
  seuils_force: [0.2, 0.4, 0.7]
  fiabilite_plancher: 0.2
  ecart_meilleur_decalage: 0.10
  couverture_min: 0.8
  fenetres: {S: 26, M_5A: 24, M_long: 36, T: 12}
  decalage_max_mois: 24
  epaisseurs: {gris: 1.5, faible: 2, modere: 3, fort: 4.5}
graphiques: {trou_max_jours: {J: 12, S: 15, M: 45, T: 135, A: 550}}
```

---

## 9. JavaScript

### 9.1 Fichiers (scripts classiques, un objet global chacun, chargés dans cet ordre)

| Fichier | Global | Rôle |
|---|---|---|
| `lib/chart.umd.min.js` | `Chart` | Chart.js 4.5.0 |
| `js/format.js` | `Format` | Nombres, dates, heure belge (`Intl`, `fr-BE`, `Europe/Brussels`), unités, ordinal « 85ᵉ » |
| `js/dom.js` | `Dom` | Création d'éléments (repris d'Aedifica, sans modules) |
| `js/donnees.js` | `Donnees` | Chargement par injection de `<script>`, cache, accès aux séries |
| `js/stats.js` | `Stats` | Existe |
| `js/graphiques.js` | `Graphiques` | Courbes, barres, mini-courbes SVG, greffons (réticule, événements, étiquettes de fin de trait) |
| `js/composants.js` | `Composants` | Carte, graphique de famille, panneau de fiche, jauge, bandeau d'état, sélecteur de période |
| `js/comparateur.js` | `Comparateur` | Page Comparateur |
| `js/pages.js` | `Pages` | Accueil, pages thématiques (générées depuis le catalogue), Comprendre, État des données |
| `js/blocs.js` | `Blocs` | Lot 3 : SPF, récession, signaux, FMI, jauges et historique, schéma des liens, courbe du pétrole |
| `js/fiches.js` | `window.FICHES` | Fiches ; **chargé au premier clic sur ⓘ** |
| `js/app.js` | — | Démarrage, navigation par `#/page`, stockage local (`try/catch`) |

Le cahier des charges ne cite que cinq fichiers JS ; les autres évitent un `app.js` de plusieurs milliers de lignes. Navigation GSM : barre inférieure « Accueil · Comparateur · Thèmes · Comprendre », « Thèmes » ouvrant la liste des 8 pages.

### 9.2 Chargement

- `app.js` injecte `data/etat.js?t=<horloge>` (jamais mis en cache), puis `catalogue.js` et `resume.js` avec `?v=<genere_le>`, puis affiche l'Accueil. Les fichiers de famille sont injectés à la demande avec le même `?v=`. Tout fonctionne en `file://` (le suffixe est ignoré).
- `Donnees.charger("taux_recent")` rend une promesse résolue sur `onload`, rejetée sur `onerror` (message « données non disponibles », jamais d'écran blanc).
- `Donnees.serie(id, vue)` : `vue = "native"` → `_recent` pour J et S, `_historique` pour M, T, A ; `vue = "mensuelle"` → `_historique` + point provisoire.
- Dates : toujours `Date.UTC` ; jamais `new Date("AAAA-MM-JJ")` en heure locale.

### 9.3 Graphiques

Axe linéaire en millisecondes, graduations maison reprises d'Aedifica (étendues à 30 ans et Max). Trois précautions :
1. **Ne pas reprendre la fonction `aligner` d'Aedifica** : elle reporte la dernière valeur connue, ce que la règle 1 interdit. Utiliser `Stats.aligner`.
2. **Pas de `spanGaps: true`.** `spanGaps` reçoit une durée en millisecondes, par série, selon sa fréquence native (`graphiques.trou_max_jours`) : un week-end ne coupe pas la courbe, un mois manquant (IPC américain d'octobre 2025) la coupe.
3. **Ne pas reprendre `alleger`** (un point sur n) : le nombre de points se règle par la fréquence de la vue.

Graphique de famille : 1 M et 1 A → données natives (`_recent`, ou `_historique` pour M, T, A) ; 5 A et plus → vue mensuelle. Grille commune `Stats.aligner(séries, "J" ou "M")` pour que l'infobulle en mode `index` montre toutes les séries à la même date. Bouton de période grisé si la série la moins fournie cochée a moins de 12 points (`Stats.pointsDansPeriode`). Axe % à gauche, niveaux à droite. Mini-courbes : SVG, sans Chart.js. Couleurs lues dans les variables CSS et relues au changement de thème. Événements : greffon qui trace les lignes de `catalogue.evenements` comprises dans la fenêtre.

### 9.4 Comparateur — enchaînement du calcul

```
entrée : ids, référence, période (ou dates libres), mode, décalages {id: k}, affichage
1. f = la plus lente entre Stats.frequencePourPeriode(période) et les fréquences natives de la sélection
2. données : f ∈ {J, S} → vue native ; f ∈ {M, T, A} → vue mensuelle
3. G = Stats.aligner(séries ENTIÈRES, f)             (grille régulière, C1)
4. [i0, i1] = indices de G dans la période ; i1 = dernière période où la référence a une valeur
5. x[id] = Stats.transformer(G.dates, valeurs, type, mode)      sur la grille entière
6. xd = Stats.decaler(x[id], k)
   r global   = Stats.pearson(x[ref][i0..i1], xd[i0..i1])       → Stats.classer
   glissante  = Stats.correlationGlissante(x[ref], xd, w)        sur la grille entière, puis découpe [i0..i1]
7. tracé : valeurs (ou base 100 calculée sur [i0..i1]), dessinées décalées de k
```

Conventions de `stats.js`, inchangées : Pearson sur les paires où les deux valeurs existent, 12 paires au moins ; seuil de fiabilité max(0,2 ; 2 ÷ √n) appliqué partout où un r colore ou s'affiche ; modes `mouvements` (N en %, T et N* en points), `rythmes` (N : variation sur 12 mois appariée par date ; T et N* : niveau), `niveaux` ; `decaler(valeurs, k)` place la valeur de t en t + k, donc k > 0 signifie que l'indicateur précède la référence ; meilleur décalage annoncé seulement s'il est fiable et gagne au moins 0,10 en |r|. Les réglages viennent de `catalogue.reglages.comparateur` ; `REGLAGES_DEFAUT` ne sert que de repli.

- Transformer **avant** de décaler, sur la grille entière : la première variation de la fenêtre existe, et la corrélation glissante est colorée dès le début de la période quand l'historique le permet. « Gris pointillé » seulement quand la fenêtre n'est pas complète (C2).
- Note « fuseaux horaires » : affichée en vue 1 M quand la sélection mélange au moins deux valeurs de `zone_horaire`.
- `w` : S → 26 ; M → 24 si la période fait 7 ans au plus, 36 au-delà ; T → 12 ; J (1 M) → pas de corrélation glissante.
- Décalage : borne = le plus petit entre 24 mois (104 semaines, 24 mois, 8 trimestres) et un tiers du nombre de points de la fenêtre. Pour k < 0 il n'existe pas de données après la fin : n diminue de |k|, et n est affiché dans l'infobulle du graphique « r selon le décalage ».
- Courbe décalée de k > 0 : la grille est prolongée de k périodes futures (`Stats.prolongerGrille`), zone légendée « ce que l'indicateur annonce ».
- Phrase du meilleur décalage : k > 0 → « X semble précéder Y d'environ k … » ; k < 0 → « X semble suivre Y d'environ |k| … » ; `annonce` faux → « Aucun décalage ne ressort nettement. »
- Dates libres : J si la durée est ≤ 92 jours et dans la fenêtre des fichiers récents ; S si ≤ 2 ans et dans cette fenêtre ; M sinon.
- Axes : une clé d'axe par unité après conversion (« base 100 » est une unité) ; plus de 3 clés → ajout refusé avec le message du cahier des charges.
- Segments colorés : `segment.borderColor`, `segment.borderWidth`, `segment.borderDash`, lus à l'indice `p1DataIndex` de la corrélation glissante. Bande de corrélation : un `<canvas>` calé sur `chart.chartArea`, mêmes couleurs.
- Étiquettes en bout de trait : nom court sur PC ; pastille numérotée sur GSM, reprise dans la légende.
- Ajout proposé : troisième affichage « Séries du calcul » (les séries transformées par le mode, par exemple le Brent en variation sur 12 mois), choisi par défaut par les comparaisons en mode « Rythmes annuels ». Sans lui, le bouton « Pétrole → inflation » montre un prix en dollars à côté d'un taux, alors que le lien calculé porte sur la variation du prix.
- Export : CSV construit en JavaScript (`Blob`), nombres sans séparateur de milliers, virgule décimale ; résumé texte dans le presse-papiers, zone de texte en repli.

### 9.5 Comparaisons prêtes à l'emploi (`config/comparaisons.yaml`)

| Bouton | référence | autres | mode | période | affichage |
|---|---|---|---|---|---|
| Pétrole → inflation zone euro | C5 | H1 | rythmes | 10A | séries du calcul |
| Inflation vs taux BCE vs Bund | C5 | A2, B4 | rythmes | 30A | valeurs |
| Bund vs immobilier coté européen | B4 | H11 | mouvements | 10A | valeurs |
| VIX vs S&P 500 | G2 | J1 | mouvements | 5A | valeurs |
| Dette et taux : Italie vs Allemagne | B8 | B4, E3T_IT, E3T_DE (fréquence trimestrielle) | rythmes | Max | valeurs |
| Bilan de la Fed vs Nasdaq | G4 | F1 | rythmes | Max | séries du calcul |
| Dollar vs or | H3 | I6 | mouvements | 10A | base 100 |
| Gaz TTF vs inflation Belgique | C7 | H4 | rythmes | 10A | séries du calcul |

Décalage initial 0 partout. Si l'affichage « séries du calcul » n'est pas retenu, ces boutons s'ouvrent en « valeurs ». Chaque configuration est testée à l'étape 3 : au moins 12 points et un r calculable.

---

## 10. GitHub

### 10.1 Workflow `.github/workflows/mise-a-jour.yml`

Versions majeures vérifiées le 22 novembre 2026 par l'API GitHub (`releases/latest`) : `actions/checkout` v7 (7.0.1), `actions/setup-python` v7 (7.1.0), `actions/configure-pages` v6 (6.0.0), `actions/upload-pages-artifact` v5 (5.0.0), `actions/deploy-pages` v5 (5.0.1). À revérifier le jour de l'écriture.

```yaml
name: Mise à jour des données
on:
  schedule:
    - cron: "17 5 * * *"
  workflow_dispatch:
  push:
    branches: [main]
    paths-ignore: ["docs/**", "**.md"]
permissions:
  contents: write
  pages: write
  id-token: write
concurrency:
  group: mise-a-jour
  cancel-in-progress: false
jobs:
  mise-a-jour:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: github-pages
      url: ${{ steps.deploiement.outputs.page_url }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        if: github.event_name != 'push'
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: scripts/requirements.txt
      - name: Dépendances
        if: github.event_name != 'push'
        run: pip install -r scripts/requirements.txt
      - name: Collecte
        if: github.event_name != 'push'
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: python scripts/collect.py --declencheur "${{ github.event_name }}"
      - name: Contrôle
        if: github.event_name != 'push'
        continue-on-error: true
        run: python scripts/collect.py --verifier
      - name: Aucune clé dans les fichiers produits
        if: github.event_name != 'push'
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: python scripts/verifier_cle.py --dossiers data docs
      - name: Enregistrement
        if: github.event_name != 'push'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/
          if git diff --cached --quiet; then
            echo "Aucun changement dans data/"
          else
            git commit -m "Mise à jour des données — $(TZ=Europe/Brussels date +%d/%m/%Y)"
            git pull --rebase origin main
            git push origin HEAD:main
          fi
      - name: Site
        run: |
          mkdir _site
          cp -r index.html robots.txt css js lib data _site/
      - uses: actions/configure-pages@v6
      - uses: actions/upload-pages-artifact@v5
        with:
          path: _site
      - id: deploiement
        uses: actions/deploy-pages@v5
      - name: Alerte
        if: github.event_name != 'push'
        run: python scripts/collect.py --alerte
```

- Sur `push` : ni Python ni collecte, seulement le redéploiement de `data/` tel qu'il est dans le dépôt.
- La clé n'est donnée qu'aux deux étapes qui en ont besoin. Si la clé est trouvée dans `data/` ou `docs/`, l'exécution s'arrête avant tout enregistrement.
- `collect.py` en mode normal sort toujours en code 0, même si des sources échouent (les données réussies doivent être publiées) ; seul `--alerte`, en dernière étape, peut marquer l'exécution en échec.
- Seuls `index.html`, `robots.txt`, `css`, `js`, `lib`, `data` sont publiés sur le site.
- `etat.js` change à chaque exécution : il y a donc un commit par jour, ce qui garde la planification active. À vérifier pendant la première semaine et à documenter dans le README.
- L'e-mail d'échec part vers le compte qui a écrit en dernier la ligne `cron` : pousser le workflow avec le compte de Georgy, et lui faire vérifier « Settings → Notifications → Actions ».

### 10.2 Mise en ligne (étape 3)

1. `python scripts/verifier_cle.py` (§10.3), puis `gh repo create tableau-marches --public --source . --push`.
2. Secret, sans afficher la clé (PowerShell) : `(Get-Content .env | Where-Object { $_ -match '^FRED_API_KEY=' }) -replace '^FRED_API_KEY=', '' | gh secret set FRED_API_KEY`.
3. Pages : `gh api --method POST repos/{owner}/{repo}/pages -f build_type=workflow`.
4. `gh workflow run "Mise à jour des données"`, `gh run watch`, contrôle de la date sur le site public ; vérifier qu'aucune seconde exécution n'a été déclenchée par le commit du robot.
5. `git pull`, puis comparaison série par série avec une collecte locale faite dans `cache/essai` (`--sortie`) : statut, dernière date, nombre de points. Toute série en `erreur` sur GitHub et `ok` en local est traitée avant de continuer (§12).

### 10.3 Vérification de la clé avant `git push`

`python scripts/verifier_cle.py` : lit la clé dans `FRED_API_KEY` ou `.env` ; cherche la chaîne exacte dans les fichiers suivis (`git ls-files`), dans `data/` et `docs/`, puis dans l'historique (`git log --all --oneline -S"<clé>"`) ; n'affiche que des noms de fichiers ou des identifiants de commit, jamais la clé ; code 1 si elle est trouvée, code 2 si aucune clé n'est disponible pour chercher. Installé aussi comme crochet local `.git/hooks/pre-push`. Équivalent manuel (Git Bash) :

```bash
CLE="$(sed -n 's/^FRED_API_KEY=//p' .env | tr -d '\r\n"')"
if [ -z "$CLE" ]; then echo "Clé absente de .env : vérification impossible"
elif { git grep -lF -e "$CLE" -- . ; git log --all --oneline -S"$CLE" ; } | grep -q . ; then echo "ARRÊT : clé trouvée"
else echo "Aucune clé"; fi
```

Avant le premier `git push` également : relire `AVANCEMENT.md` et `README.md` pour en retirer tout chemin du PC (règle 11) ; vérifier `git config user.email` (adresse « noreply »).

---

## 11. Découpage en lots

| Lot | Contenu | Terminé quand |
|---|---|---|
| 2a | `config.py`, les six YAML, corrections §2, `ecriture.py`, squelette de `collect.py` ; sources FRED, BCE, Eurostat ; séries des 12 cartes de l'Accueil non Yahoo | Collecte partielle déterministe (deux exécutions → fichiers identiques hors `etat.js`) |
| 2b | Autres modules de sources (ordre de risque : Yahoo, BoE, ONS, FMI, OCDE, BIS, fichiers, Bundesbank, MoF, BoJ, Banque mondiale) ; raccords, secours, séries calculées | Chaque série du §4 a un statut ; `docs/couverture.md` produit |
| 2c | `resume.py`, `previsions.py`, CSV, `verifier.py`, tests du §12 du cahier des charges et de ce plan | `--verifier` sans `ALERTE` non justifiée ; pytest et `node --test` verts |
| 2d | Relecteur « revue des calculs », corrections | Rapport traité |
| 3 (lot 1) | `index.html`, `format`, `dom`, `donnees`, `graphiques`, `composants`, `app` ; Accueil (cartes, « ce qui a bougé », bandeau), Comparateur complet, page Taux, État des données ; dépôt, secret, Pages, workflow ; comparaison GitHub / local ; vue GSM | Site public à jour, zéro erreur de console en `file://` et en ligne, **point d'arrêt Georgy** |
| 4 | Fiches par familles (une fiche par valeur de `fiche` + 15 fiches transversales) | `js/fiches.js` complet, incertitudes listées |
| 5 (lot 2) | Pages Inflation (cartes et graphiques), Croissance et dette, Banques centrales, Bourses, Énergie, Devises, Risques ; export CSV ; Comprendre (lexique, mode d'emploi, sources et mentions) | Toutes les pages affichent leurs cartes et graphiques de famille |
| 5 (lot 3) | Dans cet ordre : jauges (score), probabilité de récession, anticipations de taux, prévisions FMI, SPF, signaux d'inflation, historique des jauges, schéma des liens, courbe du pétrole | Chaque bloc livré ou annoncé absent |
| 6-8 | Captures, tests, relecture finale, remise | Checklist du §12 du cahier des charges |

Tests ajoutés par ce plan : grille régulière (C1) ; fenêtre glissante incomplète (C2) ; raccord refusé (C4) ; fraîcheur sur `date_source` et seuil trimestriel (C5) ; mouvement sur 7 jours avec une série 7 jours sur 7 (C6) ; direction trimestrielle (C7) ; secours `prolonge` et `remplace` ; compteur d'échecs (planifié seulement) ; série d'une source non publiée absente de `data/` ; jauge historique sans connaissance du futur ; somme et moyenne de 4 trimestres avec un trimestre manquant ; D14 contre le fichier ; somme SPF ≈ 100 ; semaine ISO → vendredi ; option `escalier`.

---

## 12. Risques et parades

| Risque | Parade |
|---|---|
| **Yahoo refuse les serveurs de GitHub (429, réponses vides)** | Un seul appel groupé, `threads=False` ; 3 essais espacés de 20, 60 et 180 s ; rattrapage code par code ; second passage en fin d'exécution ; anciennes valeurs conservées ; alerte seulement après 3 exécutions planifiées. Test à l'étape 3. Si l'échec est durable : second `cron` de rattrapage en fin de matinée qui ne collecte que les sources en échec, puis escalade à l'architecte (pistes non testées : `NASDAQCOM`, `NIKKEI225`, `SP500` sur FRED ; API gratuite à clé, à demander à Georgy) |
| Yahoo retire un code (cas `^V2TX`, `000300.SS`) | Statut `erreur`, alerte, remplaçant manuel du §4 |
| Banque d'Angleterre, ONS, STOXX, Fed de New York et de Philadelphie filtrent les robots ou les centres de données | `User-Agent` de navigateur (déjà dans `commun.session`), suivi des redirections, détection des pages HTML renvoyées à la place d'un CSV ; secours du §4 (A4 → BIS, B9 → FRED mensuel, C11 → FMI, E1_UK → OCDE). J2 n'a pas de secours : si STOXX bloque GitHub, J2 reste sur ses anciennes valeurs et la condition 2 de la jauge zone euro devient « non évaluée » |
| FMI et OCDE limitent le débit (429) | Un appel par indicateur ou par flux, attente longue, cadence hebdomadaire pour le WEO |
| Séries OCDE diffusées par FRED arrêtées sans préavis | Elles ne sont plus source principale que pour A5 et B12 ; fraîcheur surveillée ; secours BoJ pour A5 |
| Changement de version du jeu WEO (`9.0.0`) ou des classes de la SPF | WEO demandé en « dernière version » (`%2B`) ; classes SPF lues dans la réponse, jamais écrites en dur |
| Adresse du classeur de la Banque mondiale qui change chaque mois | Lien extrait de la page à chaque usage |
| Fausses alertes de fraîcheur | Exceptions du §4, fraîcheur sur `date_source`, cadence des jeux |
| Réponse tronquée ou série redéfinie par le fournisseur | Garde-fou ; `--forcer ID` après vérification humaine |
| Fuite de la clé FRED dans un message d'erreur | `nettoyer()` partout, test pytest dédié, `verifier_cle.py` dans le workflow et avant chaque `git push` |
| Deux mains dans `data/` | `--sortie cache/essai` en local ; `git pull --rebase` dans le workflow ; `concurrency` |
| Dépôt qui grossit | Une ligne par série, écriture seulement si le contenu change, CSV limité aux mois complets. Ordre de grandeur : 1,5 Mo réécrit par jour avant compression ; à surveiller après un mois |
| Accueil lent sur GSM | Trois petits fichiers au démarrage, fiches et familles à la demande, mini-courbes en SVG |
| Couleurs de corrélation instables | Seuil de fiabilité par fenêtre, couverture minimale, pas de corrélation glissante en vue 1 M |
| Conditions de rediffusion | §5 ; décisions de Georgy avant le premier `git push` |

---

## 13. À signaler à Georgy (sans attendre de réponse)

- **B11 (Chine 10 ans, essentiel) : non disponible.** Aucune source gratuite et documentée ; le seul accès trouvé est un point d'entrée interne et non documenté du site chinois CFETS, écarté.
- **G5 Euro Stoxx 50** : historique depuis mars 2007 seulement. **G11** : remplacé par un ETF qui suit le CSI 300. **D13 zone euro** : remplacé par l'Allemagne et par l'agrégat des 4 grandes économies européennes.
- **Inflation en zone euro et par pays** : depuis 1997 (début de l'indice harmonisé).
- **J6-J7** : écart de crédit calculé par la Fed (méthode Gilchrist-Zakrajšek) pour les États-Unis ; pour la zone euro, une composante de l'indice de stress de la BCE, qui n'est qu'une approximation.
- **Probabilités de la BCE** : la phrase donnera trois chiffres (sous 1,8 %, proche de 2 %, au-dessus de 2,2 %), les classes de l'enquête ne permettant pas de dire exactement « sous 2 % ».
- **Événement récent à valider** : 5 novembre 2026, forte chute des valeurs liées à l'intelligence artificielle (VIX de 16,6 à 28,2 en un jour), proposé dans `docs/sources/J_risques.md`.
- Une clé gratuite EIA n'est utile que si la courbe à terme du pétrole (D15) ne peut pas venir de Yahoo.

---

## Questions pour Georgy

1. **Cours de bourse et de marché (Yahoo Finance, et VSTOXX du site STOXX).** Leurs conditions n'autorisent pas clairement la collecte automatique ni la republication. Sans eux il n'y a plus ni bourses, ni ETF, ni or, ni gaz, ni cuivre, ni indice du dollar, ni Aedifica, et la moitié des cartes de l'Accueil disparaît. Je recommande de les publier avec mention de la source, sur un site personnel, non commercial et non indexé, en sachant que c'est une zone grise. **D'accord, ou préfères-tu que je les retire ?**
2. **FRED (environ 35 séries : taux américains, inflation américaine, VIX, pétrole…).** Ses conditions actuelles interdisent d'enregistrer ses données et de les redistribuer sans accord écrit, alors que toute l'application repose sur ce principe (elles permettent en revanche de créer une application avec une partie de ses données). Je te prépare un court message à envoyer à FRED pour demander cet accord. **Préfères-tu mettre en ligne tout de suite avec les mentions exigées, quitte à retirer ces séries en cas de refus (ce que je recommande), ou attendre la réponse de FRED avant toute mise en ligne ?**
3. **FMI et BIS (prévisions, dette et déficit de tous les pays, inflation japonaise, taux chinois et suisse, bilan de la Banque d'Angleterre), ainsi que le VIX, l'enquête de l'Université du Michigan et les données japonaises reprises par FRED.** Leur réutilisation non commerciale est permise à condition de citer la source. Je recommande de les publier avec cette mention. **D'accord ?**
