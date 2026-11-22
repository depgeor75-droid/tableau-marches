# Famille B — Taux longs (obligations d'État)

Tests réalisés le 22 novembre 2026 (Python 3.12 / curl, Windows). Profondeur visée : 1er janvier 1990.
Aucune clé API n'a été utilisée. Pour FRED, les tests ont utilisé `fredgraph.csv` (sans clé) ; la collecte utilisera l'API officielle avec clé (même contenu).

## Tableau de synthèse

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| B1 | États-Unis 10 ans | FRED | `DGS10` | 1962-01-02 | 2026-11-19 (5,04) | quotidien (jours ouvrés) | — | oui (données Fed/Trésor, domaine public ; mention FRED) | valeurs manquantes = `.` (jours fériés) |
| B2 | États-Unis 2 ans | FRED | `DGS2` | 1976-06-01 | 2026-11-19 (4,76) | quotidien | — | oui | idem |
| B3 | États-Unis 3 mois | FRED | `DGS3MO` | 1981-09-01 | 2026-11-19 (4,34) | quotidien | — | oui | idem |
| B4 | Allemagne 10 ans (Bund) | Bundesbank, courbe Svensson, titres fédéraux cotés, 10 ans | `BBSIS` `D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A` (quotidien) et `M.I.ZST...` (fin de mois) | quotidien : 1997-08-07 ; fin de mois : 1990-01 | 2026-11-20 (3,39) | quotidien depuis 08/1997, mensuel (fin de mois) avant | FRED `IRLTLT01DEM156N` (mensuel, moyenne mensuelle, 1960 → 2026-10) ; Eurostat `irt_lt_mcby_m` geo=DE | oui avec mention (données Bundesbank, réutilisation autorisée avec citation de la source ; à citer « Deutsche Bundesbank ») | quotidien seulement depuis août 1997 ; avant : une valeur par mois (fin de mois). Raccord de nature (fin de mois vs jours) : garder le mensuel pré-1997 comme série à part ou le marquer « mensuel avant 08/1997 » |
| B5_2A | Zone euro 2 ans (courbe AAA BCE) | BCE | `YC` / `B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y` | 2004-09-06 | 2026-11-19 (3,125) | quotidien (jours ouvrés TARGET) | — | oui (BCE : réutilisation avec mention de la source) | 5 678 observations, pas de trou |
| B5_10A | Zone euro 10 ans (courbe AAA BCE) | BCE | `YC` / `B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y` | 2004-09-06 | 2026-11-19 (3,442) | quotidien | — | oui | idem. Pas d'historique avant 2004 pour la courbe AAA (Svensson BCE démarre 2004-09-06) : « depuis 2004 », à dire dans la fiche. Prolongement possible avant 2004 avec le Bund (B4), mais ce serait une autre nature : ne pas raccorder |
| B6 | Belgique 10 ans (OLO) | FRED (OCDE) | `IRLTLT01BEM156N` | 1960-01 | 2026-10 (4,38) | mensuel (moyenne mensuelle) | Eurostat `irt_lt_mcby_m` geo=BE (1990-01 → 2026-10, 442 mois, complet) | oui avec mention (OCDE/Eurostat) | mensuel seulement : pas de quotidien gratuit trouvé (la BNB n'a pas été testée) |
| B7 | France 10 ans (OAT) | FRED (OCDE) | `IRLTLT01FRM156N` | 1960-01 | 2026-10 (4,89) | mensuel | Eurostat geo=FR (1990-01 → 2026-10) | oui avec mention | mensuel |
| B8 | Italie 10 ans (BTP) | FRED (OCDE) | `IRLTLT01ITM156N` | 1991-03 | 2026-10 (4,68) | mensuel | Eurostat geo=IT (1990-01 → 2026-10, 442 mois, complet) | oui avec mention | FRED commence en 1991-03 ; Eurostat couvre dès 1990-01 : utiliser Eurostat en secours pour les 2 premiers mois, ou le dire (« depuis mars 1991 ») |
| B9 | Royaume-Uni 10 ans (Gilt) | Banque d'Angleterre IADB, rendement au pair nominal 10 ans | `IUDMNPY` | 1993-11-01 | 2026-11-18 (5,268) | quotidien (jours ouvrés) | FRED `IRLTLT01GBM156N` (mensuel, 1960 → 2026-10, identique à la moyenne mensuelle IADB `IUMAMNPY` : 5,3393) ; IADB `IUDMNZC` (zéro-coupon 10 ans, quotidien depuis 1990-01-02, autre nature) | restreinte à vérifier : la BoE autorise la réutilisation avec mention (« Source: Bank of England »), conditions exactes non lues ; marquer « oui avec mention » sous réserve | quotidien depuis 1993-11 ; 1990-1993 : FRED mensuel seulement. Raccord quotidien/mensuel à faire en deux séries ou en marquant la zone mensuelle |
| B10 | Japon 10 ans (JGB) | Ministère des Finances japonais | fichiers `jgbcme_all.csv` (historique) + `jgbcme.csv` (mois en cours), colonne `10Y` | 1986-07-05 (10 ans non vide ; la 1re ligne du fichier date de 1974) | 2026-11-19 (fichier du mois) ; fichier historique : 2026-10-30 (2,817) | quotidien (jours ouvrés) | FRED `IRLTLT01JPM156N` (mensuel, 1989-01 → 2026-10) | oui avec mention (MOF : © Ministry of Finance Japan ; conditions précises non lues, à citer) | `-` = valeur absente ; dates `AAAA/M/J` non zéro-paddées ; le fichier mensuel est en cp932 avec lignes parasites (lignes vides, note en bas) |
| B11 | Chine 10 ans | **non disponible** (gratuit et fiable, avec historique) | voir remarque | — | — | — | — | inconnue | voir « B11 » plus bas |
| B12 | Suisse 10 ans | FRED (OCDE) | `IRLTLT01CHM156N` | 1960-01 | 2026-10 (0,51) | mensuel | BNS (non testé) | oui avec mention | mensuel seulement |
| T10Y2Y | Écart US 10 ans − 2 ans | FRED | `T10Y2Y` | 1976-06-01 | 2026-11-20 (0,29) | quotidien | calcul `DGS10 − DGS2` | oui | FRED publie un jour de plus que DGS10/DGS2 dans ce test (20/11) |
| T10Y3M | Écart US 10 ans − 3 mois | FRED | `T10Y3M` | 1982-01-04 | 2026-11-20 (0,60) | quotidien | calcul `DGS10 − DGS3MO` | oui | idem |

Écarts Italie/France/Belgique − Allemagne : à calculer en mensuel avec les séries FRED/Eurostat (même source, même date) ; en quotidien impossible (seul le Bund est quotidien).

## Appels exacts qui ont fonctionné

### FRED (sans clé, test) — B1, B2, B3, B6, B7, B8, B9 (secours), B10 (secours), B12, T10Y2Y, T10Y3M, B4 (secours)
`GET https://fred.stlouisfed.org/graph/fredgraph.csv?id=<CODE>&cosd=1960-01-01` → 200, CSV `observation_date,<CODE>`. Valeurs manquantes : `.`. Les séries OCDE mensuelles sont datées au 1er du mois (ex. `2026-10-01`). La collecte réelle : API `https://api.stlouisfed.org/fred/series/observations?series_id=<CODE>&api_key=<CLÉ>&file_type=json&observation_start=1990-01-01`.
`IRLTLT01CNM156N` (Chine) : 404, n'existe pas.

### BCE — B5
`GET https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y?format=csvdata&startPeriod=1990-01-01` et idem `SR_10Y` → 200, aucune en-tête spéciale. Colonnes utiles : `TIME_PERIOD`, `OBS_VALUE`. 5 678 lignes, de 2004-09-06 à 2026-11-19. Confirmé : 2 ans et 10 ans quotidiens depuis septembre 2004.

### Bundesbank — B4
Quotidien : `GET https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&startPeriod=1990-01-01` → 200 (`format=csvdata` renvoie 406 : utiliser `format=csv`).
Format : séparateur `;`, décimale virgule (`3,39`), BOM UTF-8, environ 10 lignes d'en-tête de métadonnées puis lignes `AAAA-MM-JJ;valeur;drapeau`. Valeur absente = `.` avec le texte « Kein Wert vorhanden » ; les jours de week-end/fériés apparaissent donc comme lignes vides (à ignorer). 7 436 valeurs réelles de 1997-08-07 à 2026-11-20.
Fin de mois (avant 1997-08) : même appel avec `M.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A` et `startPeriod=1990-01` → 1990-01 (7,88) … 2026-10 (3,40). Commentaire de la série : « Bis Juli 1997 liegen lediglich Ultimowerte vor » (avant août 1997, uniquement des valeurs de fin de mois). Le test sans en-tête User-Agent fonctionne.
Alternative écartée : `BBK01/WT1010` (Umlaufrendite) → 404.

### Banque d'Angleterre IADB — B9
`GET https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N` renvoie 302 vers `https://www.bankofengland.co.uk/boeapps/database/_iadb-FromShowColumns.asp?<mêmes paramètres>`. **Nécessite un en-tête `User-Agent` de navigateur et le suivi des redirections (`-L`)** : sans cela, on obtient 302 sans contenu. Avec `curl -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."` : 200, `application/csv`. Format : `DATE,IUDMNPY`, dates `01 Nov 1993` (format `%d %b %Y`), décimale point. 8 352 lignes, 01 Nov 1993 → 18 Nov 2026 (retard de 2-3 jours). Avec `requests`, redirections suivies par défaut, ajouter `headers={"User-Agent": "Mozilla/5.0 ..."}`. Séries voisines testées : `IUDMNZC` (zéro-coupon 10 ans, depuis 1990-01-02), `IUMAMNPY` (moyenne mensuelle, depuis 1993-12-31), `IUDLNPY` (long terme, depuis 2000).

### Eurostat — secours B6, B7, B8 (et DE)
`GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_mcby_m?format=JSON&geo=BE&geo=FR&geo=IT&geo=DE&sinceTimePeriod=1990-01` → 200, JSON-stat (dimensions `freq`, `int_rt`, `geo`, `time` ; BE=0, DE=1, FR=2, IT=3). 442 mois pleins par pays, 1990-01 → 2026-10 (critère de convergence de Maastricht, mensuel).

### Ministère des Finances japonais — B10
Historique : `GET https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv` → 200 (1,2 Mo). Attention : l'adresse sans `/historical/` renvoie 404. Mois en cours : `GET https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv` → 200 (en-tête `Last-Modified`, jours du mois jusqu'au 19/11/2026). Un `User-Agent` de navigateur a été envoyé (non testé sans). Format : ligne 1 titre, ligne 2 en-têtes (`Date,1Y,2Y,…,10Y,…`), dates `AAAA/M/J`, valeurs absentes `-`. Le fichier historique se termine le 2026-10-30 (2,817) et le fichier du mois commence le 2026-11-02 : raccord sans trou. Le fichier mensuel est encodé en Shift-JIS (cp932) et se termine par des lignes vides et une note (à ignorer).

