# Famille H — Énergie, matières premières, valeurs refuges et ETF

Tests réalisés le 22 novembre 2026 (Python 3.12, yfinance 1.8, requests). Aucune clé API utilisée. Les « dernières dates » sont celles observées lors du test.

## Tableau récapitulatif

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| H1 | Pétrole Brent | FRED (EIA) historique + Yahoo jours récents | `DCOILBRENTEU` ; `BZ=F` | FRED 20 mai 1987 ; Yahoo 30 juil. 2007 | FRED 17 nov. 2026 ; Yahoo 20 nov. 2026 | quotidienne | Banque mondiale « Crude oil, Brent » (mensuel, 1960M01 → 2026M10) | FRED/EIA : oui (domaine public, citation demandée) ; Yahoo : restreinte/inconnue | **Raccord à risque** : `BZ=F` est un contrat à terme (mois le plus proche), `DCOILBRENTEU` un prix au comptant. Écart mesuré depuis juin 2025 : moyenne 3,9 %, maximum 24,5 % ; au point de raccord (17 nov.) seulement 0,22 %. Voir « Points d'attention » |
| H2 | Pétrole WTI | FRED (EIA) + Yahoo | `DCOILWTICO` ; `CL=F` | FRED 2 janv. 1986 ; Yahoo 23 août 2000 | FRED 17 nov. 2026 ; Yahoo 20 nov. 2026 | quotidienne | Banque mondiale « Crude oil, WTI » (mensuel, 1982M01 → 2026M10) | idem H1 | Écart au point de raccord le 17 nov. 2026 : **−3,9 %** (Yahoo 86,01 contre FRED 89,53) → dépasse le seuil de 2 % de la spec, à signaler. Écart moyen absolu 1,8 %, max 8,4 % depuis juin 2025. **WTI négatif confirmé** (voir plus bas) |
| H3 | Or | Yahoo | `GC=F` | 30 août 2000 | 20 nov. 2026 (3 515,4 USD/oz) | quotidienne | Banque mondiale « Gold » (mensuel, 1960M01 → 2026M10, USD/once troy) | Yahoo : restreinte/inconnue ; Banque mondiale : oui avec mention (CC BY 4.0, à confirmer) | Contrat à terme, pas le comptant. Avant 2000 : uniquement le secours mensuel (raccord de nature différente → le secours **remplace** la série ou reste une série à part) |
| H4 | Gaz naturel Europe (TTF) | Yahoo | `TTF=F` | **23 oct. 2017** | 20 nov. 2026 (88,451) | quotidienne | Banque mondiale « Natural gas, Europe » (mensuel, 1960M01 → 2026M10, USD/mmbtu) | idem H3 | Historique Yahoo court : ~9 ans. Yahoo en EUR/MWh (contrat ICE Endex), Banque mondiale en USD/mmbtu (moyenne des prix européens : TTF depuis 2015 environ, avant autre indice) → **ne pas raccorder**. Plus long trou : 5 jours (2 avr. 2024, Pâques) |
| H5 | Gaz naturel États-Unis (Henry Hub) | Yahoo | `NG=F` | 30 août 2000 | 20 nov. 2026 (3,748 USD/mmbtu) | quotidienne | Banque mondiale « Natural gas, US » (mensuel, 1960M01 → 2026M10) | idem H3 | RAS |
| H6 | Cuivre | Yahoo | `HG=F` | 30 août 2000 | 20 nov. 2026 (5,485 USD/livre) | quotidienne | Banque mondiale « Copper » (mensuel, 1960M01 → 2026M10, **USD/tonne**) | idem H3 | **Unités différentes** : Yahoo en USD/livre (lb), Banque mondiale en USD/tonne. Ne pas raccorder sans conversion, et même alors nature différente (contrat COMEX à terme contre prix LME comptant) |
| H7 | ETF matières premières diversifiées | Yahoo | `DBC` | 6 févr. 2006 | 20 nov. 2026 (29,32) | quotidienne | `GSG` (21 juil. 2006 → 20 nov. 2026) | restreinte/inconnue | Clôture non ajustée (`auto_adjust=False`), donc hors dividendes. Secours : série différente, ne pas raccorder |
| H8 | ETF pétrole | Yahoo | `USO` ; `BNO` | USO 10 avr. 2006 ; BNO 2 juin 2010 | 20 nov. 2026 (USO 139,63 ; BNO 59,02) | quotidienne | — | restreinte/inconnue | Une série par variante : `H8_USO`, `H8_BNO`. USO a probablement subi un regroupement d'actions en 2020 : **vérifier les sauts** (cours « non ajusté » du dividende, mais Yahoo ajuste les fractionnements/regroupements) — minimum observé 17,04, dernier cours 139,63 : la série doit être inspectée avant usage |
| H9 | ETF or | Yahoo | `GLD` | 18 nov. 2004 | 20 nov. 2026 (322,87) | quotidienne | — | restreinte/inconnue | RAS |
| H10 | ETF immobilier coté américain | Yahoo | `VNQ` | 29 sept. 2004 | 20 nov. 2026 (92,56) | quotidienne | — | restreinte/inconnue | Hors dividendes : les REIT distribuent beaucoup, à mentionner dans la fiche |
| H11 | ETF immobilier coté européen | Yahoo | **`IPRP.AS`** (iShares European Property Yield UCITS ETF EUR Dist, Euronext Amsterdam, **EUR**) | 2 janv. 2008 | 20 nov. 2026 (27,23 EUR) | quotidienne | `IPRP.L` (Londres, **GBp** = pence, depuis 2 janv. 2009, dernier 2 283,25) ou `IPRP.MI` (Borsa Italiana, depuis 2 janv. 2008, dernier 30,755, devise non vérifiée) | restreinte/inconnue | Même fonds sur trois places. Retenir `IPRP.AS` (EUR, historique le plus long). Le secours Londres est en pence : même nature mais **devise différente** → remplace, ne prolonge pas. Distribution (Dist) : cours hors dividendes |
| H12 | ETF obligations d'État US longues | Yahoo | `TLT` | 30 juil. 2002 | 20 nov. 2026 (81,45) | quotidienne | — | restreinte/inconnue | Hors coupons, donc dérive baissière sur le long terme |
| H13 | ETF obligations d'État US 7-10 ans | Yahoo | `IEF` | 30 juil. 2002 | 20 nov. 2026 (91,65) | quotidienne | — | restreinte/inconnue | idem |
| H14 | ETF obligations d'État zone euro | Yahoo | **`IEGA.AS`** (iShares Core € Govt Bond UCITS ETF EUR Dist, Amsterdam, **EUR**) | 6 juin 2014 | 20 nov. 2026 (105,82 EUR) | quotidienne | `SEGA.L` (même fonds à Londres, **GBP**, depuis 17 avr. 2009, dernier 88,725) ; `IEGA.L` et `IEGZ.L` : **introuvables** chez Yahoo | restreinte/inconnue | Volume très faible à Amsterdam (82 titres lors de la lecture du 20 nov.) mais cours présent chaque jour de bourse. `SEGA.L` donne 5 ans d'historique en plus mais en livres : **remplace, ne prolonge pas** (devise différente) ; à décider avec Georgy. `IBGL.L` est un autre fonds (Govt Bond 15-30 ans), non retenu |
| H15 | ETF obligations indexées sur l'inflation (US) | Yahoo | `TIP` | 5 déc. 2003 | 20 nov. 2026 (105,74) | quotidienne | — | restreinte/inconnue | RAS |

