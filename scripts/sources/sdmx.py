"""Lecture des réponses SDMX au format CSV (BCE, BRI/BIS, OCDE, FMI…).

Les périodes sont normalisées en dates ISO au premier jour de la période :
« 2026-10 » → 2026-10-01 ; « 2026-Q3 » → 2026-07-01 ; « 2026 » → 2026-01-01 ;
« 2026-11-20 » inchangé ; « 2026-W46 » → lundi de la semaine, ou le jour donné par
`jour_semaine` (1 = lundi … 5 = vendredi : bilan hebdomadaire de la BCE, jeu ILM).

Outils communs aux modules bce, bis, ocde, fmi : lecture de toutes les séries d'un CSV
(`lire_csv_series`), correspondance d'une clé avec un motif (`cle_correspond`), regroupement
de clés qui ne diffèrent que par une dimension (`regrouper_cles`) et coupure à une date
de début (`couper`).
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date
from typing import Callable

from commun import ErreurSource, nettoyer, serie_propre

# Colonnes d'en-tête qui ne sont pas des dimensions (SDMX-CSV 1.0 / 2.0, format csvdata BCE).
COLONNES_STRUCTURE = {"KEY", "DATAFLOW", "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION"}
VALEURS_VIDES = ("", "NaN", "NA", "nan", "-")


def normaliser_periode(periode: str, jour_semaine: int = 1) -> str | None:
    p = periode.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p):
        return p
    if re.fullmatch(r"\d{4}-\d{2}", p):
        return p + "-01"
    m = re.fullmatch(r"(\d{4})-?Q([1-4])", p)
    if m:
        return f"{m.group(1)}-{(int(m.group(2)) - 1) * 3 + 1:02d}-01"
    m = re.fullmatch(r"(\d{4})-?M(\d{2})", p)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    m = re.fullmatch(r"(\d{4})-W(\d{2})", p)
    if m:
        return date.fromisocalendar(int(m.group(1)), int(m.group(2)), jour_semaine).isoformat()
    if re.fullmatch(r"\d{4}", p):
        return p + "-01-01"
    return None


def lire_csv(texte: str, colonne_periode: str = "TIME_PERIOD", colonne_valeur: str = "OBS_VALUE",
             filtres: dict[str, str] | None = None, separateur: str = ",",
             jour_semaine: int = 1) -> dict[str, float]:
    """Une série à partir d'un CSV SDMX « long » (une ligne par observation)."""
    lecteur = csv.DictReader(io.StringIO(texte.lstrip("﻿")), delimiter=separateur)
    if not lecteur.fieldnames or colonne_periode not in lecteur.fieldnames:
        raise ErreurSource("format SDMX inattendu (colonne de période absente)")
    paires = []
    for ligne in lecteur:
        if filtres and any(ligne.get(k) != v for k, v in filtres.items()):
            continue
        d = normaliser_periode(ligne.get(colonne_periode, ""), jour_semaine)
        valeur = (ligne.get(colonne_valeur) or "").strip()
        if d and valeur not in VALEURS_VIDES:
            paires.append((d, valeur))
    return serie_propre(paires)


def lire_csv_multiple(texte: str, colonne_cle: str, colonne_periode: str = "TIME_PERIOD",
                      colonne_valeur: str = "OBS_VALUE", jour_semaine: int = 1) -> dict[str, dict[str, float]]:
    """Plusieurs séries d'un même CSV, regroupées par la valeur de `colonne_cle`."""
    lecteur = csv.DictReader(io.StringIO(texte.lstrip("﻿")))
    groupes: dict[str, list] = {}
    for ligne in lecteur:
        d = normaliser_periode(ligne.get(colonne_periode, ""), jour_semaine)
        valeur = (ligne.get(colonne_valeur) or "").strip()
        if d and valeur not in VALEURS_VIDES:
            groupes.setdefault(ligne.get(colonne_cle, ""), []).append((d, valeur))
    return {cle: serie_propre(paires) for cle, paires in groupes.items()}


# ------------------------------------------------------------------ toutes les séries d'un CSV
def colonnes_dimensions(entetes: list[str], colonne_periode: str = "TIME_PERIOD") -> list[str]:
    """Colonnes de dimension : celles qui précèdent la période, hors colonnes de structure."""
    if colonne_periode not in entetes:
        raise ErreurSource("format SDMX inattendu (colonne de période absente)")
    avant = entetes[:entetes.index(colonne_periode)]
    return [c for c in avant if c.split("[")[0] not in COLONNES_STRUCTURE]


def lignes_csv(texte: str) -> tuple[list[str], list[dict[str, str]]]:
    texte = texte.lstrip("﻿")
    if texte.lstrip().startswith("<"):
        raise ErreurSource("réponse inattendue (page HTML ou XML au lieu d'un CSV)")
    lecteur = csv.DictReader(io.StringIO(texte))
    return list(lecteur.fieldnames or []), list(lecteur)


def lire_csv_series(texte: str, colonne_periode: str = "TIME_PERIOD", colonne_valeur: str = "OBS_VALUE",
                    jour_semaine: int = 1) -> dict[str, dict[str, float]]:
    """Toutes les séries d'un CSV SDMX, par clé « D1.D2.… » (valeurs des dimensions dans l'ordre)."""
    entetes, lignes = lignes_csv(texte)
    dims = colonnes_dimensions(entetes, colonne_periode)
    groupes: dict[str, list] = {}
    for ligne in lignes:
        cle = ".".join(ligne.get(c, "") for c in dims)
        d = normaliser_periode(ligne.get(colonne_periode, ""), jour_semaine)
        valeur = (ligne.get(colonne_valeur) or "").strip()
        groupes.setdefault(cle, [])
        if d and valeur not in VALEURS_VIDES:
            groupes[cle].append((d, valeur))
    return {cle: serie_propre(paires) for cle, paires in groupes.items()}


