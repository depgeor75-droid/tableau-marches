"""Lecture des réponses SDMX au format CSV (BCE, BRI/BIS, OCDE, FMI…).

Les périodes sont normalisées en dates ISO au premier jour de la période :
« 2026-10 » → 2026-10-01 ; « 2026-Q3 » → 2026-07-01 ; « 2026 » → 2026-01-01 ;
« 2026-11-20 » inchangé ; « 2026-W46 » → lundi de la semaine.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date

from commun import ErreurSource, serie_propre


def normaliser_periode(periode: str) -> str | None:
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
        return date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1).isoformat()
    if re.fullmatch(r"\d{4}", p):
        return p + "-01-01"
    return None


def lire_csv(texte: str, colonne_periode: str = "TIME_PERIOD", colonne_valeur: str = "OBS_VALUE",
             filtres: dict[str, str] | None = None, separateur: str = ",") -> dict[str, float]:
    """Une série à partir d'un CSV SDMX « long » (une ligne par observation)."""
    lecteur = csv.DictReader(io.StringIO(texte.lstrip("﻿")), delimiter=separateur)
    if not lecteur.fieldnames or colonne_periode not in lecteur.fieldnames:
        raise ErreurSource("format SDMX inattendu (colonne de période absente)")
    paires = []
    for ligne in lecteur:
        if filtres and any(ligne.get(k) != v for k, v in filtres.items()):
            continue
        d = normaliser_periode(ligne.get(colonne_periode, ""))
        valeur = (ligne.get(colonne_valeur) or "").strip()
        if d and valeur not in ("", "NaN", "NA"):
            paires.append((d, valeur))
    return serie_propre(paires)


def lire_csv_multiple(texte: str, colonne_cle: str, colonne_periode: str = "TIME_PERIOD",
                      colonne_valeur: str = "OBS_VALUE") -> dict[str, dict[str, float]]:
    """Plusieurs séries d'un même CSV, regroupées par la valeur de `colonne_cle`."""
    lecteur = csv.DictReader(io.StringIO(texte.lstrip("﻿")))
    groupes: dict[str, list] = {}
    for ligne in lecteur:
        d = normaliser_periode(ligne.get(colonne_periode, ""))
        valeur = (ligne.get(colonne_valeur) or "").strip()
        if d and valeur not in ("", "NaN", "NA"):
            groupes.setdefault(ligne.get(colonne_cle, ""), []).append((d, valeur))
    return {cle: serie_propre(paires) for cle, paires in groupes.items()}
