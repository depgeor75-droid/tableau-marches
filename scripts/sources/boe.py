"""Banque d'Angleterre — base IADB (A4 `IUDBEDR` Bank Rate, B9 `IUDMNPY` Gilt 10 ans).

Appel CSV de l'IADB avec un User-Agent de navigateur (commun.session) et suivi des
redirections (302 de l'ancienne adresse vers `_iadb-FromShowColumns.asp`). Si le site renvoie
une page HTML (« Object moved », page d'erreur ou de filtrage) au lieu du CSV, la série est
mise en erreur. Format : `DATE,IUDBEDR`, dates anglaises `02 Jan 1990`.

Demande : {"cle": "A4", "code": "IUDBEDR", "debut": "1990-01-01" (facultatif)}.
Une requête par code (un code refusé ne fait pas échouer l'autre).
"""
from __future__ import annotations

import csv
import io
from datetime import date

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import date_anglaise, decoder, refuser_html
except ImportError:  # module chargé depuis scripts/sources directement
    from formats import date_anglaise, decoder, refuser_html

ADRESSES = [
    "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp",
    "https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp",  # renvoie un 302
]
MOIS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _date_iadb(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day:02d}/{MOIS[d.month - 1]}/{d.year}"


def lire_csv_iadb(octets: bytes, code: str) -> dict[str, float]:
    """CSV de l'IADB → série quotidienne (dates réelles)."""
    refuser_html(octets, f"Banque d'Angleterre {code}")
    lecteur = csv.reader(io.StringIO(decoder(octets)))
    entete = next(lecteur, None)
    if not entete or entete[0].strip().upper() != "DATE":
        raise ErreurSource(f"Banque d'Angleterre {code} : format CSV inattendu")
    colonnes = [c.strip().upper() for c in entete]
    if code.upper() not in colonnes:
        raise ErreurSource(f"Banque d'Angleterre {code} : série absente de la réponse")
    j = colonnes.index(code.upper())
    paires = []
    for ligne in lecteur:
        if len(ligne) > j:
            d = date_anglaise(ligne[0])
            if d:
                paires.append((d, ligne[j].strip() or None))
    serie = serie_propre(paires)
    if not serie:
        raise ErreurSource(f"Banque d'Angleterre {code} : aucune valeur")
    return serie


def telecharger_serie(code: str, debut: str = "1990-01-01") -> dict[str, float]:
    params = {"csv.x": "yes", "Datefrom": _date_iadb(debut), "Dateto": "now", "SeriesCodes": code,
              "CSVF": "TN", "UsingCodes": "Y", "VPD": "Y", "VFD": "N"}
    erreurs = []
    for adresse in ADRESSES:
        try:
            reponse = get(adresse, params=params, entetes={"Accept": "text/csv,*/*;q=0.8"})
            return lire_csv_iadb(reponse.content, code)
        except ErreurSource as erreur:
            erreurs.append(str(erreur))
    raise ErreurSource(nettoyer(f"Banque d'Angleterre {code} : {' ; '.join(dict.fromkeys(erreurs))}"))


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for demande in demandes:
        try:
            resultats[demande["cle"]] = telecharger_serie(demande["code"], demande.get("debut", "1990-01-01"))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = erreur
        except Exception as erreur:  # filet de sécurité : jamais d'exception non contrôlée
            resultats[demande["cle"]] = ErreurSource(nettoyer(f"Banque d'Angleterre : erreur inattendue ({type(erreur).__name__})"))
    return resultats