def cle_correspond(cle: str, motif: str) -> bool:
    """« M.CN » correspond à « M.CN+CH » et à « M. » (champ vide = toutes les valeurs)."""
    a, b = cle.split("."), motif.split(".")
    if len(a) != len(b):
        return False
    return all(m == "" or v in m.split("+") for v, m in zip(a, b))


def choisir_serie(series: dict[str, dict[str, float]], motif: str, nom: str) -> dict[str, float]:
    """La série unique d'une réponse qui correspond au motif ; ErreurSource sinon."""
    trouvees = [s for cle, s in series.items() if cle_correspond(cle, motif)]
    if not trouvees:
        raise ErreurSource(f"{nom} : série absente de la réponse")
    if len(trouvees) > 1:
        raise ErreurSource(f"{nom} : clé ambiguë ({len(trouvees)} séries correspondent)")
    if not trouvees[0]:
        raise ErreurSource(f"{nom} : série vide")
    return trouvees[0]


def regrouper_cles(cles: list[str], sep: str = ".") -> list[tuple[str, list[int]]]:
    """Regroupe des clés qui ne diffèrent que par UNE dimension : [(clé fusionnée « A+B », [indices])].

    Glouton : on forme d'abord le plus grand groupe possible, puis on recommence avec le reste.
    Les valeurs fusionnées sont triées (adresse d'appel déterministe).
    """
    parties = [c.split(sep) for c in cles]
    restants = list(range(len(cles)))
    groupes: list[tuple[str, list[int]]] = []
    while restants:
        meilleur: tuple[int, list[int]] | None = None
        for i in restants:
            n = len(parties[i])
            for pos in range(n):
                membres = [j for j in restants if len(parties[j]) == n
                           and all(parties[j][k] == parties[i][k] for k in range(n) if k != pos)]
                if meilleur is None or len(membres) > len(meilleur[1]):
                    meilleur = (pos, membres)
        pos, membres = meilleur
        valeurs = sorted({v for j in membres for v in parties[j][pos].split("+")})
        fusion = list(parties[membres[0]])
        fusion[pos] = "+".join(valeurs)
        groupes.append((sep.join(fusion), membres))
        restants = [j for j in restants if j not in membres]
    return groupes


def couper(serie: dict[str, float], debut: str | None) -> dict[str, float]:
    """Garde les dates ≥ debut (AAAA-MM-JJ) ; inchangé si debut est vide."""
    if not debut:
        return serie
    return {d: v for d, v in serie.items() if d >= debut}


def annee_debut(debut: str | None) -> str | None:
    """« 1989-01-01 » → « 1989 » (forme acceptée par toutes les API SDMX pour toutes les fréquences)."""
    return debut[:4] if debut else None


def separer_code(code: str, nom: str) -> tuple[str, str]:
    """« FLUX/CLE » → (FLUX, CLE)."""
    if not isinstance(code, str) or code.count("/") != 1 or not all(code.split("/")):
        raise ErreurSource(f"{nom} : code mal formé (attendu « FLUX/CLE »)")
    flux, cle = code.split("/")
    return flux.strip(), cle.strip()


def traiter_demandes(demandes: list[dict], nom: str,
                     appel: Callable[[str, str, str | None, tuple], dict[str, dict[str, float]]],
                     options_groupe: Callable[[dict], tuple] = lambda d: (),
                     apres: Callable[[dict, dict[str, float]], dict[str, float]] | None = None,
                     ) -> dict[str, dict[str, float] | ErreurSource]:
    """Moteur commun : regroupe les demandes (même flux, mêmes options de groupe, clés qui ne
    diffèrent que par une dimension), fait un appel par groupe et isole les erreurs.

    appel(flux, clé_fusionnée, début_ou_None, options) → {clé de série: série}.
    apres(demande, série) → série transformée (escalier, années observées…), appliqué avant la coupure.
    Un échec d'appel met en erreur chacune des séries du groupe, jamais les autres.
    """
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    lots: dict[tuple, list[tuple[dict, str]]] = {}
    for demande in demandes:
        try:
            flux, cle = separer_code(demande.get("code"), nom)
            lots.setdefault((flux, options_groupe(demande)), []).append((demande, cle))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(erreur))
    for (flux, options), membres in lots.items():
        for cle_fusion, indices in regrouper_cles([c for _, c in membres]):
            groupe = [membres[i] for i in indices]
            debuts = [d.get("debut") for d, _ in groupe]
            debut = None if not all(debuts) else min(debuts)
            try:
                series = appel(flux, cle_fusion, debut, options)
            except ErreurSource as erreur:
                message = nettoyer(f"{nom} {flux} : {erreur}")
                for d, _ in groupe:
                    resultats[d["cle"]] = ErreurSource(message)
                continue
            except Exception as erreur:  # réponse illisible : jamais d'arrêt de la collecte
                message = nettoyer(f"{nom} {flux} : réponse illisible ({type(erreur).__name__})")
                for d, _ in groupe:
                    resultats[d["cle"]] = ErreurSource(message)
                continue
            for d, cle in groupe:
                try:
                    serie = choisir_serie(series, cle, f"{nom} {flux}/{cle}")
                    if apres:
                        serie = apres(d, serie)
                    serie = couper(serie, d.get("debut"))
                    if not serie:
                        raise ErreurSource(f"{nom} {flux}/{cle} : aucune valeur depuis {d.get('debut')}")
                    resultats[d["cle"]] = serie
                except ErreurSource as erreur:
                    resultats[d["cle"]] = ErreurSource(nettoyer(erreur))
    return resultats