Toutes les séries Yahoo : colonne `Close` avec `auto_adjust=False`. Tous les cours testés sont strictement positifs, sauf `CL=F` (voir ci-dessous). Plus long intervalle sans cotation observé : 5 à 6 jours calendaires (week-ends et jours fériés), sauf `BZ=F` : **17 jours calendaires, se terminant le 1er mai 2009 (dernière cotation précédente vers le 14 avril 2009)** à signaler dans la fiche H1 (le trou reste un trou). Aucune autre anomalie de continuité.

## Appels exacts qui ont fonctionné

### FRED (sans clé, même contenu que l'API)
- `GET https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU` → CSV 2 colonnes (`observation_date`, code). Début 1987-05-20, **dernière valeur 2026-11-17 (92,94 USD/baril)**, soit un retard de 3 jours ouvrés au 22 nov. 2026.
- `GET https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO` → début 1986-01-02, **dernière valeur 2026-11-17 (89,53)**.
- Particularités : les jours fériés américains sont des **cellules vides** (1 173 sur 10 305 lignes pour Brent, 1 117 sur 10 664 pour WTI) : à traiter en trous, sans report. Unité : dollars US par baril, journalier.
- Cas du 20 avril 2020 : FRED `DCOILWTICO` = **−36,98** (le 17 avril : 18,31 ; le 21 avril : 8,91). Brent FRED ce jour-là : 17,36. Yahoo `CL=F` : **−37,63** le 20 avril 2020 (seule valeur ≤ 0 de la série ; 17 avril : 18,27 ; 21 avril : 10,01 ; 22 avril : 13,78). Valeur à conserver, sans variation en % ni base 100 pour ce point (spec §5).