## B11 — Chine 10 ans : non disponible
- FRED : `IRLTLT01CNM156N` n'existe pas (404) ; aucune série chinoise de rendement 10 ans trouvée dans les essais FRED.
- IMF/IFS (via DBnomics) : pas de série de rendement obligataire chinois (`M.CN.FIGB_PA` introuvable).
- Yahoo Finance (yfinance) : `CN10Y=X`, `^CN10Y`, `10CNY.B`, `CN10YT=RR` introuvables.
- Stooq (`10cny.b`) : bloqué par une vérification anti-robot (preuve de travail JavaScript) : non contourné.
- ChinaBond (`yield.chinabond.com.cn`) : HTTP 405 sur l'appel direct testé.
- ChinaMoney (CFETS, `chinamoney.com.cn`) : un point d'accès JSON interne (`/ags/ms/cm-u-bk-currency/ClsYldCurvHis`, paramètre `termId`) a renvoyé la courbe du dernier jour (2026-11-20), mais il s'agit d'un point d'accès non documenté de l'application web ; la profondeur historique n'a pas pu être vérifiée (un test plus poussé a été bloqué par le contrôle de permissions de la session) et les conditions de rediffusion sont inconnues. Non retenu.
- Décision proposée : « non disponible » pour B11, sauf si Georgy accepte une source à rediffusion douteuse. Piste éventuelle à valider avec lui : données ChinaBond/CFETS officielles (accès gratuit mais conditions d'usage à lire).

## Points d'attention
- Quotidien gratuit existant seulement pour : US (B1-B3), Bund (depuis 1997), zone euro AAA (depuis 2004), Gilt (depuis 1993), JGB. Belgique, France, Italie, Suisse : mensuel uniquement ; écarts vs Bund en mensuel.
- Les séries mensuelles FRED/OCDE sont des moyennes mensuelles, datées du 1er du mois ; la série Bundesbank mensuelle est une valeur de fin de mois : ne pas mélanger sans le dire (ex. 1990-01 : 7,88 vs 7,695).
- B4, B9, B10 : raccord mensuel → quotidien à traiter en deux séries distinctes ou à la date commune ; le Bund pré-1997 et le Gilt pré-1993 viennent de FRED mensuel.
- Date du jour réelle 2026-11-22 : toutes les dernières observations sont à 1-3 jours (quotidien) ou jusqu'à octobre 2026 (mensuel) : normal.
- Aucune série de la famille B n'est de type ICE/BofA ; les conditions de réutilisation précises de la BoE et du MOF japonais sont à confirmer avant mise en ligne (mention de la source dans tous les cas).
