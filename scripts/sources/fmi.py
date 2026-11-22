"""FMI — API SDMX 2.1 du nouveau portail (api.imf.org/external/sdmx/2.1), réponse CSV, sans clé.

Le FMI interdit le téléchargement automatisé en masse : un appel par groupe de séries, pauses
entre appels, 20 s d'attente entre essais (C10), et aucune réponse n'est demandée deux fois
dans une même exécution (cache en mémoire ; une réponse WEO couvrant plus de pays sert aussi
aux demandes portant sur une partie d'entre eux).

Interface : telecharger(demandes) -> {cle: série | ErreurSource}.

Une demande : {"cle": "C12", "code": "CPI/JPN.CPI._T.YOY_PCH_PA_PT.M", …options}
  code    « FLUX/CLE ». Flux « CPI » (IMF.STA:CPI, clé COUNTRY.INDEX_TYPE.COICOP_1999.
          TYPE_OF_TRANSFORMATION.FREQUENCY) ou « WEO » (IMF.RES:WEO, dernière édition, clé
          COUNTRY.INDICATOR.FREQUENCY, ex. « WEO/JPN.GGXWDG_NGDP.A » ; zone euro = G163).
          Un identifiant complet « AGENCE,FLUX[,VERSION] » est aussi accepté.
  debut   « AAAA-MM-JJ » facultatif : coupure (et startPeriod pour les flux autres que WEO).
  observees_seulement  WEO seulement, défaut true : ne garde que les années ≤ dernière année
          observée de la série (attribut LATEST_ACTUAL_ANNUAL_DATA) ; les prévisions vont dans
          le jeu `fmi` (telecharger_weo).

Regroupement : clés d'un même flux qui ne diffèrent que par une dimension (ex. tous les pays
d'un indicateur WEO) ; un échec d'appel met en erreur chacune de ses séries, jamais les autres.

Jeu particulier : telecharger_weo(indicateurs, pays) → {"edition": "AAAA-MM", "publiee_le":
"AAAA-MM-JJ", "derniere_annee_observee": int, "derniere_annee_par_pays": {pays: int},
"valeurs": {indicateur: {pays: {annee: valeur}}}} ; un appel par indicateur, tous pays ensemble.
"""
from __future__ import annotations

import time
from collections import Counter

from commun import ErreurSource, nettoyer, serie_propre, telecharger as http
from sources.sdmx import (annee_debut, cle_correspond, colonnes_dimensions, lignes_csv,
                          normaliser_periode, traiter_demandes)

URL = "https://api.imf.org/external/sdmx/2.1/data/{flux}/{cle}"
ENTETES = {"Accept": "text/csv"}
ATTENTE = 20.0
PAUSE = 2.0  # secondes minimales entre deux appels au FMI
NOM = "FMI"
FLUX_COMPLETS = {"WEO": "IMF.RES,WEO", "CPI": "CPI"}

INDICATEURS_WEO = ["PCPIPCH", "NGDP_RPCH", "GGXWDG_NGDP", "GGXCNL_NGDP", "NGDP"]
PAYS_WEO = {"US": "USA", "ZE": "G163", "DE": "DEU", "FR": "FRA", "IT": "ITA", "BE": "BEL",
            "JP": "JPN", "CN": "CHN", "UK": "GBR"}

_cache: dict[str, str] = {}                       # adresse + paramètres → texte
_cache_weo: dict[tuple[str, str], tuple[frozenset, str]] = {}  # (indicateur, fréquence) → (pays, texte)
_dernier_appel = [0.0]


def vider_cache() -> None:
    _cache.clear()
    _cache_weo.clear()


def _get(flux: str, cle: str, params: dict | None = None) -> str:
    adresse = URL.format(flux=FLUX_COMPLETS.get(flux, flux), cle=cle)
    cle_cache = adresse + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    if cle_cache in _cache:
        return _cache[cle_cache]
    ecart = time.monotonic() - _dernier_appel[0]
    if ecart < PAUSE:
        time.sleep(PAUSE - ecart)
    try:
        texte = http(adresse, params=params, entetes=ENTETES, attente=ATTENTE).text
    finally:
        _dernier_appel[0] = time.monotonic()
    _cache[cle_cache] = texte
    return texte


def _texte_weo(cle: str) -> str:
    """Réponse WEO pour « PAYS+PAYS.INDICATEUR.FREQ », réutilisée si un appel plus large existe déjà."""
    parties = cle.split(".")
    if len(parties) != 3:
        raise ErreurSource("clé WEO mal formée (attendu PAYS.INDICATEUR.FRÉQUENCE)")
    pays, indicateur, frequence = frozenset(parties[0].split("+")), parties[1], parties[2]
    if "" not in pays and "+" not in indicateur:
        deja = _cache_weo.get((indicateur, frequence))
        if deja and pays <= deja[0]:
            return deja[1]
    texte = _get("WEO", cle)
    if "" not in pays and "+" not in indicateur:
        _cache_weo[(indicateur, frequence)] = (pays, texte)
    return texte


