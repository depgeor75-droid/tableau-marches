"""Eurostat — API de diffusion 1.0, format JSON-stat 2.0, sans clé.

Interface : telecharger(demandes) -> {cle: série | ErreurSource}.

Une demande : {"cle": "B6", "code": "irt_lt_mcby_m", "filtres": {"geo": "BE"}, …options}
  code     nom du jeu Eurostat (ex. « namq_10_gdp », « gov_10q_ggdebt », « prc_hicp_minr »).
  filtres  {dimension: valeur} ; toute dimension du jeu qui compte plusieurs valeurs dans la
           réponse doit être filtrée (sinon : erreur « filtre manquant »), « time » excepté.
  debut    « AAAA-MM-JJ » facultatif : coupure locale (l'historique complet est demandé, ce qui
           évite d'avoir à écrire `sinceTimePeriod` selon la fréquence du jeu).

Regroupement : les demandes d'un même jeu, avec les mêmes dimensions filtrées, qui ne diffèrent
que par la valeur d'UNE dimension partent en un seul appel (ex. irt_lt_mcby_m pour
geo=BE, DE, FR, IT) ; un échec d'appel met en erreur chacune de ses séries, jamais les autres.

Dates : « 2026-10 » → 2026-10-01 ; « 2026-Q3 » → 2026-07-01 ; « 2026 » → 2026-01-01.
"""
from __future__ import annotations

from commun import ErreurSource, nettoyer, serie_propre, telecharger as http
from sources.sdmx import couper, normaliser_periode, regrouper_cles

URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{jeu}"
ATTENTE = 4.0
NOM = "Eurostat"
SEP = "\x1f"  # séparateur interne des valeurs de filtres (les codes Eurostat contiennent « . » rarement)


def lire_jsonstat(donnees: dict) -> tuple[list[str], list[int], dict[str, dict[str, int]], dict[int, float]]:
    """(identifiants des dimensions, tailles, index des catégories par dimension, valeurs par position)."""
    if "error" in donnees and "value" not in donnees:
        raise ErreurSource("réponse d'erreur d'Eurostat")
    ids, tailles = donnees["id"], donnees["size"]
    index = {}
    for dim in ids:
        categories = donnees["dimension"][dim]["category"]["index"]
        if isinstance(categories, list):
            categories = {code: i for i, code in enumerate(categories)}
        index[dim] = categories
    brutes = donnees.get("value", {})
    if isinstance(brutes, list):
        valeurs = {i: v for i, v in enumerate(brutes) if v is not None}
    else:
        valeurs = {int(k): v for k, v in brutes.items() if v is not None}
    return ids, tailles, index, valeurs


def extraire_serie(donnees: dict, filtres: dict[str, str]) -> dict[str, float]:
    """Une série d'une réponse JSON-stat, choisie par ses filtres (toutes dimensions sauf time)."""
    ids, tailles, index, valeurs = lire_jsonstat(donnees)
    if "time" not in ids:
        raise ErreurSource("réponse sans dimension de temps")
    pas, produit = [0] * len(ids), 1
    for k in range(len(ids) - 1, -1, -1):
        pas[k] = produit
        produit *= tailles[k]
    base = 0
    for k, dim in enumerate(ids):
        if dim == "time":
            continue
        if dim in filtres:
            if filtres[dim] not in index[dim]:
                raise ErreurSource(f"aucune donnée pour {dim}={filtres[dim]}")
            base += index[dim][filtres[dim]] * pas[k]
        elif tailles[k] == 1:
            continue
        else:
            raise ErreurSource(f"filtre manquant pour la dimension {dim}")
    k_temps = ids.index("time")
    paires = []
    for periode, i in index["time"].items():
        position = base + i * pas[k_temps]
        if position in valeurs:
            paires.append((normaliser_periode(periode), valeurs[position]))
    return serie_propre((d, v) for d, v in paires if d)


def _appel(jeu: str, filtres_multiples: dict[str, list[str]]) -> dict:
    params: list[tuple[str, str]] = [("format", "JSON"), ("lang", "EN")]
    for dim, valeurs in filtres_multiples.items():
        params.extend((dim, v) for v in valeurs)
    reponse = http(URL.format(jeu=jeu), params=params, attente=ATTENTE)
    return reponse.json()


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    lots: dict[tuple, list[dict]] = {}
    for d in demandes:
        jeu, filtres = d.get("code"), d.get("filtres") or {}
        if not jeu or not isinstance(filtres, dict):
            resultats[d["cle"]] = ErreurSource(f"{NOM} : demande mal formée (code ou filtres)")
            continue
        lots.setdefault((jeu, tuple(sorted(filtres))), []).append(d)
    for (jeu, dims), membres in lots.items():
        cles = [SEP.join(str(m["filtres"][dim]) for dim in dims) for m in membres] if dims else [""] * len(membres)
        for cle_fusion, indices in regrouper_cles(cles, sep=SEP):
            groupe = [membres[i] for i in indices]
            multiples = {dim: v.split("+") for dim, v in zip(dims, cle_fusion.split(SEP))} if dims else {}
            try:
                donnees = _appel(jeu, multiples)
            except ErreurSource as erreur:
                for m in groupe:
                    resultats[m["cle"]] = ErreurSource(nettoyer(f"{NOM} {jeu} : {erreur}"))
                continue
            except ValueError:
                for m in groupe:
                    resultats[m["cle"]] = ErreurSource(f"{NOM} {jeu} : réponse illisible")
                continue
            for m in groupe:
                description = ",".join(f"{k}={v}" for k, v in sorted(m["filtres"].items()))
                try:
                    serie = couper(extraire_serie(donnees, {k: str(v) for k, v in m["filtres"].items()}), m.get("debut"))
                    if not serie:
                        raise ErreurSource("série vide")
                    resultats[m["cle"]] = serie
                except ErreurSource as erreur:
                    resultats[m["cle"]] = ErreurSource(nettoyer(f"{NOM} {jeu} ({description}) : {erreur}"))
                except (KeyError, TypeError, ValueError) as erreur:
                    resultats[m["cle"]] = ErreurSource(nettoyer(f"{NOM} {jeu} : réponse illisible ({type(erreur).__name__})"))
    return resultats
