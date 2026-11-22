# Famille J — Risques, stress et géopolitique (sources testées le 22 nov. 2026)

Tests réalisés avec `curl` / `yfinance 1.8` (sans clé). « Dernière date » = dernière observation lue le 22/11/2026.

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| J1 | VIX | FRED `VIXCLS` (historique) + Yahoo `^VIX` (jours récents) | VIXCLS ; ^VIX | 1990-01-02 (les deux) | FRED 2026-11-19 (28,44) ; Yahoo 2026-11-20 (35,89) | quotidienne (jours ouvrés US) | Yahoo `^VIX` couvre aussi 1990-2026 (9293 lignes) | **restreinte** : FRED « Copyrighted: Citation Required » (© Cboe) | 302 jours vides dans le CSV FRED (jours fériés US) à ignorer. FRED a ~1 jour de retard sur Yahoo. Citation : « Chicago Board Options Exchange, CBOE Volatility Index: VIX [VIXCLS], retrieved from FRED, Federal Reserve Bank of St. Louis ». À soumettre à Georgy. |
| J2 | VSTOXX | **Site STOXX** (fichier texte) | `h_v2tx.txt` ; Yahoo `^V2TX` = **ÉCHEC** (404 « Quote not found », « possibly delisted ») | 1999-01-04 | 2026-11-20 (28,3629) | quotidienne | aucun trouvé | **inconnue, probablement restreinte** (conditions STOXX illisibles : page en 403 ; indices sous licence) | Séparateur `;`, en-tête `Date;Symbol;Indexvalue`, date `jj.mm.aaaa`, 7100 lignes, aucun trou (écart max 6 jours). Donnée du 20/11 déjà publiée. À signaler à Georgy (§3 règle 10). |
| J3a | GPR mensuel (Caldara-Iacoviello) | matteoiacoviello.com | colonne `GPR` (aussi `GPRT`, `GPRA` ; `GPRH` historique depuis 1900) | 1985-01 (GPRH : 1900-01) | 2026-10 (150,52) | mensuelle (maj. début de mois ; dernière : 2 nov. 2026) | — | **oui avec citation** (pas de licence formelle lue) | .xls ancien format (OLE2) : `pd.read_excel(..., engine="xlrd")`. 1522 lignes, colonne `month` (date), 115 colonnes (séries pays incluses), GPR vide avant 1985. |
| J3b | GPR quotidien récent | idem | colonne `GPRD` (+ `GPRD_ACT`, `GPRD_THREAT`, `GPRD_MA7`, `GPRD_MA30`) | 1985-01-01 | 2026-11-16 (189,55) | quotidienne (calendaire), maj. chaque lundi (dernière : 16 nov.) | — | idem J3a | `DAY` = entier aaaammjj, `date` = date. 15 295 lignes. Retard structurel jusqu'à ~1 semaine : seuil d'alerte « en retard » à ~10 jours. |
| J4 | Stress financier St-Louis | FRED `STLFSI4` | STLFSI4 | 1993-12-31 | 2026-11-13 (−0,8655) | hebdomadaire (vendredi) | — | à vérifier (série Fed St-Louis, clause non lue explicitement) ; citer | 1716 points, aucun trou. Démarre fin 1993 (≈ 33 ans). |
| J5 | CISS BCE (zone euro) | BCE, portail de données | `CISS.D.U2.Z0Z.4F.EC.SS_CIN.IDX` | 1980-01-03 | 2026-11-19 (0,0095) | quotidienne (jours ouvrés) | l'ancienne version `SS_CI.IDX` est arrêtée depuis 2025-05 : ne pas l'utiliser | **oui avec citation** (BCE citée, modifications signalées) | 12 239 lignes, aucun trou. Indice 0 à 1 (méthode « NEW CISS »). Variante US existante : `CISS.D.US.Z0Z.4F.EC.SS_CIN.IDX`. |
| J6 | Crédit entreprises US | **EBP (Gilchrist-Zakrajšek), recommandé** | `ebp_csv.csv`, colonnes `gz_spread`, `ebp`, `est_prob` | 1973-01-01 | 2026-10-01 (ebp −0,265 ; gz_spread 1,005) | mensuelle | FRED `NFCICREDIT` | « produit de recherche du personnel de la Fed », aucune clause lue → probablement libre avec citation ; à confirmer (« Website Policies ») | 646 lignes, aucun trou, date = 1er du mois. Maj. annoncée « vers le 4e jour ouvré de chaque mois » (dernière : 5 nov. 2026) ; **tout l'historique peut être révisé** à chaque maj. (à retélécharger en entier) ; changement de fournisseur de données sur certaines obligations depuis sept. 2026. Plus pertinent économiquement et en unités lisibles. Série non officielle, sujette à retard. |
| J6 (alt.) | NFCI crédit (Chicago Fed) | FRED `NFCICREDIT` | NFCICREDIT | 1971-01-08 | 2026-11-13 (−0,013) | hebdomadaire (vendredi) | EBP | **restreinte** : « Copyrighted: Citation Required » | 2915 points, aucun trou, indice standardisé (moyenne 0, écart-type 1 depuis 1971). Plus fréquent et plus frais ; prochaine publication 25 nov. |
| J7 | Crédit entreprises zone euro | **CISS, contribution du sous-indice « marché obligataire »** (proxy, pas un écart de crédit pur) | `CISS.D.U2.Z0Z.4F.EC.SS_BMN.CON` | 1999-01-01 | 2026-11-19 (0,0336) | quotidienne | `CISS.D.U2.Z0Z.4F.EC.SS_FIN.CON` (intermédiaires financiers) | oui avec citation (BCE) | Mêle volatilité des taux souverains, écarts de swap et écarts obligataires privés. C'est une **contribution** au CISS (pondérée par les corrélations), pas le sous-indice brut. 7275 lignes, aucun trou. Aucun vrai écart de crédit des entreprises gratuit et rediffusable trouvé en zone euro : pour cette définition précise, « non disponible ». |