def lire_reponse(texte: str, observees_seulement: bool = False) -> tuple[dict[str, dict[str, float]], dict[str, dict]]:
    """({clé de série: série}, {clé de série: attributs utiles}) d'une réponse CSV du FMI."""
    entetes, lignes = lignes_csv(texte)
    dims = colonnes_dimensions(entetes)
    paires: dict[str, list] = {}
    attributs: dict[str, dict] = {}
    for ligne in lignes:
        cle = ".".join(ligne.get(c, "") for c in dims)
        paires.setdefault(cle, [])
        info = attributs.setdefault(cle, {})
        for a in ("LATEST_ACTUAL_ANNUAL_DATA", "PUBLICATION_DATE"):
            if (ligne.get(a) or "").strip():
                info[a] = ligne[a].strip()
        d = normaliser_periode(ligne.get("TIME_PERIOD", ""))
        valeur = (ligne.get("OBS_VALUE") or "").strip()
        if d and valeur not in ("", "NaN", "NA"):
            paires[cle].append((d, valeur))
    series = {}
    for cle, p in paires.items():
        serie = serie_propre(p)
        derniere = attributs[cle].get("LATEST_ACTUAL_ANNUAL_DATA", "")
        if observees_seulement:
            if not derniere[:4].isdigit():
                raise ErreurSource("dernière année observée absente de la réponse")
            serie = {d: v for d, v in serie.items() if int(d[:4]) <= int(derniere[:4])}
        series[cle] = serie
    return series, attributs


def _options(demande: dict) -> tuple:
    flux = str(demande.get("code", "")).split("/")[0]
    est_weo = FLUX_COMPLETS.get(flux, flux).endswith("WEO")
    return (bool(demande.get("observees_seulement", True)) if est_weo else False,)


def _appel(flux: str, cle: str, debut: str | None, options: tuple) -> dict[str, dict[str, float]]:
    (observees,) = options
    if FLUX_COMPLETS.get(flux, flux).endswith("WEO"):
        texte = _texte_weo(cle)  # WEO entier (1980-2031, petit) : jamais de startPeriod
    else:
        texte = _get(flux, cle, {"startPeriod": annee_debut(debut)} if debut else None)
    series, _ = lire_reponse(texte, observees)
    return series


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    return traiter_demandes(demandes, NOM, _appel, _options)


def analyser_weo(textes: dict[str, str], pays: dict[str, str]) -> dict:
    """Assemble le jeu `fmi` à partir des réponses WEO (une par indicateur)."""
    court = {v: k for k, v in pays.items()}
    valeurs: dict[str, dict[str, dict[int, float]]] = {}
    dernieres: list[int] = []
    par_pays: dict[str, int] = {}
    publications: list[str] = []
    for indicateur, texte in textes.items():
        series, attributs = lire_reponse(texte)
        valeurs[indicateur] = {}
        for cle, serie in series.items():
            if not cle_correspond(cle, f".{indicateur}."):
                continue
            code = cle.split(".")[0]
            if code not in court or not serie:
                continue
            valeurs[indicateur][court[code]] = {int(d[:4]): v for d, v in serie.items()}
            info = attributs[cle]
            if info.get("LATEST_ACTUAL_ANNUAL_DATA", "")[:4].isdigit():
                annee = int(info["LATEST_ACTUAL_ANNUAL_DATA"][:4])
                dernieres.append(annee)
                par_pays[court[code]] = min(annee, par_pays.get(court[code], annee))
            if info.get("PUBLICATION_DATE"):
                publications.append(info["PUBLICATION_DATE"][:10])
        manquants = [k for k in pays if k not in valeurs[indicateur]]
        if len(manquants) == len(pays):
            raise ErreurSource(f"WEO {indicateur} : aucune donnée")
    if not publications:
        raise ErreurSource("WEO : date de publication absente")
    publiee_le = Counter(publications).most_common(1)[0][0]
    if dernieres:
        compte = Counter(dernieres).most_common()
        derniere = max(a for a, n in compte if n == compte[0][1])
    else:
        derniere = int(publiee_le[:4]) - 1
    return {"edition": publiee_le[:7], "publiee_le": publiee_le, "derniere_annee_observee": derniere,
            "derniere_annee_par_pays": dict(sorted(par_pays.items())), "valeurs": valeurs}


def telecharger_weo(indicateurs: list[str] | None = None, pays: dict[str, str] | None = None) -> dict:
    """Jeu `fmi` (PLAN §6.5) : dernière édition du WEO, un appel par indicateur, tous pays ensemble."""
    indicateurs = indicateurs or INDICATEURS_WEO
    pays = pays or PAYS_WEO
    codes = "+".join(sorted(pays.values()))
    textes = {}
    for indicateur in indicateurs:
        try:
            textes[indicateur] = _texte_weo(f"{codes}.{indicateur}.A")
        except ErreurSource as erreur:
            raise ErreurSource(nettoyer(f"{NOM} WEO {indicateur} : {erreur}")) from None
    try:
        return analyser_weo(textes, pays)
    except ErreurSource as erreur:
        raise ErreurSource(nettoyer(f"{NOM} : {erreur}")) from None
    except (ValueError, KeyError) as erreur:
        raise ErreurSource(nettoyer(f"{NOM} WEO : réponse illisible ({type(erreur).__name__})")) from None
