"""Outils communs de la collecte : chemins, requêtes HTTP robustes, nettoyage des
messages (aucune clé ni adresse d'appel complète ne doit sortir), écriture déterministe.

Portabilité Windows / Linux : pathlib partout, encoding="utf-8" explicite, fins de ligne LF.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_CONFIG = RACINE / "config"
DOSSIER_CACHE = RACINE / "cache"
FUSEAU_BELGE = ZoneInfo("Europe/Brussels")

AGENT_NAVIGATEUR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)
DELAI_REQUETE = 45  # secondes
ESSAIS = 3


class ErreurSource(Exception):
    """Erreur d'une source, avec un message en français déjà nettoyé."""


# ------------------------------------------------------------------ clés et .env
def charger_env() -> None:
    """Charge le fichier .env local (s'il existe) dans les variables d'environnement."""
    fichier = RACINE / ".env"
    if not fichier.exists():
        return
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        cle, valeur = cle.strip(), valeur.strip().strip('"').strip("'")
        if valeur and not os.environ.get(cle):
            os.environ[cle] = valeur


def secrets_connus() -> list[str]:
    return [v for v in (os.environ.get("FRED_API_KEY"), os.environ.get("EIA_API_KEY")) if v]


_MOTIFS_SENSIBLES = [
    re.compile(r"(api_key|apikey|api-key|key|token)=([^&\s'\"]+)", re.I),
    re.compile(r"https?://\S+"),  # aucune adresse d'appel complète dans les messages
]


def nettoyer(message: object) -> str:
    """Retire toute clé API et toute adresse d'appel d'un message (règle 3 du §3)."""
    texte = str(message)
    for secret in secrets_connus():
        texte = texte.replace(secret, "«clé masquée»")
    texte = _MOTIFS_SENSIBLES[0].sub(r"\1=«masqué»", texte)
    texte = _MOTIFS_SENSIBLES[1].sub(lambda m: _hote(m.group(0)), texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte[:300]


def _hote(adresse: str) -> str:
    morceaux = re.match(r"https?://([^/\s?]+)", adresse)
    return f"[{morceaux.group(1)}]" if morceaux else "[adresse masquée]"


# ------------------------------------------------------------------ HTTP
_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": AGENT_NAVIGATEUR, "Accept-Language": "en,fr;q=0.8"})
    return _session


def telecharger(url: str, *, params: dict | None = None, entetes: dict | None = None,
                essais: int = ESSAIS, delai: int = DELAI_REQUETE, attente: float = 4.0) -> requests.Response:
    """GET avec délai maximal, 3 essais espacés ; lève ErreurSource avec un message nettoyé."""
    derniere = None
    for essai in range(1, essais + 1):
        try:
            reponse = session().get(url, params=params, headers=entetes, timeout=delai)
            if reponse.status_code == 200:
                return reponse
            derniere = f"réponse HTTP {reponse.status_code}"
            if reponse.status_code in (400, 401, 403, 404):
                break  # inutile d'insister
        except requests.RequestException as erreur:
            derniere = f"{type(erreur).__name__} : {erreur}"
        if essai < essais:
            time.sleep(attente * essai)
    raise ErreurSource(nettoyer(f"échec du téléchargement ({derniere})"))


# ------------------------------------------------------------------ séries
def serie_propre(paires) -> dict[str, float]:
    """{date ISO: valeur} trié, sans valeurs non numériques (un trou reste un trou)."""
    resultat = {}
    for date, valeur in paires:
        if valeur is None:
            continue
        try:
            v = float(valeur)
        except (TypeError, ValueError):
            continue
        if math.isnan(v) or math.isinf(v):
            continue
        resultat[str(date)[:10]] = v
    return dict(sorted(resultat.items()))


def maintenant_belge() -> datetime:
    return datetime.now(timezone.utc).astimezone(FUSEAU_BELGE)


# ------------------------------------------------------------------ écriture
def arrondir(valeur: float, decimales: int) -> float:
    r = round(float(valeur), decimales)
    return 0.0 if r == 0 else r  # pas de « -0.0 »


def json_deterministe(objet) -> str:
    return json.dumps(objet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def ecrire_si_change(chemin: Path, contenu: str) -> bool:
    """Écrit en UTF-8 / LF seulement si le contenu change. Retourne True si écrit."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if chemin.exists() and chemin.read_text(encoding="utf-8") == contenu:
        return False
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    return True


def ecrire_js(chemin: Path, nom: str, objet) -> bool:
    """Fichier de données chargé par <script> : window.DONNEES["nom"] = {...};"""
    contenu = (
        "window.DONNEES = window.DONNEES || {};\n"
        f"window.DONNEES[{json.dumps(nom)}] = {json_deterministe(objet)};\n"
    )
    return ecrire_si_change(chemin, contenu)


def lire_js(chemin: Path):
    """Relit un fichier écrit par ecrire_js (pour la fusion avec les données existantes)."""
    if not chemin.exists():
        return None
    texte = chemin.read_text(encoding="utf-8")
    debut = texte.find("] = ")
    if debut < 0:
        return None
    return json.loads(texte[debut + 4:].rstrip().rstrip(";"))
