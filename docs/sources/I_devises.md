# Famille I — Devises (test du 22 novembre 2026)

Tous les codes ont été testés par téléchargement réel. Aucune clé API n'a été utilisée (FRED : export CSV public, même contenu que l'API).

## Tableau

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| I1 | EUR/USD | BCE | `EXR.D.USD.EUR.SP00.A` (dollars par euro) | 1999-01-04 | 2026-11-20 | quotidienne (jours ouvrés TARGET) | FRED `DEXUSEU` (1999-01-04 → 2026-11-13) | oui, source citée | Fixation BCE à 14 h 15 (Francfort). |
| I2 | USD/JPY | BCE croisé dès 1999 ; FRED avant | BCE `JPY` ÷ `USD` ; FRED `DEXJPUS` | FRED 1971-01-04 ; BCE 1999-01-04 | BCE 2026-11-20 ; FRED 2026-11-13 | quotidienne | FRED `DEXJPUS` seul (9 jours de retard) | oui (BCE : source citée ; FRED : domaine public, citation demandée) | (JPY par EUR) ÷ (USD par EUR). |
| I3 | USD/CNY | BCE croisé dès 2000-01-13 ; FRED avant | BCE `CNY` ÷ `USD` ; FRED `DEXCHUS` | FRED 1981-01-02 ; BCE CNY 2000-01-13 | BCE 2026-11-20 ; FRED 2026-11-13 | quotidienne | FRED `DEXCHUS` seul | oui (idem) | Le CNY de la BCE commence le 2000-01-13 (pas en 1999). Avant : FRED. |
| I4 | GBP/USD | BCE croisé dès 1999 ; FRED avant | BCE `USD` ÷ `GBP` ; FRED `DEXUSUK` | FRED 1971-01-04 ; BCE 1999-01-04 | BCE 2026-11-20 ; FRED 2026-11-13 | quotidienne | FRED `DEXUSUK` seul | oui (idem) | GBP/USD = (USD par EUR) ÷ (GBP par EUR). |
| I5 | USD/CHF | BCE croisé dès 1999 ; FRED avant | BCE `CHF` ÷ `USD` ; FRED `DEXSZUS` | FRED 1971-01-04 ; BCE 1999-01-04 | BCE 2026-11-20 ; FRED 2026-11-13 | quotidienne | FRED `DEXSZUS` seul | oui (idem) | |
| I6 | Indice du dollar (DXY) | Yahoo | `DX-Y.NYB` (`auto_adjust=False`, colonne `Close`) | 1990-01-01 (début demandé du test) | 2026-11-20 | quotidienne | FRED `DTWEXBGS` : REMPLACEMENT, pas raccord | inconnue / restreinte (Yahoo, usage personnel) ; FRED : domaine public | Un seul trou de plus de 5 jours : 11-17 sept. 2001. |
| I6 (secours) | Indice large du dollar (Fed) | FRED | `DTWEXBGS` | 2006-01-02 | 2026-11-13 | quotidienne, livrée par lots hebdomadaires | — | oui (domaine public, citation demandée) | Autre indice que le DXY (panier large pondéré par les échanges, base janv. 2006 = 100) : niveau et historique différents. |
| croisés | EUR/GBP, EUR/CHF, EUR/JPY, EUR/CNY | BCE | `EXR.D.GBP+CHF+JPY+CNY.EUR.SP00.A` (valeurs directes, aucun calcul) | 1999-01-04 (CNY : 2000-01-13) | 2026-11-20 | quotidienne | croisé FRED, ex. EUR/JPY = DEXJPUS × DEXUSEU (dès 1999 seulement) | oui, source citée | Directement dans la réponse BCE. |

## Fréquence réelle de FRED

- Les 5 séries FRED de change (H.10) ont toutes la même dernière date : 2026-11-13 (vendredi) alors que nous sommes le 22 novembre, soit 9 jours de retard. La BCE va jusqu'au 2026-11-20 (2 jours). Données quotidiennes, mais livrées par lots hebdomadaires (cohérent avec la remarque de la spec).
- Profondeur : DEXJPUS, DEXUSUK, DEXSZUS depuis 1971-01-04 ; DEXCHUS depuis 1981-01-02 ; DEXUSEU depuis 1999-01-04 ; DTWEXBGS depuis 2006-01-02.
- Format du CSV FRED : en-têtes `observation_date,CODE` ; les jours sans cotation (fériés américains) sont des cellules vides (282 dans DEXUSEU), à laisser en trou (§3 règle 1). Les trous de plus de 5 jours sont rares : 1 pour DEXJPUS, DEXUSUK et DEXSZUS, 7 pour DEXCHUS, 2 pour DTWEXBGS.

## BCE

