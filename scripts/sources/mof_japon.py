"""Ministère des Finances japonais — rendements des JGB (B10, colonne `10Y`).

Deux fichiers, téléchargés une seule fois quel que soit le nombre de demandes :
`historical/jgbcme_all.csv` (depuis 1974, jusqu'au mois précédent) et `jgbcme.csv` (mois en
cours ; il prime en cas de recouvrement). Encodage cp932 ; ligne 1 = titre, ligne 2 = en-têtes
(`Date,1Y,…,10Y,…`) ; dates `AAAA/M/J` non complétées de zéros ; « - » = pas de valeur ;
lignes parasites (vides, note en bas) ignorées.

Demande : {"cle": "B10", "code": "10Y"} — `code` = nom de la colonne (échéance).
Un échec de l'un des deux fichiers met en erreur toutes les séries demandées.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import decoder, refuser_html
except ImportError:
    from formats import decoder, refuser_html

BASE = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/"
FICHIERS = ["historical/jgbcme_all.csv", "jgbcme.csv"]  # ordre : le second prime
_DATE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")


def lire_csv_mof(octets: bytes) -> dict[str, dict[str, float]]:
    """{colonne: série} pour toutes les échéances d'un fichier du MoF."""
    refuser_html(octets, "MoF Japon")
    lignes = list(csv.reader(io.StringIO(decoder(octets, ("cp932", "utf-8-sig", "cp1252")))))
    i_entete = next((i for i, l in enumerate(lignes[:10]) if l and l[0].strip() == "Date"), None)
    if i_entete is None:
        raise ErreurSource("MoF Japon : en-tête « Date » introuvable")
    colonnes = [c.strip() for c in lignes[i_entete]]
    paires: dict[str, list] = {c: [] for c in colonnes[1:] if c}
    for ligne in lignes[i_entete + 1:]:
        if not ligne:
            continue
        m = _DATE.match(ligne[0].strip())
        if not m:
            continue
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            continue
        for j, nom in enumerate(colonnes[1:], start=1):
            if nom and j < len(ligne):
                valeur = ligne[j].strip()
                paires[nom].append((d, None if valeur in ("", "-") else valeur))
    return {nom: serie_propre(p) for nom, p in paires.items()}


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    if not demandes:
        return {}
    try:
        tables = [lire_csv_mof(get(BASE + nom).content) for nom in FICHIERS]
    except ErreurSource as erreur:
        e = ErreurSource(nettoyer(f"MoF Japon : {erreur}"))
        return {d["cle"]: e for d in demandes}
    except Exception as erreur:
        e = ErreurSource(nettoyer(f"MoF Japon : erreur inattendue ({type(erreur).__name__})"))
        return {d["cle"]: e for d in demandes}
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for demande in demandes:
        colonne = demande["code"]
        if colonne not in tables[0] and colonne not in tables[1]:
            resultats[demande["cle"]] = ErreurSource(f"MoF Japon : colonne « {colonne} » absente")
            continue
        fusion: dict[str, float] = {}
        for table in tables:
            fusion.update(table.get(colonne, {}))
        resultats[demande["cle"]] = dict(sorted(fusion.items())) if fusion else ErreurSource(
            f"MoF Japon : colonne « {colonne} » vide")
    return resultats