### Yahoo (un seul appel groupé)
```
import yfinance as yf
d = yf.download(["BZ=F","CL=F","GC=F","TTF=F","NG=F","HG=F","DBC","GSG","USO","BNO","GLD","VNQ","TLT","IEF","TIP","IPRP.AS","IEGA.AS","SEGA.L","IPRP.L","IPRP.MI"],
                start="1990-01-01", auto_adjust=False, group_by="ticker", threads=False)
serie = d["CODE"]["Close"].dropna()
```
Tous les codes ci-dessus ont répondu en un appel. Dernière date commune : 20 nov. 2026 (vendredi). Devise et place vérifiées avec `yfinance.Ticker(code).get_history_metadata()` : `IPRP.AS` = EUR (AMS), `IEGA.AS` = EUR (AMS), `IPRP.L` = GBp, `SEGA.L` = GBP, `IBGL.L` = GBP. Remarque : l'ancienne adresse `IEGA.L` renvoie « possibly delisted ».

### Banque mondiale — « Pink Sheet »
- Page d'origine : `https://www.worldbank.org/en/research/commodity-markets` (lien « Monthly prices — November 2026 (XLS) »).
- **Adresse du fichier lors du test** : `https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx` (588 Ko). **Le segment central de l'adresse (identifiant et « 0050012026 ») change à chaque publication mensuelle** : le script doit lire la page ci-dessus et en extraire le lien (motif `CMO-Historical-Data-Monthly.xlsx`) plutôt que mémoriser l'adresse.
- Structure : classeur de 5 feuilles (`Mismatch Details`, `Monthly Prices`, `Monthly Indices`, `Description`, `Index Weights`). Feuille **`Monthly Prices`** : ligne 4 (index 3) « Updated on November 03, 2026 » ; **ligne 5 (index 4) = noms des séries**, ligne 6 = unités, **données dès la ligne 7** ; colonne A = période au format texte `1960M01` (année, « M », mois à 2 chiffres). Valeurs manquantes écrites sous forme d'un caractère non numérique (affiché `…`) : à traiter en trous.
- Colonnes utiles (index à partir de 0, vérifier par le nom, pas par la position) :

| série | colonne (nom exact en ligne 5) | index | unité | première valeur | dernière valeur |
|---|---|---|---|---|---|
| Brent | `Crude oil, Brent` | 2 | USD/baril | 1960M01 (1,6) | 2026M10 (125) |
| WTI | `Crude oil, WTI` | 4 | USD/baril | **1982M01** (35,3) ; 264 mois non renseignés avant | 2026M10 (97,7) |
| Gaz US (Henry Hub) | `Natural gas, US` | 7 | USD/mmbtu | 1960M01 (0,14) | 2026M10 (2,96) |
| Gaz Europe | `Natural gas, Europe` | 8 | USD/mmbtu | 1960M01 (0,4) | 2026M10 (28,5) |
| Cuivre | `Copper` | 64 | **USD/tonne** | 1960M01 (715) | 2026M10 (14 508) |
| Or | `Gold` | 69 | USD/once troy | 1960M01 (35) | 2026M10 (4 105) |

