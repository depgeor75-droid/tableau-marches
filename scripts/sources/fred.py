"""FRED (Banque fédérale de réserve de Saint-Louis) — API officielle avec clé gratuite.

La clé est lue dans FRED_API_KEY (fichier .env en local, secret GitHub en ligne). L'adresse
d'appel contient la clé : les messages d'erreur passent TOUJOURS par commun.nettoyer().
Secours sans clé : téléchargement CSV fredgraph (même contenu).
"""
from __future__ import annotations

import csv
import io
import os
import time

from commun import ErreurSource, nettoyer, serie_propre
from commun import telecharger as requete

URL_API = "https://api.stlouisfed.org/fred/series/observations"
URL_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


# Le secours CSV sans clé relève de la collecte hors API, que les conditions de FRED
# n'autorisent pas sans accord : désactivé par défaut (PLAN §2, C12). Une clé refusée
# apparaît donc comme une erreur.
SECOURS_CSV = False


def telecharger(demandes: list[dict]) -> dict:
    """Interface commune : {cle: série | ErreurSource}. 0,3 s entre deux appels."""
    resultats = {}
    for i, demande in enumerate(demandes):
        if i:
            time.sleep(0.3)
        try:
            resultats[demande["cle"]] = telecharger_serie(demande["code"], demande.get("debut", "1989-01-01"))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = erreur
    return resultats


def telecharger_serie(code: str, debut: str = "1989-01-01") -> dict[str, float]:
    cle = os.environ.get("FRED_API_KEY")
    if cle:
        try:
            reponse = requete(URL_API, params={
                "series_id": code, "api_key": cle, "file_type": "json", "observation_start": debut,
            })
            donnees = reponse.json()
            if "observations" not in donnees:
                raise ErreurSource(nettoyer(f"réponse FRED inattendue pour {code}"))
            return serie_propre((o["date"], None if o["value"] in (".", "") else o["value"])
                                for o in donnees["observations"])
        except (ErreurSource, ValueError) as erreur:
            premiere = nettoyer(erreur)
        else:  # pragma: no cover
            premiere = None
    else:
        premiere = "clé FRED absente"
    if not SECOURS_CSV:
        raise ErreurSource(nettoyer(f"FRED {code} : {premiere}"))
    # Secours : CSV public, sans clé
    try:
        reponse = requete(URL_CSV, params={"id": code, "cosd": debut})
        lecteur = csv.reader(io.StringIO(reponse.text))
        next(lecteur, None)
        serie = serie_propre((ligne[0], ligne[1] or None) for ligne in lecteur if len(ligne) >= 2)
        if not serie:
            raise ErreurSource(f"série FRED {code} vide")
        return serie
    except ErreurSource as erreur:
        raise ErreurSource(nettoyer(f"FRED {code} : {premiere} ; secours CSV : {erreur}")) from None