Autres sous-indices disponibles (même schéma, dernière date 2026-11-19), tous en `.CON` : `SS_EMN` (actions), `SS_MMN` (monétaire), `SS_FXN` (change), `SS_FIN` (intermédiaires financiers), `SS_CON` (corrélations croisées). Les anciennes versions (`SS_BM`, `SS_FI`…) sont arrêtées au 2025-05-02. Aucune série BCE publique d'écart de crédit des entreprises trouvée (indices iBoxx/ICE sous licence).

## Appels exacts qui ont fonctionné

```
J1  curl -sL "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"   (observation_date,VIXCLS ; vide = manquant)
J1  yfinance : yf.download("^VIX", period="max", auto_adjust=False)         (colonne Close)
J2  curl -sL "https://www.stoxx.com/document/Indices/Current/HistoricalData/h_v2tx.txt"
J2  (échec) yfinance "^V2TX" -> 404 Quote not found
J3  curl -sL "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
J3  curl -sL "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"
J4  curl -sL "https://fred.stlouisfed.org/graph/fredgraph.csv?id=STLFSI4"
J5  curl -sL -H "Accept: text/csv" "https://data-api.ecb.europa.eu/service/data/CISS/D.U2.Z0Z.4F.EC.SS_CIN.IDX?format=csvdata"
    (colonnes utiles : TIME_PERIOD, OBS_VALUE ; OBS_VALUE peut être vide pour le jour courant sur certaines séries pays)
J6  curl -sL "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"
J6  curl -sL "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NFCICREDIT"
J7  curl -sL -H "Accept: text/csv" "https://data-api.ecb.europa.eu/service/data/CISS/D.U2.Z0Z.4F.EC.SS_BMN.CON?format=csvdata"
    liste de toutes les séries CISS : ".../service/data/CISS/all?lastNObservations=1&format=csvdata"
```
Notes techniques : lire les .xls avec `xlrd` (pandas 3 : moteur déprécié, `python-calamine` en alternative). STOXX : `pd.read_csv(sep=";")`, `pd.to_datetime(format="%d.%m.%Y")`.