- 802 mois (1960M01 → 2026M10), **dernière période = octobre 2026**, publiée le 3 novembre 2026 : retard d'environ un mois.
- Attention : la dernière moyenne mensuelle d'octobre 2026 pour le Brent (125) est très au-dessus du dernier cours journalier de novembre (≈ 93) : plausible comme moyenne d'un mois très volatil, mais **à recouper avant affichage** (non vérifié pour octobre). Ne pas utiliser sans contrôle de cohérence avec `DCOILBRENTEU` (moyenne mensuelle).

## Conditions de réutilisation (site public)

- **Yahoo Finance** : données soumises aux conditions de Yahoo et des bourses ; usage personnel, pas de licence de rediffusion. Statut : **restreinte / inconnue**. Je n'ai pas pu lire les conditions de rediffusion de Yahoo lors de ce test : la mention est de mémoire de pratique courante, **à ne pas considérer comme vérifiée** ; la décision revient à Georgy (publier des cours de clôture de quelques ETF avec citation de la source est une pratique courante mais non couverte par une licence).
- **FRED** : conditions de l'API (lues sur fred.stlouisfed.org/legal) : citer FRED comme service d'origine et conserver les mentions de droits d'auteur ; ne pas laisser entendre que l'application est approuvée par la Fed ; afficher que le produit utilise l'API FRED sans être approuvé ni certifié par la Réserve fédérale de St. Louis ; ne pas reproduire l'expérience du site FRED ; « FRED » ne doit pas figurer dans le nom de domaine. Les séries portant la mention « Copyright » appartiennent à des tiers. La page FRED de `DCOILBRENTEU` et `DCOILWTICO` porte l'étiquette **« Public Domain: Citation Requested »** (la page contient aussi la phrase générique « Data in this graph are copyrighted », qui est un message standard de FRED). Source d'origine : U.S. Energy Information Administration (EIA).
- **EIA** : déclare ses données dans le **domaine public** (publications du gouvernement fédéral américain), citation demandée (« Source: U.S. Energy Information Administration (date) »), https://www.eia.gov/about/copyrights_reuse.php. → Statut **oui**, avec citation « EIA via FRED ».
- **Banque mondiale** (Pink Sheet) : la page des prix des matières premières renvoie vers « Data Access and Licensing » (ancre `#cc-by`) ; la fiche du catalogue de données « Global Economic Monitor — Commodities » indique « Creative Commons Attribution 4.0 ». Le Pink Sheet lui-même n'est pas nommé dans ces textes : **CC BY 4.0 probable mais non confirmé pour ce fichier précis** ; les conditions générales du site mentionnent aussi que des tiers peuvent détenir des droits sur certains contenus. Mention d'attribution à prévoir : « Source : Banque mondiale, Commodity Price Data (The Pink Sheet) ».

## Points d'attention
1. **Raccord Brent et WTI (FRED + Yahoo)** : FRED = prix au comptant, Yahoo = contrat à terme du mois le plus proche ; les deux ne sont pas de même nature et le décalage fluctue (changements de contrat). Au point de raccord du 17 nov. 2026 : Brent +0,22 % (OK), **WTI −3,9 % (dépasse le seuil de 2 %)**. À signaler dans `etat.js` ; envisager de n'utiliser les jours récents de Yahoo que comme valeurs provisoires visibles comme telles.
2. **Retard FRED** : dernière valeur au 17 nov. 2026 pour une date de test du 22 nov. (3 jours ouvrés) : normal, prévoir la tolérance d'alerte en conséquence.
3. **WTI négatif** : −36,98 (FRED) et −37,63 (Yahoo) le 20 avril 2020.
4. **TTF=F** : historique Yahoo seulement depuis le 23 oct. 2017 ; la Banque mondiale (mensuel, USD/mmbtu) ne peut que remplacer, pas prolonger.
5. **Devises et unités** : H11 et H14 en EUR (Amsterdam) ; les secours londoniens sont en GBp/GBP ; cuivre Yahoo en USD/lb contre USD/tonne à la Banque mondiale.
6. **Trou Brent Yahoo** de 17 jours calendaires se terminant le 1er mai 2009.
7. Aucune source introuvable dans la famille H ; deux codes d'essai (`IEGA.L`, `IEGZ.L`) sont inexistants chez Yahoo.
8. **Non vérifié** : continuité des cours de USO (regroupement d'actions) et exactitude de la moyenne d'octobre 2026 de la Banque mondiale.
