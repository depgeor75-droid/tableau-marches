# Famille C — Inflation (C1 à C13)

Tests réalisés le 22 novembre 2026 (sans clé API). Scripts et téléchargements de test hors projet.
« Glissement annuel » = variation sur 12 mois en %.

## Points d'attention majeurs

1. **IPC américain d'octobre 2025 : trou confirmé.** `CPIAUCSL` et `CPILFESL` ont une valeur **vide** au 2025-10-01 (ligne `2025-10-01,` du CSV FRED, pas de point « . »). Le glissement annuel est donc manquant en **octobre 2025** (pas d'indice) et en **octobre 2026** (pas de base de comparaison). L'indice d'octobre 2026 existe (337,476 et 339,9), mais pas son glissement. Calcul fait sur toute la période : seuls ces 2 mois manquent depuis 1990. Septembre et novembre 2025 sont présents. Le FMI (`USA.CPI._T.IX.M`) a le même trou.
2. **Autres séries américaines : pas de trou.** `PCEPI` et `PCEPILFE` (octobre 2025 présent : 127,790 et 127,165), `PPIACO` (260,591), `CES0500000003` (36,85) et `MICH` (4,6) sont complètes. Seul l'IPC (C1, C2) est concerné. Dernières observations : PCEPI et PCEPILFE 2026-09 ; PPIACO, CES0500000003 et MICH 2026-10.
3. **Codes BCE du cahier des charges périmés.** Le jeu `ICP` de la BCE (et `prc_hicp_manr` d'Eurostat) s'arrête en **décembre 2025** : l'IPCH change de méthode le 4 février 2026 (nomenclature ECOICOP v2) et la BCE a remplacé `ICP` par le jeu **`HICP`** (clé en `4D0`). Sur 1997-2025 les deux jeux diffèrent de 0,1 point au plus (révisions) : prendre le nouveau jeu en entier, sans raccord.
4. **BCE avant 1997 : non.** Les taux annuels de la zone euro commencent en **janvier 1997** (indice depuis janvier 1996). Pour 1991-1996 : OCDE `EA20` (voir C5). Pour le sous-jacent (C6) : rien avant 1997.
5. **Séries OCDE de FRED arrêtées** : Japon (`CPALTT01JPM659N`, `JPNCPIALLMINMEI`) dernière valeur 2021-06 ; Royaume-Uni (`CPALTT01GBM659N`, `GBRCPIALLMINMEI`) 2025-03 ; Chine (`CHNCPIALLMINMEI`, `CPALTT01CNM659N`) 2025-04. À ne pas utiliser. L'API OCDE directe est à jour pour la Chine (2026-10) mais **arrêtée pour le Japon (2021-06)**.

## Tableau

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| C1 | É.-U. IPC | FRED (BLS) | `CPIAUCSL` (indice) ; glissement calculé | 1947-01 | indice 2026-10 ; glissement 2026-09 | mensuelle, indice 1982-84=100, désaisonnalisé | FMI `USA.CPI._T.IX.M` (même trou) | oui (données BLS publiques ; mention FRED) | **Trou 2025-10** : glissement manquant en 2025-10 et 2026-10. Série désaisonnalisée : le glissement diffère un peu du chiffre officiel (non désaisonnalisé, `CPIAUCNS`, non testé). |
| C2 | É.-U. IPC hors énergie et alimentation | FRED (BLS) | `CPILFESL` | 1957-01 | indice 2026-10 ; glissement 2026-09 | mensuelle, indice 1982-84=100 | — | oui | Même trou 2025-10 et 2026-10. |
| C3 | É.-U. PCE | FRED (BEA) | `PCEPI` | 1959-01 | 2026-09 | mensuelle, indice 2017=100 | — | oui | Pas de trou. Publié un mois après l'IPC. |
| C4 | É.-U. PCE sous-jacent | FRED (BEA) | `PCEPILFE` | 1959-01 | 2026-09 | mensuelle | — | oui | Pas de trou. |
| C5 | Zone euro IPCH | BCE, jeu `HICP` | `HICP/M.U2.N.000000.4D0.ANR` | 1997-01 | 2026-10 (4,0) | mensuelle, % | Eurostat `prc_hicp_minr` (geo=EA, TOTAL, RCH_A) : même début, même dernière valeur. Pré-1997 : OCDE `EA20.M.N.CPI.PA._T.N.GY`, 1991-01 à 1996-12 (écart ≤ 0,18 point avec la BCE sur 1997-2025) | oui, avec mention (BCE : reproduction autorisée en citant la source ; Eurostat : réutilisation libre avec source) | Aucun trou 1997-2026. Composition variable de la zone. Le raccord OCDE 1991-96 est facultatif (série EA20 rétropolée, arrêtée en 2025-12). |
| C6 | Zone euro IPCH sous-jacent (hors énergie, alimentation, alcool, tabac) | BCE, jeu `HICP` | `HICP/M.U2.N.XEF000.4D0.ANR` | 1997-01 | 2026-10 (2,6) | mensuelle | Eurostat `prc_hicp_minr`, `coicop18=TOT_X_NRG_FOOD` : début seulement 2000-12 | oui | Rien avant 1997 (OCDE `EA20` hors énergie/alimentation : 1997-01 aussi). L'ancien code `...XEF000.4.ANR` s'arrête en 2025-12. |
| C7 | Belgique IPCH | BCE, jeu `HICP` | `HICP/M.BE.N.000000.4D0.ANR` | 1997-01 | 2026-10 (5,2) | mensuelle | Eurostat `prc_hicp_minr` (geo=BE) | oui | Aucun trou. Avant 1997 : seulement l'IPC national OCDE (`BEL`, 1988-2025), non harmonisé, non retenu. |
| C8 | Allemagne IPCH | BCE, jeu `HICP` | `HICP/M.DE.N.000000.4D0.ANR` | 1997-01 | 2026-10 (2,9) | mensuelle | Eurostat (geo=DE) | oui | Aucun trou. |
| C9 | France IPCH | BCE, jeu `HICP` | `HICP/M.FR.N.000000.4D0.ANR` | 1997-01 | 2026-10 (3,7) | mensuelle | Eurostat (geo=FR) | oui | Aucun trou. |
| C10 | Italie IPCH | BCE, jeu `HICP` | `HICP/M.IT.N.000000.4D0.ANR` | 1997-01 | 2026-10 (5,6) | mensuelle | Eurostat (geo=IT) | oui | Aucun trou. |
| C11 | Royaume-Uni IPC | ONS | `D7G7` (jeu MM23) | 1989-01 | 2026-10 (3,6) | mensuelle, glissement annuel déjà calculé | FMI `GBR.CPI._T.YOY_PCH_PA_PT.M` (1956-01 à 2026-09 ; écarts jusqu'à 0,2 point avec l'ONS) | oui (Open Government Licence v3, mention ONS) | Aucun trou. L'OCDE (API et FRED) donne des valeurs **différentes** de l'ONS (jusqu'à 1,6 point dans le passé, 0,1 en 2026) : ne pas l'utiliser. Prochaine publication : 16 décembre 2026. |
| C12 | Japon IPC | FMI via `api.imf.org` | `CPI/JPN.CPI._T.IX.M` (indice 2020=100) ; ou `...YOY_PCH_PA_PT.M` | 1955-01 | 2026-09 (indice 114,5 ; glissement 2,23) | mensuelle | Bureau des statistiques du Japon (e-Stat) : CSV téléchargeable mais identifiant de fichier changeant à chaque publication ; API e-Stat avec clé gratuite (non créée) | à vérifier (conditions d'utilisation du FMI) | OCDE et FRED/OCDE arrêtés en 2021-06. Un mois de retard environ (octobre 2026 pas encore au FMI). Écart possible de 0,1 point avec le chiffre officiel (indice à 1 décimale : janvier 2023, 4,39 contre 4,3 officiel). Aucun trou. |
| C13 | Chine IPC | OCDE (API) | `CHN.M.N.CPI.PA._T.N.GY` | 1988-01 | 2026-10 (0,7) | mensuelle, glissement déjà calculé | FMI `CHN.CPI._T.YOY_PCH_PA_PT.M` (1994-01 à 2026-10, identique en 2026) | oui avec mention (conditions OCDE à re-vérifier) | Origine NBS ; `data.stats.gov.cn` répond 403 aux appels automatiques. OCDE et FMI diffèrent parfois de plus de 0,3 point (2000, 2006, 2020-07, 2021-05, 2021-07) ; valeurs connues (février 2020 : 5,2 ; octobre 2022 : 2,1) conformes à l'OCDE. Aucun trou. |

## Appels exacts qui fonctionnent

### FRED (sans clé)
`https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL` (idem `CPILFESL`, `PCEPI`, `PCEPILFE`, `PPIACO`, `CES0500000003`, `MICH`). CSV à deux colonnes (`observation_date`, code série) ; valeur manquante = champ **vide**. Dates au premier jour du mois. Paramètres facultatifs `cosd=` et `coed=`. Avec la clé, utiliser l'API officielle (même contenu).
Conditions : mention exigée par FRED (« This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis »), à vérifier sur leur site.

### BCE (nouveau jeu `HICP`)
`https://data-api.ecb.europa.eu/service/data/HICP/M.U2.N.000000.4D0.ANR?format=csvdata`
Autres clés : `M.U2.N.XEF000.4D0.ANR`, `M.BE.N.000000.4D0.ANR`, `M.DE...`, `M.FR...`, `M.IT...`. Colonnes utiles : `TIME_PERIOD` (`2026-10`), `OBS_VALUE`. Avant 1997 les lignes existent avec valeur vide (à ignorer). Filtres `startPeriod=` et `lastNObservations=` possibles. Indice : `...000000.4D0.INX` (valide depuis 1996-01).
Ancien jeu `ICP/M.U2.N.000000.4.ANR?format=csvdata` : répond, mais s'arrête en 2025-12.

### Eurostat (secours)
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?format=JSON&lang=EN&geo=EA&unit=RCH_A&coicop18=TOTAL&sinceTimePeriod=1996-01`
Sous-jacent : `coicop18=TOT_X_NRG_FOOD`. Unités : `RCH_A` (glissement annuel), `I25` et `I15` (indices). Jeu mis à jour le 2026-11-18. L'ancien `prc_hicp_manr` s'arrête en 2025-12.

### ONS
`https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23/data` (JSON, tableau `months`, champs `date` au format `2026 OCT` et `value` en texte). Nécessite un `User-Agent` ordinaire. CSV : `https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7g7/mm23`.

### OCDE
`https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/CHN.M.N.CPI.PA._T.N.GY?startPeriod=1988-01` avec l'en-tête `Accept: application/vnd.sdmx.data+csv`. Zone euro pré-1997 : même appel avec `EA20`. Indice : `...CPI.IX._T.N._Z`.

### FMI
`https://api.imf.org/external/sdmx/2.1/data/CPI/JPN.CPI._T.IX.M` (XML SDMX ; attributs `TIME_PERIOD="2026-M09"` et `OBS_VALUE`). Glissement : `JPN.CPI._T.YOY_PCH_PA_PT.M`. `User-Agent` ordinaire. DBnomics (`api.db.nomics.world/v22/series/IMF/CPI/M.JP.PCPI_IX`) répond aussi, non exploité.
