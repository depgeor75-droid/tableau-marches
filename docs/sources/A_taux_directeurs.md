# Famille A — Taux directeurs (A1 à A7)

Tests réalisés le 22 novembre 2026 (téléchargements sans clé FRED via `fredgraph.csv`, même contenu que l'API `series/observations`). Profondeur visée : 1er janvier 1990. Unité : % par an pour toutes les séries (type T).

## Tableau de synthèse

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Fed — fonds fédéraux effectif | FRED | `DFF` | 1954-07-01 (couvre 1990) | 2026-11-19 (3,88) | quotidienne (7j/7, valeur reportée les week-ends) | FRED `FEDFUNDS` (mensuelle, → 2026-10-01, 3,88) ; BIS `WS_CBPOL` US (milieu de la fourchette cible, mensuelle, 1990-01 → 2026-10) | oui (données de la Federal Reserve ; citer FRED / Federal Reserve) | OK. Taux effectif, pas la cible. |
| A2 | BCE — taux de dépôt | FRED | `ECBDFR` | 1999-01-01 | 2026-11-20 (2,50) | quotidienne (valeur reportée) | BCE `FM/B.U2.EUR.4F.KR.DFR.LEV` (dates de changement seulement) ; BIS XM (mensuelle, 1999-01 →) | oui avec mention de la source (BCE) ; à reconfirmer sur le portail ECB Data Portal | Aucun taux de dépôt avant 1999-01 : 1990-1998 « non disponible ». Dernier changement : 2026-09-16 à 2,50. |
| A3 | Euribor 3 mois (synthétique avant 1999) | **BCE** (jeu FM) | `FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA` | 1994-01 (6,91) | 2026-10 (2,6347) | mensuelle (moyenne du mois) | FRED `IR3TIB01EZM156N` | oui avec mention (fournisseur indiqué : Refinitiv, via la BCE) | **Remplacement** : le code FRED est périmé (dernière valeur 2026-01, trou en 2026-02) ; ses valeurs sont identiques à la BCE de 1994 à 2026-01 (écart max 0,012). Pas de série quotidienne dans FM (`D.` donne 404). 1990-1993 : non disponible. |
| A4 | Banque d'Angleterre — Bank Rate | Banque d'Angleterre (IADB) | `IUDBEDR` | 1990-01-02 (14,875) | 2026-11-19 (4,00) | quotidienne, jours ouvrés seulement (écart max 5 jours) | BIS `WS_CBPOL` GB (mensuelle, 1990-01 →) ; SNB cube `snboffzisa` code `L0` (mensuelle 2000 →). Pas de code FRED équivalent trouvé (`IUDBEDR` y est en 404) | oui (base sous Open Government Licence v3.0 ; mention « Bank of England ») | OK. Dernier changement : 2026-11-05 (3,75 vers 4,00). |
| A5 | Banque du Japon — taux au jour le jour | FRED (OCDE) | `IRSTCI01JPM156N` | 1985-07-01 | 2026-10-01 (1,227) | mensuelle | **BoJ API** `FM01/STRDCLUCON` (quotidienne, 1998 → 2026-11-18, 1,227) ; BIS JP (cible, avec trous) | inconnue / à vérifier (série OCDE hébergée par FRED : citer l'OCDE ; conditions de la BoJ non vérifiées) | Taux de marché (call rate), pas la cible : 1,227 contre cible 1,25 (relevée le 24 sept. 2026). BIS JP a 116 mois manquants (1999-03 à 2016-08, période sans taux directeur) : à ne pas utiliser comme série principale. |
| A6 | Chine — LPR 1 an (avant 2019-08 : taux de prêt de référence 1 an) | **BIS** | `WS_CBPOL`, clé `M.CN` (ou `D.CN`) | 1996-01 (12,06) | mensuelle 2026-10 (3,00) ; quotidienne 2026-11-17 (3,00) | mensuelle (fin de période) ; quotidienne disponible | PBoC/CFETS chinamoney.com.cn (JSON non documenté, 1 an glissant seulement). FRED `INTDSRCNM193N` / `IRSTCB01CNM156N` à ne pas utiliser (taux d'escompte ≈ 2,9, nature différente, arrêtées 2025 / 2023) | restreinte : la BIS autorise la rediffusion non commerciale avec citation, mais exclut de la tolérance d'extrait les statistiques du BIS Data Portal ; à faire trancher | 1990-1995 : non disponible dans une source gratuite fiable testée. Raccord 2019 cohérent (4,35 jusqu'au 19 août 2019, puis 4,25). Dernière LPR vérifiée sur chinamoney : 2026-11-20, 3,00. |
| A7 | Banque nationale suisse | **BIS** (recoupée avec SNB) | `WS_CBPOL`, clé `M.CH` ; contrôle : SNB cube `snboffzisa` | BIS 1990-01 (6,00) ; SNB 2000-01 | BIS 2026-10 (0,00) ; SNB 2026-09 (0,00, publié le 2026-10-21) | mensuelle | FRED `IR3TIB01CHM156N` (interbancaire 3 mois, 1999-07 → 2026-10, −0,04 : nature différente, à éviter) | BIS : voir A6 ; SNB : inconnue (page de conditions introuvable) | Composition BIS : 1990-1999 taux d'escompte, 2000 à 2019-06 milieu de la fourchette cible Libor 3 mois, depuis le 13 juin 2019 taux directeur. SNB seule : `LZ` n'existe que depuis 2019-06 ; avant, `UG0`/`OG0` (limites basse/haute). Le contrôle numérique SNB vs BIS n'a porté que sur la dernière valeur. |

## Appels exacts qui ont fonctionné (sans clé)

### FRED (A1, A2, A5, secours A3 et A7)
`GET https://fred.stlouisfed.org/graph/fredgraph.csv?id=<CODE>` (option `&cosd=1990-01-01`). Format : CSV `observation_date,<CODE>`, dates `YYYY-MM-DD`, valeur manquante = cellule vide. Pour la collecte définitive : `https://api.stlouisfed.org/fred/series/observations?series_id=<CODE>&file_type=json&observation_start=1990-01-01&api_key=...` (clé jamais dans le dépôt). Une coupure transitoire (code 000) est apparue en fin de session : prévoir des nouvelles tentatives.
Codes testés : `DFF`, `FEDFUNDS`, `ECBDFR`, `IRSTCI01JPM156N` OK et à jour ; `IR3TIB01EZM156N` périmé (2026-01) ; `IR3TIB01CHM156N` à jour mais autre nature ; `IR3TIB01GBM156N` (Royaume-Uni, 3 mois) s'arrête en 2026-01 ; `IUDBEDR` inexistant sur FRED.

### BCE (secours A2, A3)
- `GET https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV?format=csvdata` : colonnes `TIME_PERIOD`, `OBS_VALUE` ; **une ligne par date de changement seulement** (1999-01-01 : 2 ; 2026-06-17 : 2,25 ; 2026-09-16 : 2,5). Pour la quotidienne, reporter la valeur jusqu'au changement suivant (règle de calcul, pas interpolation).
- `GET https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA?format=csvdata` : 394 mois, `TIME_PERIOD` au format `YYYY-MM`.

### Banque d'Angleterre (A4)
`GET "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N"` avec un `User-Agent` de navigateur. Format : `DATE,IUDBEDR`, dates `02 Jan 1990` (`%d %b %Y`, anglais), 9 323 lignes, pas de week-end.

### Banque du Japon (secours A5)
`GET "https://www.stat-search.boj.or.jp/api/v1/getDataCode?format=csv&lang=en&db=FM01&code=STRDCLUCON&startDate=199001"` : une dizaine de lignes d'en-tête (`STATUS`, `MESSAGEID`, …) puis l'en-tête `SERIES_CODE,NAME_OF_TIME_SERIES,UNIT,FREQUENCY,CATEGORY,LAST_UPDATE,SURVEY_DATES,VALUES` ; dates `YYYYMMDD`, une ligne par jour calendaire, `null` sans cotation (week-ends et toute la période 1990-1997). Le format JSON avec un autre code a répondu 400 : utiliser le CSV.

### BIS — `WS_CBPOL` (A6 retenu, A7, secours général)
`GET "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/M.CN+CH+US+XM+GB+JP?format=csv&startPeriod=1990-01"` (1,5 Mo ; le filtre de zone n'est pas strict : refiltrer sur `REF_AREA`). Colonnes utiles : `REF_AREA` (CN, CH, US, XM, GB, JP), `TIME_PERIOD` (`YYYY-MM`), `OBS_VALUE`, `COMPILATION` (décrit les ruptures de définition). Quotidien : `.../WS_CBPOL/1.0/D.CN?format=csv&startPeriod=2019-06-01` (`YYYY-MM-DD`, quelques NaN). La clé `D..` renvoie 404. Fraîcheur : mensuelle jusqu'en 2026-10, quotidienne jusqu'au 17 nov. 2026. Couverture : US, GB, CH dès 1990 ; JP dès 1990 avec trous ; CN dès 1996 ; XM dès 1999. Concordance vérifiée : BIS US vs FRED `FEDFUNDS` proche (écart non quantifié à cause d'une erreur de script, à contrôler à l'implémentation).

### Chine, vérification officielle (non retenue)
`https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis?lang=EN&pageNum=1&pageSize=5` renvoie un JSON (`records` avec `1Y`, `5Y`, `showDateCN`). Endpoint non documenté, limité à un an glissant (paramètres de date refusés : 403) : à utiliser seulement pour vérifier la dernière valeur.

### SNB (contrôle A7)
`GET "https://data.snb.ch/api/cube/snboffzisa/data/csv/en"` : séparateur `;`, 3 lignes d'en-tête puis `Date;D0;Value`, dates `YYYY-MM`. `LZ` = taux directeur (2019-06 → 2026-09), `UG0`/`OG0` = fourchette cible (2000-01 → 2019-05), aussi `L0` (Bank Rate), `L1` (BoJ), `EF` (dépôt BCE). Le cube `snbgwdzid` (marché monétaire quotidien, SARON) n'est PAS le taux directeur.

## Points d'attention
- Profondeur : A2 dès 1999 ; A3 dès 1994 ; A6 dès 1996 ; reste avant ces dates : « non disponible ».
- Les séries OCDE sur FRED (A5, secours A3/A7) peuvent s'arrêter sans préavis : surveiller la dernière date.
- Raccord A5 : FRED mensuel (1985 →) et BoJ quotidien (1998 →), vérifier l'écart < 0,10 point à l'implémentation.
- Rediffusion : A6 et A7 dépendent de la BIS (non commerciale avec citation) ; à signaler dans `PLAN.md` pour décision de Georgy. Conditions de la BoJ, de la SNB et de FRED (série OCDE) non confirmées (pages inaccessibles ou 404).