- Début 1999-01-04 pour USD, JPY, GBP, CHF ; CNY : 2000-01-13. Dernière date : 2026-11-20 pour toutes.
- 7 141 observations par devise (CNY : 6 874). Colonnes utiles : `CURRENCY`, `TIME_PERIOD`, `OBS_VALUE`, `OBS_STATUS`. Valeurs vides (statut `H`) : 309 lignes, toutes entre 1999-12-31 et 2012-05-01 ; ne pas les interpoler. Toutes les cotes sont en unités de devise pour 1 EUR.
- Format « long » (une ligne par devise et par jour), UTF-8, séparateur virgule : il faut pivoter.
- Réutilisation (mentions légales de la BCE) : diffusion et reproduction permises si l'information est exacte et si la BCE est citée comme source. La BCE décline toute responsabilité.

## Écart FRED / BCE croisé (même jour, 6 638 jours communs depuis 2000-01-13)

FRED = midi à New York ; BCE = 14 h 15 à Francfort (environ 8 h 15 à New York). Deux instants différents, donc deux cotations différentes.

| paire | écart absolu moyen | 95e centile | maximum (date) | biais moyen |
|---|---|---|---|---|
| EUR/USD | 0,25 % | 0,74 % | 2,73 % (2016-03-10) | −0,01 % |
| USD/JPY | 0,24 % | 0,68 % | 3,65 % (2022-10-21) | +0,01 % |
| USD/CNY | 0,04 % | 0,16 % | 2,01 % (2005-07-21, réévaluation) | +0,01 % |
| GBP/USD | 0,24 % | 0,67 % | 2,35 % (2022-11-10) | −0,01 % |
| USD/CHF | 0,27 % | 0,77 % | 2,97 % (2015-01-16, décrochage du franc) | +0,02 % |

Pas de biais, mais un bruit quotidien d'environ 0,25 % avec des jours extrêmes de 2 à 4 % les jours de forte volatilité. En 2026 l'écart moyen est de 0,15 à 0,18 % (USD/CNY : 0,03 %).

Écart au point de raccord proposé (premier jour BCE) : USD/JPY +1,15 % (1999-01-04), USD/CHF +0,36 %, EUR/USD −0,20 %, GBP/USD −0,02 %, USD/CNY −0,03 % (2000-01-13). Tous sous 2 % ; USD/JPY à surveiller.

## Recommandation : variante (b)

BCE pour toute la période depuis 1999 (2000-01-13 pour le CNY), FRED uniquement avant, avec raccord à date fixe (1999-01-04 ; 2000-01-13 pour le CNY).

1. La variante (a) raccorde FRED (midi New York) et BCE (14 h 15 Francfort) à une date qui bouge chaque semaine : à chaque arrivée de FRED, l'historique récent change de 0,25 % en moyenne (parfois plusieurs %), ce qui crée de faux mouvements et oblige à gérer des jours « provisoires ».
2. En (b) il n'y a qu'un raccord, fixe, mesuré une fois. Les croisés EUR/xxx sont les valeurs BCE directes, donc cohérents avec I1-I5.
3. La fraîcheur est celle de la BCE (2 jours) au lieu de 9 jours.
4. Coût : le tracé depuis 1999 diffère de celui de la Fed d'environ 0,25 % en moyenne, négligeable pour un tableau de bord. EUR/USD n'existe pas avant 1999 (la spec dit « depuis 1999 »).
5. Si la BCE tombe en panne, retomber sur FRED seul (retard signalé), selon la règle 7.

## DXY (I6)

- Yahoo `DX-Y.NYB` : 9 400 clôtures, 1990-01-01 → 2026-11-20 (103,81 au 2026-11-20), non ajusté. Seul trou de plus de 5 jours : 2001-09-17 (marchés fermés après le 11 septembre). Source non officielle : rediffusion à traiter comme douteuse (Georgy tranche, §3 règle 10).
- Secours : FRED `DTWEXBGS` (2006-01-02 → 2026-11-13). Ce n'est pas le DXY (autre panier, autre base) : en cas de panne de Yahoo il REMPLACE la série entière, jamais raccordé, et doit être étiqueté « indice large du dollar (Fed) ».

## Appels exacts qui ont fonctionné (sans clé)

- FRED : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSEU` (idem `DEXJPUS`, `DEXCHUS`, `DEXUSUK`, `DEXSZUS`, `DTWEXBGS`).
- BCE (toutes devises depuis 1999) : `https://data-api.ecb.europa.eu/service/data/EXR/D.USD+JPY+CNY+GBP+CHF.EUR.SP00.A?format=csvdata` (environ 7,7 Mo ; le paramètre `startPeriod` pour les mises à jour n'a pas été testé).
- Yahoo : `yfinance.download("DX-Y.NYB", start="1990-01-01", auto_adjust=False)`, colonne `Close`.
- Licence FRED : pages des séries H.10 et DTWEXBGS marquées « public domain: citation requested ». Citer « Board of Governors of the Federal Reserve System (US), via FRED, Federal Reserve Bank of St. Louis ».

## Formules (BCE)

USD/JPY = JPY ÷ USD ; USD/CNY = CNY ÷ USD ; USD/CHF = CHF ÷ USD ; GBP/USD = USD ÷ GBP ; EUR/USD = USD (direct) ; croisés EUR/GBP, EUR/CHF, EUR/JPY, EUR/CNY = valeurs BCE directes.
