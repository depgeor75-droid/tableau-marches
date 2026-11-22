"""Calculs côté Python (§4 « Qui calcule quoi » et §6.1).

Une série est un dict {date ISO: valeur} trié. Aucune interpolation : un trou reste un trou.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from statistics import pstdev


def phi(x: float) -> float:
    """Fonction de répartition de la loi normale centrée réduite."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ------------------------------------------------------------------ dates
def cle_mois(iso: str) -> str:
    return iso[:7] + "-01"


def an_plus_tot(iso: str) -> str:
    return f"{int(iso[:4]) - 1}{iso[4:10]}"


def ajouter_mois(iso: str, n: int) -> str:
    a, m = int(iso[:4]), int(iso[5:7]) - 1 + n
    return f"{a + m // 12:04d}-{m % 12 + 1:02d}-01"


# ---------------------------------------------------------- transformations
def glissement_annuel(serie: dict[str, float]) -> dict[str, float]:
    """valeur(t) ÷ valeur(même mois / trimestre un an plus tôt) − 1, en %, apparié PAR DATE.
    Les séries mensuelles/trimestrielles sont datées au premier jour de la période."""
    sortie = {}
    for d, v in serie.items():
        ancien = serie.get(an_plus_tot(d))
        if ancien is None or ancien <= 0 or v is None or v <= 0:
            continue
        sortie[d] = (v / ancien - 1) * 100
    return sortie


