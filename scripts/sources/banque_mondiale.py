"""Banque mondiale — « Pink Sheet », prix mensuels des matières premières (secours de H1-H6).

L'adresse du classeur change à chaque publication : elle est lue à chaque usage sur la page
`commodity-markets` (motif `CMO-Historical-Data-Monthly.xlsx`). Feuille `Monthly Prices` :
ligne des noms de séries (« Crude oil, Brent »…), ligne des unités, puis une ligne par mois,
période texte `1960M01` → 1960-01-01. Valeurs manquantes = caractère non numérique (trou).

Demande : {"cle": "H1", "code": "Crude oil, Brent"} — `code` = nom exact de la colonne
(comparaison sans tenir compte de la casse, des espaces multiples ni des « * »).
Colonnes utiles : "Crude oil, Brent", "Crude oil, WTI", "Gold", "Natural gas, Europe",
"Natural gas, US", "Copper" (USD/tonne). Un seul téléchargement pour toutes les demandes.
"""
from __future__ import annotations

import re

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import decoder, lire_classeur, nombre, normaliser_nom
except ImportError:
    from formats import decoder, lire_classeur, nombre, normaliser_nom

PAGE = "https://www.worldbank.org/en/research/commodity-markets"
FEUILLE = "Monthly Prices"
_LIEN = re.compile(r"""https?://[^"'\s<>]*CMO-Historical-Data-Monthly\.xlsx""", re.I)
_PERIODE = re.compile(r"^(\d{4})M(\d{2})$")


def extraire_lien(html: str) -> str:
    m = _LIEN.search(html)
    if not m:
        raise ErreurSource("Banque mondiale : lien du classeur mensuel introuvable sur la page")
    return m.group(0).replace("&amp;", "&")


def periode_iso(texte) -> str | None:
    m = _PERIODE.match(str(texte or "").strip())
    if not m or not 1 <= int(m.group(2)) <= 12:
        return None
    return f"{m.group(1)}-{m.group(2)}-01"


def lire_prix_mensuels(lignes: list[list]) -> dict[str, dict[str, float]]:
    """{nom normalisé de colonne: série} à partir des lignes de la feuille `Monthly Prices`."""
    i_noms = None
    for i, ligne in enumerate(lignes[:20]):
        noms = {normaliser_nom(c) for c in ligne if c}
        if "crude oil, brent" in noms or "gold" in noms:
            i_noms = i
            break
    if i_noms is None:
        raise ErreurSource("Banque mondiale : ligne des noms de séries introuvable")
    entete = [normaliser_nom(c) for c in lignes[i_noms]]
    paires: dict[str, list] = {nom: [] for nom in entete if nom}
    for ligne in lignes[i_noms + 1:]:
        if not ligne:
            continue
        d = periode_iso(ligne[0])
        if not d:
            continue
        for j, nom in enumerate(entete):
            if nom and j < len(ligne):
                paires[nom].append((d, nombre(ligne[j])))
    return {nom: serie_propre(p) for nom, p in paires.items()}


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    if not demandes:
        return {}
    try:
        page = get(PAGE)
        lien = extraire_lien(decoder(page.content))
        feuilles = lire_classeur(get(lien).content, "classeur de la Banque mondiale")
        if FEUILLE not in feuilles:
            raise ErreurSource(f"Banque mondiale : feuille « {FEUILLE} » absente")
        table = lire_prix_mensuels(feuilles[FEUILLE])
    except ErreurSource as erreur:
        e = ErreurSource(nettoyer(erreur))
        return {d["cle"]: e for d in demandes}
    except Exception as erreur:
        e = ErreurSource(nettoyer(f"Banque mondiale : erreur inattendue ({type(erreur).__name__})"))
        return {d["cle"]: e for d in demandes}
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for demande in demandes:
        serie = table.get(normaliser_nom(demande["code"]))
        if serie is None:
            resultats[demande["cle"]] = ErreurSource(f"Banque mondiale : colonne « {demande['code']} » absente")
        elif not serie:
            resultats[demande["cle"]] = ErreurSource(f"Banque mondiale : colonne « {demande['code']} » vide")
        else:
            resultats[demande["cle"]] = serie
    return resultats