## Conditions de réutilisation (§3 règle 10)
- **VIX (FRED) et NFCICREDIT** : « Copyrighted: Citation Required » ; rediffusion de la série entière incertaine (VIX : Cboe). Yahoo : conditions Yahoo (usage personnel). À faire trancher par Georgy.
- **VSTOXX** : propriété de STOXX (Deutsche Börse) ; conditions non consultables automatiquement (403). Rediffusion à considérer comme restreinte.
- **BCE** : libre reproduction avec mention de la BCE comme source, exactitude, et indication des modifications (calculs de variation, etc.).
- **GPR** : citer Caldara et Iacoviello (2022, AER 112(4)) + « Data downloaded from https://www.matteoiacoviello.com/gpr.htm on <date> ».
- **EBP / STLFSI4** : sources Fed, aucune clause lue ; citer.

## Événements (§8.1) — dates vérifiées

Les mentions « confirmé » viennent des données FRED ou de sources officielles consultées ; les autres reposent sur la connaissance générale (non revérifiées en ligne).

| événement | date retenue | vérification |
|---|---|---|
| Crise asiatique | 2 juil. 1997 (flottement du baht thaïlandais) | non revérifié |
| Crise russe / LTCM | 17 août 1998 (défaut et dévaluation russes) ; sauvetage LTCM 23 sept. 1998 | non revérifié ; préciser « 17 août » |
| Sommet de la bulle Internet | 10 mars 2000 (clôture record du Nasdaq Composite) | non revérifié |
| 11 septembre | 11 sept. 2001 (marchés US fermés jusqu'au 17) | non revérifié |
| Lehman Brothers | 15 sept. 2008 | VIX 31,70 ce jour (confirmé) |
| Zone euro | 2 mai 2010 (plan d'aide à la Grèce) ; 10 mai 2010 (programme SMP de la BCE) | non revérifié ; proposer 2 mai |
| Draghi « Whatever it takes » | 26 juil. 2012 | VIX 17,53, en baisse (cohérent) |
| Brexit | 23 juin 2016 (vote) ; réaction de marché le 24 juin | VIX 25,76 le 24/06 (confirmé) |
| Covid | 11 mars 2020 (OMS : pandémie) ; pic du VIX le 16 mars 2020 (82,69) | pic confirmé par FRED ; l'annotation « mars 2020 » peut viser le 16 mars |
| Ukraine | 24 févr. 2022 | VIX 30,32 (cohérent) |
| SVB | 10 mars 2023 | VIX 24,80 le 10/03, 26,52 le 13/03 |
| Yen | 5 août 2024 | VIX 38,57 (confirmé) |
| Droits de douane | 2 avr. 2025 (« Liberation Day ») ; pic VIX le 8 avr. 2025 (52,33) | pic confirmé |
| QE Fed | 25 nov. 2008 (600 Md$ GSE + MBS, communiqué Fed) ; 3 nov. 2010 (QE2, 600 Md$ de Trésors) ; 13 sept. 2012 (QE3, MBS 40 Md$/mois) ; 15 mars 2020 (dimanche : taux à zéro + achats de titres, 700 Md$ selon la presse) | recoupés via federalreserve.gov et newyorkfed.org |
| QE BCE | 22 janv. 2015 (APP élargi aux titres souverains ; achats dès mars 2015) ; 18 mars 2020 (PEPP, 750 Md€) | communiqués BCE `pr150122_1` et `pr200318_1` |

**Événement récent proposé (à valider par Georgy)**
1. **5 nov. 2026 — Krach des valeurs « IA »** : S&P 500 −3,7 % (≈ 7 407), VIX de 16,61 à 28,18, troisième plus forte hausse en un jour depuis 1990. Confirmé par FRED (VIXCLS : 04/11 = 16,61 ; 05/11 = 28,18). Sources : Cboe Insights (« Week of 11/9/2026 »), 247wallst.com (6 nov. 2026), Kitco (5 nov. 2026).
2. Fin mars 2026 : VIX au-dessus de 30 (31,05 le 27 mars selon FRED), mais cause non identifiée par mes recherches : ne pas retenir sans source.

Note : le VIX remonte à nouveau (28,44 le 19 nov. selon FRED, 35,89 le 20 nov. selon Yahoo) ; épisode en cours, à suivre.