def ecart(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    """a − b aux dates communes (en points de %)."""
    return {d: a[d] - b[d] for d in a if d in b}


def croise(numerateur: dict[str, float], denominateur: dict[str, float]) -> dict[str, float]:
    """Taux croisé : numérateur ÷ dénominateur aux dates communes (ex. USD/JPY = JPY/EUR ÷ USD/EUR)."""
    return {d: numerateur[d] / denominateur[d] for d in numerateur if d in denominateur and denominateur[d]}


def produit(a: dict[str, float], b: dict[str, float], facteur: float = 1.0) -> dict[str, float]:
    return {d: a[d] * b[d] * facteur for d in a if d in b}


def inverse(a: dict[str, float]) -> dict[str, float]:
    return {d: 1 / v for d, v in a.items() if v}


# ------------------------------------------------------------- fréquences
def mensualiser(serie: dict[str, float], methode: str = "fin") -> dict[str, float]:
    """Valeur de fin de mois (dernière observation du mois), datée au 1er du mois.
    methode="moyenne" : moyenne des observations du mois."""
    groupes: dict[str, list[float]] = {}
    for d, v in serie.items():
        groupes.setdefault(cle_mois(d), []).append(v)
    if methode == "moyenne":
        return {m: sum(vs) / len(vs) for m, vs in sorted(groupes.items())}
    return {m: vs[-1] for m, vs in sorted(groupes.items())}


def mois_complets(serie_mensuelle: dict[str, float], aujourd_hui: date) -> dict[str, float]:
    """Retire le mois calendaire en cours (« mois complets uniquement » dans l'historique)."""
    mois_courant = aujourd_hui.isoformat()[:7] + "-01"
    return {m: v for m, v in serie_mensuelle.items() if m < mois_courant}


def filtrer_depuis(serie: dict[str, float], debut: str) -> dict[str, float]:
    return {d: v for d, v in serie.items() if d >= debut}


# --------------------------------------------------------------- variations
def valeur_a_date(serie: dict[str, float], cible: str, tolerance_jours: int) -> tuple[str, float] | None:
    """Dernière observation à la date cible ou juste avant (dans la tolérance)."""
    meilleure = None
    for d in serie:
        if d <= cible:
            meilleure = d
        else:
            break
    if meilleure is None:
        return None
    if (date.fromisoformat(cible) - date.fromisoformat(meilleure)).days > tolerance_jours:
        return None
    return meilleure, serie[meilleure]


def variation(type_serie: str, avant: float | None, apres: float | None) -> float | None:
    """En points pour T et N* ; en % pour N (non calculée si une valeur est ≤ 0)."""
    if avant is None or apres is None:
        return None
    if type_serie == "N":
        if avant <= 0 or apres <= 0:
            return None
        return (apres / avant - 1) * 100
    return apres - avant


def recul(iso: str, mois: int = 0, jours: int = 0) -> str:
    d = date.fromisoformat(iso[:10])
    if mois:
        a, m = d.year, d.month - 1 - mois
        a += m // 12
        m = m % 12 + 1
        jour = min(d.day, [31, 29 if a % 4 == 0 and (a % 100 or a % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
        d = date(a, m, jour)
    return (d - timedelta(days=jours)).isoformat()


def tolerance(frequence: str) -> int:
    return {"J": 7, "S": 10, "M": 40, "T": 100, "A": 380}[frequence]


def variations_1m_1a(serie: dict[str, float], type_serie: str, frequence: str) -> dict:
    if not serie:
        return {"1m": None, "1a": None}
    derniere = max(serie)
    v = serie[derniere]
    sortie = {}
    for cle, mois in (("1m", 1), ("1a", 12)):
        if cle == "1m" and frequence in ("T", "A"):
            sortie[cle] = None
            continue
        if frequence in ("M", "T", "A"):  # appariement exact : jamais à cheval sur un trou
            avant = serie.get(ajouter_mois(derniere, -mois))
        else:
            point = valeur_a_date(serie, recul(derniere, mois=mois), tolerance(frequence))
            avant = point[1] if point else None
        sortie[cle] = variation(type_serie, avant, v)
    return sortie


# -------------------------------------------------------------- percentiles
LIBELLES_PERCENTILE = [(10, "très bas"), (25, "bas"), (75, "habituel"), (90, "élevé"), (101, "très élevé")]


def libelle_percentile(p: float, bornes=(10, 25, 75, 90)) -> str:
    noms = ["très bas", "bas", "habituel", "élevé", "très élevé"]
    for borne, libelle in zip(list(bornes) + [101], noms):
        if p < borne:
            return libelle
    return "très élevé"


def rang_percentile(historique: list[float], valeur: float) -> float:
    """Part (en %) des observations strictement inférieures + moitié des égales (rang moyen)."""
    if not historique:
        return float("nan")
    inf = sum(1 for x in historique if x < valeur)
    egal = sum(1 for x in historique if x == valeur)
    return (inf + 0.5 * egal) / len(historique) * 100


def percentile_carte(mensuel: dict[str, float], type_serie: str, valeur_courante: float | None = None,
                     annees_max: int = 30, annees_court: int = 10, annees_min: int = 5, bornes=(10, 25, 75, 90)) -> dict | None:
    """Position de la valeur de la carte dans l'historique mensuel (mois complets, 30 ans au plus).
    Types T et N* : rang du niveau ; type N : rang de la variation sur 12 mois
    (`valeur_courante` = alors la variation sur 1 an de la carte). Affichage borné à 1-99."""
    if not mensuel:
        return None
    base_nom = "variation_12m" if type_serie == "N" else "niveau"
    base = mensuel if type_serie != "N" else glissement_annuel(mensuel)
    if not base:
        return {"valeur": None, "raison": "historique_court", "base": base_nom}
    derniere = max(base)
    debut_max = f"{int(derniere[:4]) - annees_max}{derniere[4:]}"
    fenetre = {d: v for d, v in base.items() if d > debut_max}
    premier = min(fenetre)
    duree_annees = (date.fromisoformat(derniere) - date.fromisoformat(premier)).days / 365.25 + 1 / 12
    if duree_annees < annees_min:
        return {"valeur": None, "raison": "historique_court", "depuis": premier[:4], "base": base_nom}
    cible = base[derniere] if valeur_courante is None else valeur_courante
    p = rang_percentile(list(fenetre.values()), cible)
    p_affiche = min(99, max(1, round(p)))
    return {"valeur": p_affiche, "libelle": libelle_percentile(p_affiche, bornes), "depuis": premier[:4],
            "court": duree_annees < annees_court, "base": base_nom}


def percentile_valeur(mensuel: dict[str, float], valeur: float, annees_max: int = 30) -> tuple[float, str] | None:
    """Percentile d'une valeur donnée dans l'historique mensuel (pour les jauges)."""
    if not mensuel:
        return None
    derniere = max(mensuel)
    debut_max = f"{int(derniere[:4]) - annees_max}{derniere[4:]}"
    fenetre = [v for d, v in mensuel.items() if d > debut_max]
    return rang_percentile(fenetre, valeur), min(d for d in mensuel if d > debut_max)[:4]


# ------------------------------------------------------- « ce qui a bougé »
def score_mouvement(serie_quotidienne: dict[str, float], type_serie: str, annees: int = 5,
                    jours: int = 7) -> dict | None:
    """Variation sur 7 jours calendaires (≈ 5 jours ouvrables) ÷ écart-type des variations sur
    7 jours des 5 dernières années. La valeur « 7 jours plus tôt » est la dernière observation
    à cette date ou juste avant (tolérance 4 jours) : juste pour les séries 7 jours sur 7 et à trous."""
    if len(serie_quotidienne) < 300:
        return None
    dates = list(serie_quotidienne)
    derniere = dates[-1]
    limite = recul(derniere, mois=12 * annees)
    sous = {d: serie_quotidienne[d] for d in dates if d >= recul(limite, jours=jours + 4)}
    variations = []
    for d in sous:
        if d < limite:
            continue
        point = valeur_a_date(sous, recul(d, jours=jours), 4)
        if point:
            v = variation(type_serie, point[1], sous[d])
            if v is not None:
                variations.append(v)
    if len(variations) < 200:
        return None
    ecart_type = pstdev(variations)
    point = valeur_a_date(serie_quotidienne, recul(derniere, jours=jours), 4)
    if not point or not ecart_type:
        return None
    actuelle = variation(type_serie, point[1], serie_quotidienne[derniere])
    if actuelle is None:
        return None
    return {"variation": actuelle, "rapport": actuelle / ecart_type, "depuis": point[0], "jusqua": derniere}


# --------------------------------------------------------------- direction
def direction(serie: dict[str, float], type_serie: str, demi_ecart: float = 0.5, mois: int = 3) -> dict | None:
    """▲ ▼ ▶ : variation sur 3 mois comparée à la moitié de l'écart-type historique des
    variations sur 3 mois. Valeur « 3 mois plus tôt » cherchée PAR DATE (mensuel ou trimestriel).
    Pour N, variations en % ; pour T et N*, en points."""
    variations = []
    for d, v in serie.items():
        avant = serie.get(ajouter_mois(d, -mois))
        var = variation(type_serie, avant, v)
        if var is not None:
            variations.append(var)
    if len(variations) < 24:
        return None
    seuil = demi_ecart * pstdev(variations)
    derniere = max(serie)
    v = variation(type_serie, serie.get(ajouter_mois(derniere, -mois)), serie[derniere])
    if v is None:
        return None
    fleche = "▲" if v > seuil else "▼" if v < -seuil else "▶"
    return {"fleche": fleche, "variation": v, "seuil": seuil, "date": derniere}


def probabilite_recession(ecart_10a_3m: float, alpha: float, beta: float) -> float:
    """Modèle de la Fed de New York : P = Φ(α + β × écart), en %."""
    return phi(alpha + beta * ecart_10a_3m) * 100
