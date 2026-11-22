"""Fusion des séries téléchargées avec les données existantes, raccords de sources,
et contrôle de fraîcheur (§5 « Raccord de sources », §6 « Validation » et règle 7 du §3).
"""
from __future__ import annotations

from datetime import date, timedelta

# Garde-fou contre les réponses tronquées
PERTE_MAX_POINTS = 0.05     # plus de 5 % de points perdus → on garde l'ancienne série
RETARD_DEBUT_MAX_JOURS = 45  # la nouvelle série commence « nettement plus tard »


def fusionner(ancienne: dict[str, float] | None, nouvelle: dict[str, float] | None):
    """Retourne (série retenue, anomalie | None).

    - nouvelle série valide → elle remplace l'ancienne (révisions prises en compte) ;
    - échec (None ou vide) → on garde l'ancienne ;
    - réponse tronquée (début nettement plus tardif, ou > 5 % de points perdus) → on garde
      l'ancienne et on signale l'anomalie.
    """
    if not nouvelle:
        return (ancienne or {}), None
    if not ancienne:
        return nouvelle, None
    debut_ancien = date.fromisoformat(min(ancienne))
    debut_nouveau = date.fromisoformat(min(nouvelle))
    if (debut_nouveau - debut_ancien).days > RETARD_DEBUT_MAX_JOURS:
        return ancienne, (f"réponse tronquée : la série reçue commence le {debut_nouveau.isoformat()} "
                          f"au lieu du {debut_ancien.isoformat()} ; anciennes données conservées")
    communs_anciens = [d for d in ancienne if d >= min(nouvelle)]
    if len(nouvelle) < len(ancienne) * (1 - PERTE_MAX_POINTS) or \
            (communs_anciens and len([d for d in communs_anciens if d in nouvelle]) < len(communs_anciens) * (1 - PERTE_MAX_POINTS)):
        return ancienne, (f"réponse tronquée : {len(nouvelle)} points reçus contre {len(ancienne)} ; "
                          "anciennes données conservées")
    return nouvelle, None


def ecart_raccord(type_serie: str, a: float, b: float) -> float:
    """Écart au point de raccord : en % pour N, en points pour T et N*."""
    if type_serie == "N":
        if a == 0:
            return float("inf")
        return abs(b / a - 1) * 100
    return abs(b - a)


def raccorder(type_serie: str, principale: dict[str, float], rapide: dict[str, float]):
    """Prolonge la série principale par les jours récents de la source rapide.

    Raccord à la dernière date commune ; les jours postérieurs viennent de la source rapide et
    sont provisoires. Retourne (série, dates provisoires, info du raccord).
    Seuils : N < 2 % ; T et N* < 0,10 point (sinon l'écart est signalé).
    """
    if not principale:
        return dict(rapide), sorted(rapide), {"date": None, "ecart": None, "alerte": "source principale vide"}
    if not rapide:
        return dict(principale), [], None
    communes = sorted(set(principale) & set(rapide))
    if not communes:
        return dict(principale), [], {"date": None, "ecart": None, "alerte": "aucune date commune entre les deux sources"}
    jonction = communes[-1]
    ecart = ecart_raccord(type_serie, principale[jonction], rapide[jonction])
    seuil = 2.0 if type_serie == "N" else 0.10
    serie = dict(principale)
    provisoires = sorted(d for d in rapide if d > jonction)
    for d in provisoires:
        serie[d] = rapide[d]
    info = {"date": jonction, "ecart": round(ecart, 4), "alerte": None}
    if ecart >= seuil:
        unite = "%" if type_serie == "N" else "point"
        info["alerte"] = f"écart de {ecart:.2f} {unite} au point de raccord du {jonction} (seuil {seuil:g})"
    return dict(sorted(serie.items())), provisoires, info


# --------------------------------------------------------------- fraîcheur
SEUILS_DEFAUT = {"J": 5, "S": 14, "M": 75, "T": 120, "A": 450}  # voir config/reglages.yaml


def jours_ouvrables_entre(debut: date, fin: date) -> int:
    n, d = 0, debut
    while d < fin:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def fin_de_periode(derniere: date, frequence: str) -> date:
    if frequence == "M":
        suivant = date(derniere.year + (derniere.month == 12), derniere.month % 12 + 1, 1)
        return suivant - timedelta(days=1)
    if frequence == "T":
        mois_fin = ((derniere.month - 1) // 3) * 3 + 3
        suivant = date(derniere.year + (mois_fin == 12), mois_fin % 12 + 1, 1)
        return suivant - timedelta(days=1)
    if frequence == "A":
        return date(derniere.year, 12, 31)
    return derniere


def est_en_retard(derniere_iso: str, frequence: str, aujourd_hui: date,
                  seuils: dict | None = None, retard_max_jours: int | None = None) -> tuple[bool, str]:
    """Règles du §6 : quotidien 5 jours ouvrables ; hebdo 14 j ; mensuel 75 j après la fin du mois
    observé ; trimestriel 4 mois après la fin du trimestre ; annuel 15 mois après la fin de l'année.
    `retard_max_jours` (par série) remplace la règle : jours calendaires après la fin de la période."""
    s = {**SEUILS_DEFAUT, **(seuils or {})}
    derniere = date.fromisoformat(derniere_iso[:10])
    fin = fin_de_periode(derniere, frequence)
    if retard_max_jours is not None:
        ecoule = (aujourd_hui - fin).days
        return ecoule > retard_max_jours, f"{ecoule} jours après la fin de la période (tolérance {retard_max_jours})"
    if frequence == "J":
        ecoule = jours_ouvrables_entre(derniere, aujourd_hui)
        return ecoule > s["J"], f"{ecoule} jours ouvrables depuis la dernière valeur (tolérance {s['J']})"
    ecoule = (aujourd_hui - fin).days
    return ecoule > s[frequence], f"{ecoule} jours après la fin de la période (tolérance {s[frequence]})"
