# Affirmations incertaines signalées par les rédacteurs (à trancher par le relecteur)

## Lot énergie (H)
Tranché par la session principale (faits de référence établis) : 159 litres par baril ; WTI négatif du 20/04/2020 lié à la saturation des stockages à l'échéance du contrat ; once troy ≈ 31,1 g ; 1 MWh ≈ 3,41 mmbtu ; Henry Hub en Louisiane ; livre ≈ 454 g ; nom complet de DBC (Invesco DB Commodity Index Tracking Fund) ; regroupement d'actions d'USO (1 pour 8) en avril 2020 ; GLD détient de l'or physique ; les REIT américaines distribuent l'essentiel de leurs bénéfices ; TTF = point d'échange virtuel aux Pays-Bas ; crise du gaz de 2022 liée à la guerre en Ukraine ; point bas de mai 2020 lié aux confinements. Comportement voulu : raccord H2 refusé au-delà de 2 % d'écart (courbe arrêtée à la dernière valeur FRED).
Reste à vérifier : H11 (composition de l'indice, Royaume-Uni inclus ou non) ; H14 (« moins fiable » car peu liquide : inférence) ; H13 (« repère le plus proche : 10 ans », interprétation).

## Lot bourses (G, K)
Corrigé : mentions de G6 (DAX, indice de performance) et G13 (IWDA, ETF de capitalisation) — elles ne disent plus « hors dividendes ».
Tranché (faits établis) : Nikkei 225 et Dow Jones pondérés par les prix ; DAX à 40 valeurs depuis 2021 ; FTSE = Financial Times Stock Exchange ; CAC = Cotation assistée en continu ; NASDAQ = National Association of Securities Dealers Automated Quotations ; dollar de Hong Kong arrimé au dollar américain ; Euro Stoxx 50 sans sociétés britanniques ni suisses ; SIR belges tenues de distribuer au moins 80 % de leur résultat net.
Reste à vérifier : G11 (dividendes de l'ETF 510300) ; G10 (formulations sur les petits porteurs et les sociétés contrôlées par l'État) ; G6 (« en partie parce que le DAX compte les dividendes »).

## Lot risques et transversales (J, t:)
ATTENTION : l'historique mensuel des séries quotidiennes (data/*_historique.js) contient la valeur de FIN DE MOIS, pas la moyenne mensuelle : vérifier que les fiches J1-J7 ne parlent pas de « moyennes mensuelles ».
Tranché : VSTOXX calculé sur les options de l'Euro Stoxx 50 (STOXX, groupe Deutsche Börse) ; CISS compris entre 0 et 1 par construction ; l'inversion de la courbe a souvent précédé les récessions américaines avec un délai variable ; le CAC 40 est un indice de prix.
À vérifier : J3 (base 100 = moyenne 1985-2019 ? la fiche l'affirme) ; J7 (signification exacte de « contribution » SS_BMN.CON) ; J6 (définition de l'écart GZ) ; t:spread contient un exemple chiffré hypothétique (à reformuler sans chiffres si jugé contraire à la règle « aucune donnée inventée »).

## Lot taux (A, B, écarts)
ATTENTION (même remarque) : pour les séries QUOTIDIENNES (A1, A2, A4, B1-B5, B9, B10, BC_10A2A, BC_10A3M), l'historique mensuel contient la valeur de fin de mois, pas une moyenne mensuelle. Seules A3, A5, A6, A7, B6-B8, B12 et les écarts européens sont des moyennes ou valeurs mensuelles publiées.
Tranché : taux effectif des fonds fédéraux = médiane pondérée par les volumes des prêts au jour le jour ; Conseil des gouverneurs (BCE) et comité de politique monétaire (Banque d'Angleterre) ; Euribor depuis 1999 (série synthétique avant) ; LPR établie à partir des propositions de banques ; rendement « au pair » (B9) ; BNS et taux négatifs (−0,75 %) ; critère de convergence de Maastricht pour les taux à 10 ans Eurostat.
À vérifier : exemples arithmétiques (BC_10A2A, BC_10A3M : chiffres d'illustration) ; B6 (« pas le taux des bons d'État vendus aux particuliers ») ; A4 (« publié avec quelques jours de retard »).

## Lot inflation et anticipations (C, D)
Tranché (faits établis) : objectifs d'inflation de 2 % (Fed sur le PCE ; BCE à moyen terme ; Banque d'Angleterre ; Banque du Japon) ; TIPS indexés sur l'IPC ; champ plus large du PCE ; PCEPI désaisonnalisé ; l'indexation belge utilise l'indice santé national, pas l'IPCH ; hausse de la taxe japonaise sur la consommation en avril 2014 ; MICH = réponse médiane ; WEO publié en avril et octobre ; PPIACO = prix des biens (« all commodities ») ; G4E = Allemagne, France, Italie, Royaume-Uni.
À vérifier : D11 (effet de composition d'avril 2020) ; D10 (révisions du GSCPI) ; D12 (primes uniques) ; liens t:contrat_a_terme → t:future.

## Lot croissance, dette, banques centrales, devises (E, F, I)
ATTENTION (même remarque) : devises (I1-I5, IC) et bilans hebdomadaires (F1, F2) = valeurs de FIN DE MOIS dans l'historique, pas des moyennes mensuelles.
Tranché (faits établis) : abandon du cours plancher EUR/CHF par la BNS le 15 janvier 2015 ; baisse de la livre après le référendum du Brexit (23 juin 2016) ; yuan encadré par les autorités chinoises (quasi fixe à 8,28 jusqu'en juillet 2005) ; yen et franc suisse valeurs refuges ; composition générale des bilans (Fed : bons du Trésor et titres hypothécaires ; BoJ : obligations d'État japonaises ; BoE : gilts via l'Asset Purchase Facility) ; EUR/USD paire la plus échangée ; euro né le 1er janvier 1999, premières cotations le 4 janvier 1999 ; dernière année observée par le FMI propre à chaque série et à chaque pays.
À vérifier : définitions de M2 et M3 ; F5 (« périmètres des bilans pas strictement identiques ») ; E3 Belgique 139 % en 1993 = maximum de la série FMI (le dire ainsi).
