# Famille F — Banques centrales (QE/QT) et masse monétaire

Tests réalisés le 22 novembre 2026. Aucun code FRED testé avec clé : tous les appels FRED ci-dessous sont sans clé (`fredgraph.csv`, même contenu que l'API). Colonnes CSV FRED : `observation_date,<CODE>` ; valeur manquante = cellule vide ou `.` (à gérer au parsing).

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| F1 | Bilan de la Fed | FRED `WALCL` (Fed, H.4.1) | `WALCL` OK | 2002-12-18 | 2026-11-18 (6 741 452) | hebdo, mercredi | BIS `WS_CBTA` US (mensuel, depuis 1914) | oui (domaine public) | Unité : **millions USD**. Pas avant 2002 : pour 1990-2002 utiliser BIS (mensuel, milliards USD). |
| F2 | Bilan de la BCE (Eurosystème) | BCE direct `ILM` (retenue, rediffusion claire) ; FRED `ECBASSETSW` identique | `ECBASSETSW` OK ; `ILM.W.U2.C.T000000.Z5.Z01` OK | 1999-01-01 (1999-W01) | 2026-11-13 (2026-W46) : 5 906 258 | hebdo (vendredi) | FRED `ECBASSETSW` ↔ BCE ; BIS `WS_CBTA` XM | oui avec citation de la BCE (FRED : « copyrighted: citation required », reprint with permission) | Unité : **millions EUR**. Mêmes valeurs FRED/BCE (vérifié sur la dernière semaine). Composition changeante (élargissements de la zone). Date BCE = « AAAA-Wss » (semaine ISO) à convertir en vendredi. |
| F3 | Bilan de la Banque du Japon | FRED `JPNASSETS` (BoJ) | `JPNASSETS` OK | 1998-04-01 | 2026-10-01 (6 261 882) | **mensuelle**, fin de période (date = 1er du mois) | BIS `WS_CBTA` JP (mensuel, 1953-, jusqu'à 2026-07) | restreinte (FRED : « Copyright, Bank of Japan », citation obligatoire) | Unité : **100 millions de yens** (6 261 882 = 626 188,2 milliards de yens). BIS : milliards de yens (644 295,7 en 2026-07 ; concordance avec FRED). Pas de fichier BoJ natif testé. |
| F4 | Bilan de la Banque d'Angleterre | **BIS `WS_CBTA` GB** (retenue) | IADB `RPWB55A` = **faux** (billets en circulation) ; `RPWB75A` OK mais s'arrête 24/09/2014 ; `RPQB75A` OK mais trimestriel, s'arrête 30/06/2025 ; BIS OK | 1844-09 (1990-01 utile) | 2026-07 (805,29 Md GBP) ; trimestriel jusqu'à 2026-Q2 | mensuelle (retard ≈ 4 mois) | IADB `RPQB75A` (trimestriel, 2013-09→2025-06, M£) ; `RPWB75A` (hebdo 2006-05→2014-09, M£) | restreinte / inconnue pour BIS (voir ci-dessous) | Unité BIS : **milliards GBP** (UNIT_MULT 9). Les nouvelles séries hebdo du Weekly Report (depuis 2014) n'ont pas de total dans l'IADB. Raccord BIS = BoE Weekly Report depuis 09/2013, séries hebdo avant. FRED `BOEBSTAUKA` = annuel en % du PIB, s'arrête en 2016 : inutilisable. |
| F5 | Bilans en % du PIB (calcul) | calcul F1/F2/F3/F4 ÷ PIB | — | — | — | trimestrielle (PIB) | **BIS `WS_CBTA` unité `XDF_R_B1GQ`** (ratio déjà calculé, US/JP/GB/XM) | idem F4 | Voir « Aide à F5 » ci-dessous. |
| F6 | M2 États-Unis | FRED `M2SL` | `M2SL` OK | 1959-01-01 | 2026-09-01 (23 413,9) | mensuelle, désaisonnalisée | — (aucun besoin) | oui (domaine public, Fed H.6) | Unité : **milliards USD**, CVS. Croissance annuelle à calculer (valeur / valeur 12 mois avant − 1). Publié début de mois suivant+1 (retard ~ 1 mois). |
| F7 | M3 zone euro, croissance annuelle | BCE `BSI.M.U2.Y.V.M30.X.I.U2.2300.Z01.A` | OK | 1981-01 (10,188 %) | 2026-09 (3,504 %, statut P = provisoire ; 2026-08 : 3,494 %) | mensuelle | — | oui avec citation de la BCE | Unité : **% annuel** (type T). Composition changeante. Dernier point provisoire (`OBS_STATUS=P`), peut être révisé. |

## Appels exacts qui ont fonctionné

Tous en GET simple, sans clé, sans en-tête spécial (sauf mention).

- **F1** : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL` (1 249 lignes).
- **F2** : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBASSETSW` (1 455 lignes, valeurs avec décimales `.00000000`).
  Secours/primaire BCE : `https://data-api.ecb.europa.eu/service/data/ILM/W.U2.C.T000000.Z5.Z01?format=csvdata&startPeriod=1999-01-01` (colonnes utiles : `TIME_PERIOD` ex. `2026-W46`, `OBS_VALUE`, `UNIT=EUR`, `UNIT_MULT=6`). Clé : `ILM.W.U2.C.T000000.Z5.Z01` = Eurosystème, total de l'actif/passif, toutes devises.
- **F3** : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=JPNASSETS` (343 lignes).
  Secours : `https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBTA/1.0/M.JP.*.*.*.*?format=csv` (filtrer `UNIT_MEASURE=XDC`, `TRANSFORMATION=B`).
- **F4** (BIS, retenue) : `https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBTA/1.0/*.GB.*?format=csv`. Filtrer `FREQ=M`, `UNIT_MEASURE=XDC`, `TRANSFORMATION=B` (monnaie nationale, milliards, corrigée des ruptures) → `TIME_PERIOD` (AAAA-MM), `OBS_VALUE`. La colonne `DATA_COMP` indique la chaîne de sources (BoE Weekly Report depuis 09/2013).
  Séries IADB testées (User-Agent navigateur non nécessaire, mais harmless) :
  `https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now&SeriesCodes=RPQB75A&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N` (format `DATE,CODE` avec dates « 30 Sep 2013 », M£). Mêmes appels pour `RPWB75A` (hebdo, 2006-05-24 → 2014-09-24). Un code inexistant renvoie une page HTML « Object moved » (pas une erreur HTTP) : à détecter.
- **F5 (aide)** : `https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBTA/1.0/Q.US+JP+XM+GB.*.*.*.*?format=csv`, filtrer `UNIT_MEASURE=XDF_R_B1GQ` (% du PIB, trimestriel : US 1947-Q4, JP 1956-Q1, GB 1955-Q4, XM 1998-Q4 ; dernier US/JP/GB 2026-Q2 = 21,2 / 94,4 / 25,8 %, XM 2026-Q1 = 39,0 %).
- **F6** : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL` (813 lignes).
- **F7** : `https://data-api.ecb.europa.eu/service/data/BSI/M.U2.Y.V.M30.X.I.U2.2300.Z01.A?format=csvdata` (549 lignes ; colonnes `TIME_PERIOD`, `OBS_VALUE`, `OBS_STATUS`).

## Unités (indispensable pour F5)

| série | unité source | pour obtenir des milliards de monnaie locale |
|---|---|---|
| F1 `WALCL` | millions USD | ÷ 1 000 |
| F2 `ECBASSETSW` / ILM | millions EUR | ÷ 1 000 |
| F3 `JPNASSETS` | **100 millions de yens** | × 0,1 (6 261 882 → 626 188 milliards de yens) ; ÷ 10 000 pour des milliers de milliards |
| F4 BIS GB | milliards GBP | déjà en milliards (IADB : millions) |
| F6 `M2SL` | milliards USD | déjà en milliards |
| F7 | % annuel | — |

Le PIB (F5) vient d'une autre famille : vérifier ses unités (FRED `GDP` US en milliards USD, annualisé, trimestriel ; PIB japonais en 100 M¥ ou milliards ¥ selon la source). Le plus simple et cohérent : reprendre les ratios BIS `XDF_R_B1GQ` ou diviser par un PIB nominal annualisé.

## Points d'attention

- **Fréquences mixtes** : F1/F2 hebdo, F3/F4/F6/F7 mensuel ; F5 sera au plus trimestriel. Les dates de F3 sont des débuts de mois pour une valeur de fin de mois.
- **Retards** : F4 (BIS) à fin juillet 2026 (≈ 4 mois) ; F3 FRED à fin octobre. F4 ne peut pas être « essentiel à jour » : prévoir un seuil de fraîcheur de ~5 mois (priorité S).
- **Rediffusion publique** : F1 et F6 domaine public ; F2, F7 BCE : reproduction autorisée avec mention de la source (à citer) ; F3 BoJ via FRED « citation required » ; F4/BIS : conditions BIS non lues en détail → classée « inconnue / à vérifier » (les données BIS sont généralement réutilisables avec citation, mais le texte exact n'a pas été validé). À arbitrer par Georgy si l'on veut rester strict.
- **Mention FRED** : citation conseillée « Source : Board of Governors of the Federal Reserve System, retrieved from FRED, Federal Reserve Bank of St. Louis » ; les termes d'utilisation de l'API FRED précisent que les séries marquées « Copyright » dans leurs notes (JPNASSETS, ECBASSETSW) restent soumises aux droits de leur propriétaire.
- Aucune clé API utilisée ni écrite dans ce fichier. Scripts et téléchargements : répertoire temporaire du scratchpad `F/`.
