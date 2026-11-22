# Famille D — Anticipations et signaux avancés : sources testées

Test réalisé le 22 nov. 2026. Aucune clé API utilisée (FRED testé via `fredgraph.csv`, sans clé). Pour les adresses FRED, la clé sera ajoutée plus tard côté code (jamais dans ce fichier).

## Tableau de synthèse

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Point mort d'inflation US 5 ans | FRED | `T5YIE` | 2003-01-02 | 2026-11-20 (2,18) | quotidienne | — | oui (données Fed/Trésor) | OK. Pas de données avant 2003. Jours fériés = cellule vide (256 vides). |
| D2 | Point mort US 10 ans | FRED | `T10YIE` | 2003-01-02 | 2026-11-20 (2,15) | quotidienne | — | oui | OK, mêmes particularités que D1. |
| D3 | 5 ans dans 5 ans | FRED | `T5YIFR` | 2003-01-02 | 2026-11-20 (2,12) | quotidienne | — | oui | OK. |
| D4 | Inflation attendue ménages US | FRED | `MICH` | 1978-01-01 | 2026-10-01 (4,7) | mensuelle | — | restreinte (droit d'auteur Univ. du Michigan : citer la source, ne pas republier en masse ; à trancher) | OK. Octobre 2025 présent (4,6) : pas de trou. |
| D5 | Zone euro — distribution de probabilité d'inflation (SPF BCE) | Portail BCE, jeu `SPF` | `SPF/Q.U2.HICP.<classe>.<horizon>.Q.AVG` | 1999-Q1 | enquête 2026-Q4 (publiée le 30 oct. 2026) | trimestrielle | page BCE `table_3_2026q4.en.html` (tableau HTML, mêmes valeurs) ; saisie manuelle | oui (BCE : reproduction autorisée avec mention de la source) | OK, voir section D5 (piège : `PFC` n'est PAS la probabilité). Prochaine enquête : 5 févr. 2027 (provisoire). |
| D6 | États-Unis — distribution de probabilité (SPF Fed de Philadelphie) | Fed de Philadelphie | `prob.xlsx`, onglets `PRCCPI` (IPC cœur) et `PRCPCE` (PCE cœur) | 2007-Q1 | enquête 2026-Q4 (fichier mis à jour le 16 nov. 2026) | trimestrielle | — | oui (données publiques, citer la source) | OK, voir section D6. Seulement inflation cœur (pas d'IPC total). |
| D7 | Prévisions d'inflation du FMI (WEO) | **API SDMX du FMI** `api.imf.org` (jeu `IMF.RES,WEO,9.0.0`) | `USA+G163+BEL+...PCPIPCH.A` | 1980 (selon pays) | édition **octobre 2026** (publiée le 13 oct. 2026), prévisions jusqu'en 2031 | annuelle | DataMapper `/external/datamapper/api/v1/` : **en panne le 22 nov.** (voir section D7) | restreinte (« © FMI, tous droits réservés », conditions imf.org/external/terms.htm ; usage non commercial avec citation ; à trancher) | Zone euro = `G163` (pas `EURO`). |
| D8 | US prix à la production | FRED | `PPIACO` (aussi `PPIFIS`) | 1913-01-01 (`PPIFIS` : 2009-11) | 2026-10-01 (`PPIACO` 293,921) | mensuelle | `PPIFIS` | oui (BLS) | Série en **niveau d'indice** : calculer le glissement annuel en Python (oct. 2026 vs oct. 2025 = +12,8 %). Octobre 2025 présent. |
| D9 | Zone euro prix à la production industrielle | Eurostat | `sts_inppd_m` : `M.PRC_PRR_DOM.B-E36.NSA.PCH_SM.EA20` | 1996-01 (EA20) | 2026-09 (11,1 %) | mensuelle | BCE | oui (Eurostat, CC BY 4.0) | Glissement annuel déjà calculé (`PCH_SM`). `EA21` aussi disponible (depuis 2001-01, même dernière valeur). Dernière mise à jour du jeu : 21 nov. 2026. |
| D10 | GSCPI | Fed de New York | `gscpi_data.xlsx` | 1998-01 | 2026-10 (1,262) | mensuelle | — | oui (données publiques, citer la source) | Fichier nommé .xlsx mais **ancien format .xls** (OLE) : lire avec `xlrd`/`pandas` (pas `openpyxl`). |
| D11 | US salaire horaire moyen | FRED | `CES0500000003` | 2006-03-01 | 2026-10-01 (38,00 $) | mensuelle | — | oui (BLS) | **Niveau en dollars** : calculer le glissement annuel. Octobre 2025 présent (36,85). |
| D12 | Zone euro salaires négociés | BCE, jeu `INW` | `INW/Q.U2.N.INWR.000000.4F0.GY.IX` | 1991-Q1 | 2026-Q3 (2,57 %) | trimestrielle | `EWT` (ECB wage tracker, prévisions jusqu'en 2027) ; ancien jeu `STS` s'arrête à 2025-Q3 | oui (BCE) | La clé `STS/Q.I9.N.INWR...` est **périmée** (dernier point 2025-Q3). Utiliser `INW`. |
| D13 | OCDE CLI | API OCDE (`sdmx.oecd.org`) | `OECD.SDD.STES,DSD_STES@DF_CLI` | 1955-01 (US) | 2026-10 (US 100,96) | mensuelle | FRED `USALOLITOAASTSAM` (US OK, 2026-10) | oui (OCDE, CC BY 4.0) | Pas d'agrégat zone euro (voir section D13). |
| D14 | Probabilité de récession US à 12 mois | Fed de New York | `allmonth.xls` (feuille `rec_prob`) | 1960-01 | spread observé jusqu'à 2026-10 ; probabilité calculée pour 2027-10 : **12,4 %** | mensuelle | calcul FRED `GS10`/`TB3MS` | oui (citer la source) | Formule **vérifiée** (voir section D14). Fichier .xls ancien format. |
| D15 | Courbe à terme du pétrole | Yahoo Finance | contrats mensuels `BZK27.NYM` etc. | contrat par contrat | 2026-11-20 | quotidienne | EIA STEO (clé facultative, non testée) | restreinte (Yahoo : usage personnel ; données CME/NYMEX) | Fonctionne mais fiabilité moyenne (voir section D15). |

## Séries FRED (D1-D4, D8, D11)

Appel exact (sans clé) : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<CODE>`
Format : CSV, deux colonnes `observation_date,<CODE>` (ou `DATE`), dates ISO. Valeur manquante = cellule **vide** (pas de point « . »). Pas de trou pour octobre 2025 sur `MICH`, `PPIACO`, `PPIFIS`, `CES0500000003` (valeurs présentes), contrairement à ce qu'on pourrait attendre. À confirmer avec l'API officielle une fois la clé disponible. Pour D1-D3 les jours sans cotation sont vides.
Rediffusion : FRED exige sa mention propre (« This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis ») ; `MICH` porte en plus le droit d'auteur de l'Université du Michigan.

## D5 — SPF BCE, distributions de probabilité (zone euro)

Portail de données BCE, jeu `SPF`. Dimensions de la clé (7) : `FREQ.REF_AREA.FCT_TOPIC.FCT_BREAKDOWN.FCT_HORIZON.SURVEY_FREQ.FCT_SOURCE`.

Appel exact qui fonctionne (CSV, toutes les classes d'un horizon, depuis 2026-Q3 par exemple) :
`https://data-api.ecb.europa.eu/service/data/SPF/Q.U2.HICP..2027.Q.AVG?startPeriod=2026-Q3&format=csvdata`
(`Q.U2.HICP..<horizon>.Q.AVG` : le champ classe est laissé vide pour les avoir toutes ; il faut **exactement** 7 champs, sinon la BCE renvoie une page HTML « Your access has been blocked… » avec le code 400.)

- `FCT_TOPIC=HICP` (inflation totale ; `CORE` = inflation cœur).
- `FCT_HORIZON` : `2026` (année en cours), `2027` (N+1), `2028` (N+2), `LT` (long terme, = 2031 pour cette enquête). Les horizons glissants (`P12M`, etc.) existent en fréquence `A`/`M`, non utilisés ici.
- **`FCT_SOURCE=AVG` = probabilité moyenne (en %) attribuée à la classe** (c'est la bonne série). `NUM` = nombre de réponses ; `PFC` = nombre de prévisions ponctuelles dans la classe (**ne pas utiliser**, somme ≠ 100) ; codes à 3 chiffres = répondants individuels.
- `FCT_BREAKDOWN=POINT` en `AVG` = prévision ponctuelle moyenne (à exclure du histogramme ; la somme `AVG` de toutes les lignes vaut ~102 parce qu'elle l'inclut).
- Classes actuelles (13, largeur 0,5 point, nombres décimaux avec « _ » et `N` = négatif) : `TN0_8` (< −0,8) ; `FN0_7TN0_3` (−0,7 à −0,3) ; `FN0_2T0_2` (−0,2 à 0,2) ; `F0_3T0_7` ; `F0_8T1_2` ; `F1_3T1_7` ; `F1_8T2_2` ; `F2_3T2_7` ; `F2_8T3_2` ; `F3_3T3_7` ; `F3_8T4_2` ; `F4_3T4_7` ; `F4_8` (≥ 4,8). Les bornes sont **inclusives et jointives par pas de 0,1** (ex. 1,8 à 2,2 puis 2,3 à 2,7), et l'ensemble somme à 100.
- Autres codes `F...` (ex. `F2_0T2_4`, `F1_5T1_9`) = classes **d'une autre grille** utilisées dans les séries `PFC`/anciennes enquêtes : à ignorer pour l'affichage actuel. Les classes ont changé dans le temps : pour un historique propre, ne comparer que des classes présentes à chaque date ; les valeurs absentes ne sont pas des zéros.
- Dernière enquête : **2026-Q4**, publiée le 30 oct. 2026 (page `https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/ecb.spf2026q4.en.html`). Valeurs 2026-Q4, vérifiées identiques à la table officielle `.../html/table_3_2026q4.en.html` :

| classe | 2026 | 2027 | 2028 | LT |
|---|---|---|---|---|
| < −0,8 | 0,1 | 0,1 | 0,4 | 0,6 |
| −0,7 à −0,3 | 0,1 | 0,3 | 0,7 | 0,8 |
| −0,2 à 0,2 | 0,2 | 0,6 | 1,4 | 1,7 |
| 0,3 à 0,7 | 0,4 | 1,1 | 3,4 | 3,8 |
| 0,8 à 1,2 | 0,6 | 2,3 | 8,3 | 7,5 |
| 1,3 à 1,7 | 1,2 | 6,9 | 18,1 | 16,5 |
| 1,8 à 2,2 | 2,6 | 15,5 | 32,1 | 33,8 |
| 2,3 à 2,7 | 16,4 | 28,8 | 20,4 | 19,5 |
| 2,8 à 3,2 | 53,0 | 23,8 | 8,0 | 8,0 |
| 3,3 à 3,7 | 19,6 | 12,4 | 4,0 | 4,1 |
| 3,8 à 4,2 | 4,3 | 5,3 | 1,8 | 2,1 |
| 4,3 à 4,7 | 1,3 | 2,1 | 0,9 | 1,2 |
| ≥ 4,8 | 0,3 | 0,7 | 0,6 | 0,6 |

Moyennes ponctuelles : 3,0 (2026), 2,6 (2027), 2,0 (2028), 2,0 (LT). Nombre de réponses : 51, 51, 47, 38.
Exemple de phrase (§8.3) : part sous 2 % en 2027 = classes jusqu'à 1,8 à 2,2 incluse (0,1+0,3+0,6+1,1+2,3+6,9+15,5 = 26,8 %) ; attention : la classe 1,8 à 2,2 chevauche le seuil de 2 %, à préciser dans la phrase (par ex. « sous 2,3 % » ou « environ 2 % »).
Format : valeurs décimales avec point, `TIME_PERIOD` = `AAAA-Qn`, colonne `OBS_VALUE`. Valeurs manquantes : ligne absente.
Autres fichiers BCE (secours) : `https://www.ecb.europa.eu/stats/prices/indic/forecast/shared/files/data_aggregates_publication.xlsx` et `.../SPF_individual_forecasts_by_round.zip` (adresses lues sur la page `all_data.en.html`, non téléchargées) ; la table HTML `table_3_2026q4.en.html` donne les mêmes pourcentages.

## D6 — SPF de la Fed de Philadelphie (États-Unis)

- Page : `https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/probability-variables` (« last update: November 16, 2026 »).
- Fichier : `https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/survey-of-professional-forecasters/historical-data/prob.xlsx` (appel direct réussi, 181 Ko, vrai .xlsx, il faut un en-tête `User-Agent` ordinaire).
- Onglets : `PRGDP`, `PRPGDP`, `PRUNEMP`, `PRCCPI` (IPC cœur), `PRCPCE` (PCE cœur), `RECESS`. Pas d'IPC total ni de PCE total.
- `PRCCPI`/`PRCPCE` : colonnes `YEAR`, `QUARTER`, puis 20 colonnes `PRCCPI1..PRCCPI20`. Colonnes 1-10 = année en cours, 11-20 = année suivante ; ordre des 10 classes (variation T4/T4, en %) : 1 = 4,0 ou plus ; 2 = 3,5-3,9 ; 3 = 3,0-3,4 ; 4 = 2,5-2,9 ; 5 = 2,0-2,4 ; 6 = 1,5-1,9 ; 7 = 1,0-1,4 ; 8 = 0,5-0,9 ; 9 = 0,0-0,4 ; 10 = « sera en baisse » (< 0). Source : documentation `spf-documentation.pdf`, tableau 8 (valable de 2007-Q1 à aujourd'hui). Les probabilités somment 100.
- Données manquantes : texte `#N/A` (avant 2007-Q1) ; à convertir en vide.
- Dernière enquête : 2026-Q4. Core CPI 2026 : 1,7 / 6,7 / 21,6 / **57,2** / 10,7 / 1,8 / 0,2 / 0 / 0 / 0 (la classe 4, 2,5-2,9 %, domine). Fichier lu avec `pandas`/`openpyxl` (avertissement bénin sur l'en-tête de page).
- Seuil de 2 % : « sous 2,0 % » = classes 6 à 10 ; la classe 5 (2,0 à 2,4) est au-dessus du seuil.

## D7 — Prévisions du FMI (WEO)

- **Le point d'accès DataMapper `https://www.imf.org/external/datamapper/api/v1/PCPIPCH/USA` ne fonctionne pas le 22 nov. 2026** : `403 Access Denied` avec un User-Agent de navigateur, et avec un client Python `404 {"error":"Blob not found"}` (y compris pour `/indicators` et `/countries`), parfois `429` (limite de débit). Plusieurs essais sur 1 minute : même résultat. Ne pas s'appuyer dessus.
- **Appel retenu qui fonctionne** (nouveau portail IMF, SDMX 2.1) :
  `https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO,9.0.0/USA+G163+BEL+DEU+FRA+ITA+ESP+NLD+CHN+JPN+GBR+CHE.PCPIPCH+NGDP_RPCH.A?startPeriod=2023&endPeriod=2031` avec l'en-tête `Accept: text/csv` (ou `application/json`).
- Colonnes CSV utiles : `COUNTRY`, `INDICATOR`, `TIME_PERIOD` (année), `OBS_VALUE`, `LATEST_ACTUAL_ANNUAL_DATA` (2025 pour tous : les années ≥ 2026 sont des prévisions), `PUBLICATION_DATE` (2026-10-13), `LICENSE`.
- Codes pays : `USA`, `BEL`, `DEU`, `FRA`, `ITA`, `ESP`, `NLD`, `CHN`, `JPN`, `GBR`, `CHE` ; **zone euro = `G163`** (`EURO` est rejeté/absent).
- Indicateurs : `PCPIPCH` = inflation IPC, moyenne annuelle, variation en % ; `NGDP_RPCH` = croissance du PIB réel (utile pour E2).
- Édition : **octobre 2026** (jeu `WEO` version 9.0.0). Les éditions antérieures sont dans des jeux « vintage » : `WEO_2026_APR_VINTAGE`, `WEO_2025_OCT_VINTAGE`. Mise à jour par pays : 24-30 sept. 2026.
- Inflation (%), prévisions 2026/2027/2028 : USA 3,65/2,83/2,11 ; G163 3,06/2,82/2,16 ; BEL 3,79/2,90/2,08 ; DEU 2,71/3,12/1,95 ; FRA 2,41/2,24/1,88 ; GBR 3,25/2,80/2,00 ; JPN 1,95/2,55/2,00 ; CHN 1,03/1,36/1,64.
- Rediffusion : « © Fonds monétaire international, tous droits réservés » ; usage non commercial autorisé avec citation (`https://www.imf.org/external/terms.htm`) ; à faire trancher par Georgy. Citation suggérée par le FMI : « International Monetary Fund. World Economic Outlook (WEO), https://data.imf.org/en/datasets/IMF.RES:WEO ».

## D10 — GSCPI

`https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx` (252 Ko, en-tête `User-Agent` ordinaire). Fichier **réellement au format Excel 97-2003 (.xls)** malgré l'extension : `pandas.read_excel(..., engine="xlrd")`. Une seule feuille `GSCPI Monthly Data` : lignes 1 à 5 d'en-tête et vides, puis colonnes `Date` (texte `31-Jan-1998`, fin de mois) et `GSCPI` (écarts-types par rapport à la moyenne ; 0 = normal). 1998-01 → 2026-10 (1,2619), sans trou.

## D12 — Salaires négociés BCE

Appel exact : `https://data-api.ecb.europa.eu/service/data/INW/Q.U2.N.INWR.000000.4F0.GY.IX?format=csvdata` (143 points, 1991-Q1 → 2026-Q3 : 2,57 %). Colonnes `TIME_PERIOD` (`AAAA-Qn`), `OBS_VALUE`. Les séries `Q.I9...` (zone euro à 20) s'arrêtent à 2025-Q4 ; `U2` = zone euro composition changeante (à 21 pays, avec la Bulgarie depuis 2026) est à jour. L'ancienne clé `STS/Q.I9.N.INWR.000000.3.ANR` s'arrête à **2025-Q3** : ne pas l'utiliser. Complément : jeu `EWT` (« ECB wage tracker »), ex. `EWT/Q.U2.N.WT.INWR._T.4F0.GY`, 2013-Q1 → 2027-Q3 (prévisions) ; il ne reproduit pas exactement l'indicateur INW.

## D13 — Indicateurs avancés OCDE (CLI)

Appel exact (CSV, tous les pays utiles) :
`https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI/USA+CHN+JPN+GBR+DEU+FRA+ITA+G4E+G7.M.LI...AA...H` avec l'en-tête `Accept: application/vnd.sdmx.data+csv`. Clé = `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.ADJUSTMENT.TRANSFORMATION.TIME_HORIZ.METHODOLOGY` (ici `.M.LI...AA...H` = mensuel, CLI, ajusté amplitude, méthode H).
Résultats : USA 1955-01 → 2026-10 (100,96) ; CHN 1992-05 → 2026-10 ; JPN 1959-01 → 2026-10 ; GBR 1957-12 → 2026-10 ; DEU/FRA/ITA 2026-10 (101,16 / 100,73 / 100,04). Colonnes `REF_AREA`, `TIME_PERIOD` (`AAAA-MM`), `OBS_VALUE` (100 = tendance).
**Zone euro : non disponible.** `EA19`, `EA20`, `EA` ne renvoient rien ; la liste des zones disponibles est : A5M, AUS, BRA, CAN, CHN, DEU, ESP, FRA, G20, G4E, G7, GBR, IDN, IND, ITA, JPN, KOR, MEX, NAFTA, TUR, USA, ZAF. Le secours FRED `EA19LOLITOAASTSAM` s'arrête en 2022-11 (série interrompue). Proposition : `G4E` (agrégat OCDE des quatre grandes économies européennes : Allemagne, France, Italie, R.-U. — pas la zone euro) ou l'Allemagne, en le disant clairement. Secours FRED pour les États-Unis : `USALOLITOAASTSAM` (2026-10, 100,96), et `CHNLOLITOAASTSAM` (2026-10).

## D14 — Probabilité de récession (Fed de New York)

- Fichier : `https://www.newyorkfed.org/medialibrary/media/research/capital_markets/allmonth.xls` (139 Ko, Excel 97-2003, `xlrd`). Feuille `rec_prob`, colonnes : `Date` (fin de mois), `10 Year Treasury Yield`, `3 Month Treasury Yield`, `3 Month Treasury Yield (Bond Equivalent Basis)`, `Spread`, `Rec_prob` (**fraction entre 0 et 1**, pas des %), `NBER_Rec` (0/1).
- **Formule vérifiée numériquement** sur tout le fichier (écart maximal 1e-16) : `Rec_prob(t+12 mois) = Φ(−0,5333 − 0,6330 × Spread(t))` avec Φ = loi normale centrée réduite, et `Spread = 10 ans − 3 mois en équivalent obligataire` (colonne D), **moyennes mensuelles** des taux (cohérentes avec `GS10` et `TB3MS` de FRED : oct. 2026 = 5,13 et 4,05). Le 3 mois est converti en base « bond equivalent » : 4,05 % → 4,1487 %. Écart oct. 2026 = 5,13 − 4,1487 = 0,9813 pt → P = Φ(−1,1545) = **12,4 %**, inscrit sur la ligne datée **2027-10** (la probabilité est datée du mois visé, 12 mois après l'écart observé). La dernière probabilité « à 12 mois » pour l'affichage = dernière ligne du fichier avec `Spread` non vide, décalée de 12 mois (ligne 2027-10 = 12,4 %) ; la ligne datée 2026-10 (26,5 %) est la prévision faite il y a 12 mois.
- Les coefficients ne sont **pas** lisibles dans la page `https://www.newyorkfed.org/research/capital_markets/ycfaq` (contenu chargé par JavaScript, aucun texte de méthode récupérable) ; ils sont confirmés par le fichier lui-même. À citer : page « The Yield Curve as a Leading Indicator » de la Fed de New York. Recherche web : aucune page consultable n'affiche ces deux chiffres, mais ils reproduisent le fichier à la décimale près.
- Dernier écart observé : 2026-10 ; dernier mois du fichier : 2027-10 (lignes futures sans taux).
- Secours : recalculer à partir de FRED `GS10` et `TB3MS`, mais la conversion du 3 mois en équivalent obligataire (non documentée ici, à rétro-calculer depuis les colonnes C et D du fichier) est nécessaire pour retrouver les mêmes valeurs ; sinon l'écart sera biaisé d'environ 0,1 point. Le fichier de la Fed de NY reste la source à privilégier.

## D15 — Courbe à terme du pétrole

Appels exacts (yfinance 1.8, `Ticker(t).history(period="10d", auto_adjust=False)`, colonne `Close`) :
- Brent (NYMEX `BZ`, mois en lettres de livraison) : `BZF27.NYM` (janv. 2027, 92,57) … `BZK27.NYM` (mai 2027, 84,37) … `BZX27.NYM` (nov. 2027, 78,08) … `BZZ27.NYM` (déc. 2027, 77,35) ; WTI : `CLZ26.NYM` (83,98, dernier jour de cotation le 20 nov.), `CLK27.NYM` (mai 2027, 78,70), `CLX27.NYM` (nov. 2027, 73,28). Dernier cours le 2026-11-20 pour tous.
- Contrats disponibles : Brent janv. 2027 → déc. 2028 mais avec **trous en 2028** (`BZJ28`, `BZK28`, `BZN28`…`BZX28` introuvables) ; `BZZ26` (déc. 2026) introuvable (déjà échu). WTI : tous les mois de déc. 2026 à déc. 2028.
- Prix à ~6 mois et ~12 mois : Brent mai 2027 = 84,37 / nov. 2027 = 78,08 ; WTI 78,70 / 73,28 ; comparés au front (`BZ=F` 89,95, `CL=F` 83,98) → courbe en **forte backwardation** (prix attendus plus bas).
- Fiabilité : prix de règlement quotidiens, cohérents avec `BZ=F`/`CL=F` (`BZ=F` = `BZG27` à la décimale près, `CL=F` = `CLZ26`). Limites : le jeu de contrats dépend de Yahoo (certains mois lointains absents) ; le contrat expiré disparaît (il faut donc **recalculer chaque jour** quels mois utiliser : mois courant + 6 et + 12) ; un contrat qui expire le jour même (cas `CLZ26`) reste affiché avec son dernier cours ; données retardées, usage personnel (non rediffusables massivement). Choisir WTI ou Brent pour l'affichage, ne pas mélanger. Fiabilité jugée **correcte** pour un indicateur secondaire.
- Secours : EIA STEO (clé facultative, à demander à Georgy ; non testée). Sinon « non disponible ».

## Récapitulatif des points d'attention

1. D5 : prendre `FCT_SOURCE=AVG`, jamais `PFC` ; clé à 7 champs obligatoires ; page BCE `table_3_2026q4` = vérification.
2. D7 : l'API DataMapper est en panne ; utiliser `api.imf.org` (zone euro = `G163`).
3. D10 et D14 : fichiers « .xlsx »/« .xls » en réalité au format Excel ancien : `xlrd`.
4. D12 : l'ancienne clé `STS` est périmée ; utiliser `INW` (U2).
5. D13 : pas de zone euro (CLI interrompu pour l'agrégat) ; secours `G4E` ou pays.
6. D8 et D11 : séries FRED en niveau, calculer le glissement annuel ; D9 déjà en glissement annuel.
7. Rediffusion à trancher : D4 (Michigan), D7 (FMI), D15 (Yahoo/CME).
