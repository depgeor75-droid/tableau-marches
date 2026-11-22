# Tableau de bord des marchés — règles pour Claude Code

Au début de chaque session, lire AVANCEMENT.md ; la référence est SPEC_Tableau_de_bord_Marches.md.

- Interface, fiches, README, messages de commit et messages à Georgy : en français, accents corrects.
- Aucune donnée inventée, simulée ou interpolée : une série absente s'affiche « non disponible » avec la raison.
- La clé FRED ne s'écrit jamais dans un fichier suivi par git : seulement `.env` (local, ignoré) et le secret GitHub `FRED_API_KEY`. `git grep` sur la clé avant chaque push.
- Le robot GitHub (workflow « Mise à jour des données ») est seul à écrire dans `data/` : en local, `git pull` avant de travailler, ne jamais pousser de données collectées sur le PC.
- `config/indicateurs.yaml` est la source unique de vérité des séries ; les seuils sont dans `config/`.
- L'application doit marcher en `file://` : scripts classiques, pas de `fetch()` local, pas de CDN, bibliothèques dans `lib/`.
- Vert/rouge réservés aux corrélations ; variations en ▲▼ de couleur neutre.

Commandes utiles :
- Collecte : `python scripts/collect.py` · une série : `--serie B4` · contrôle : `--verifier`
- Tests : `python -m pytest scripts/tests -q` · `node --test tests_js/`
- Captures : `python scripts/captures.py`
