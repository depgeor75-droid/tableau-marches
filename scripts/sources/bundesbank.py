"""Deutsche Bundesbank — API SDMX « REST » au format CSV maison (B4 Bund 10 ans).

Demande : {"cle": "B4", "code": "BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A",
           "debut": "1990-01-01" (facultatif), "fin": "1997-07-31" (facultatif, borne incluse)}.
- `code` = « jeu/clé ». Clé en `D.` : série quotidienne (dates réelles, depuis 1997-08-07) ;
  clé en `M.` : valeurs de fin de mois datées au 1er du mois (seules disponibles avant
  août 1997 : demander `fin: "1997-07-01"` pour la partie « avant »).
- `format=csv` (`csvdata` renvoie 406). La réponse a une dizaine de lignes de métadonnées,
  puis `période;valeur;drapeau`. Selon la langue négociée, séparateur `;` et virgule décimale
  (allemand) ou `,` et point (anglais) : les deux sont lus. « . » = pas de valeur (week-end).
"""
from __future__ import annotations

import csv
import io
import re

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import decoder, refuser_html
except ImportError:
    from formats import decoder, refuser_html

ADRESSE = "https://api.statistiken.bundesbank.de/rest/data/{jeu}/{cle}"
_PERIODE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def lire_csv_bundesbank(texte: str) -> dict[str, float]:
    """CSV Bundesbank (séparateur ; ou ,) → série ; périodes mensuelles → AAAA-MM-01."""
    lignes = [l for l in texte.lstrip("﻿").splitlines() if l.strip()]
    donnees = [l for l in lignes if _PERIODE.match(l.split(";")[0].split(",")[0].strip().strip('"'))]
    if not donnees:
        raise ErreurSource("Bundesbank : aucune observation dans la réponse")
    separateur = ";" if ";" in donnees[0] else ","
    paires = []
    for ligne in csv.reader(io.StringIO("\n".join(donnees)), delimiter=separateur):
        if len(ligne) < 2:
            continue
        periode, valeur = ligne[0].strip(), ligne[1].strip()
        if valeur in ("", ".", "-"):
            continue
        if separateur == ";":
            valeur = valeur.replace(".", "").replace(",", ".")  # « 1.234,5 » → 1234.5
        if len(periode) == 7:
            periode += "-01"
        paires.append((periode, valeur))
    return serie_propre(paires)


def telecharger_serie(code: str, debut: str | None = None, fin: str | None = None) -> dict[str, float]:
    if "/" not in code:
        raise ErreurSource(f"Bundesbank : code « {code} » invalide (attendu jeu/clé)")
    jeu, cle = code.split("/", 1)
    mensuelle = cle.startswith("M.")
    debut = debut or "1990-01-01"
    params = {"format": "csv", "startPeriod": debut[:7] if mensuelle else debut[:10]}
    if fin:
        params["endPeriod"] = fin[:7] if mensuelle else fin[:10]
    reponse = get(ADRESSE.format(jeu=jeu, cle=cle), params=params)
    refuser_html(reponse.content, "Bundesbank")
    serie = lire_csv_bundesbank(decoder(reponse.content))
    if fin:
        serie = {d: v for d, v in serie.items() if d <= fin[:10]}
    if not serie:
        raise ErreurSource("Bundesbank : série vide")
    return serie


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for demande in demandes:
        try:
            resultats[demande["cle"]] = telecharger_serie(demande["code"], demande.get("debut"), demande.get("fin"))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(erreur))
        except Exception as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(f"Bundesbank : erreur inattendue ({type(erreur).__name__})"))
    return resultats
