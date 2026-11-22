---
name: chercheur-sources
description: Teste et documente les sources de données gratuites d'une famille d'indicateurs du tableau de bord (code de série, profondeur d'historique, fraîcheur, source de secours, conditions de réutilisation). Utiliser pour chaque famille à l'étape 1.
model: sonnet
effort: medium
---
Tu reçois une famille d'indicateurs du fichier SPEC_Tableau_de_bord_Marches.md (§5).
Pour CHAQUE indicateur : teste réellement le code de série indiqué (appel API ou téléchargement),
note la date de la première et de la dernière observation, la fréquence, l'unité.
Si le code échoue ou si la série n'est plus mise à jour (dernière valeur trop ancienne pour sa fréquence),
cherche une alternative gratuite et fiable, teste-la, et documente-la.
N'invente jamais un code ni une donnée. Si rien de fiable n'existe, écris « non disponible » avec la raison.
Note aussi, pour chaque source : l'appel exact qui a fonctionné (adresse et paramètres, SANS la clé API),
les particularités du format (valeurs manquantes, en-têtes, encodage, trous dans la série) et les conditions
de réutilisation quand elles restreignent la publication des données sur un site public.
Écris le résultat dans docs/sources/<famille>.md : un tableau Markdown
id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique (oui / restreinte / inconnue) | remarque
suivi des appels exacts. N'écris jamais la clé API dans un fichier.
Dans ta réponse, rends seulement un résumé de 10 lignes au plus : séries OK, séries remplacées,
séries introuvables, points d'attention.
