"""Banque du Japon — API « stat-search » (secours de A5 : `FM01/STRDCLUCON`, taux au jour le jour).

Réponse CSV : une dizaine de lignes d'état (`STATUS`, `MESSAGEID`…), puis l'en-tête
`SERIES_CODE,…,SURVEY_DATES,VALUES` ; une ligne par jour calendaire (`AAAAMMJJ`), `null` sans
cotation (week-ends, et toute la période 1990-1997). Le format JSON a répondu 400 : CSV seulement.

Demande : {"cle": "A5", "code": "FM01/STRDCLUCON",
           "debut": "1990-01" (facultatif), "quotidien": False (facultatif)}.
Par défaut la série rendue est MENSUELLE : moyenne des valeurs quotidiennes des mois
COMPLETS, datée au 1er du mois (même nature que la série OCDE `IRSTCI01JPM156N`). Un mois est
complet quand le fichier contient une ligne (même `null`) pour un jour postérieur à ce mois ou
pour son dernier jour. `quotidien: True` rend la série quotidienne brute.
Pagination gérée (`NEXTPOSITION`).
"""
from __future__ import annotations

import calendar
import csv
import io
from statistics import fmean

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import decoder, refuser_html
except ImportError:
    from formats import decoder, refuser_html

ADRESSE = "https://www.stat-search.boj.or.jp/api/v1/getDataCode"


def lire_csv_boj(texte: str) -> tuple[list[tuple[str, float | None]], str | None]:
    """→ ([(date ISO, valeur ou None)], position suivante ou None)."""
    lignes = list(csv.reader(io.StringIO(texte.lstrip("﻿"))))
    etat = {l[0].strip(): l[1].strip() for l in lignes if len(l) >= 2 and l[0].strip() in ("STATUS", "MESSAGE")}
    suivante = next((l[1].strip() for l in lignes if l and l[0].strip() == "NEXTPOSITION" and len(l) > 1 and l[1].strip()), None)
    i = next((k for k, l in enumerate(lignes) if l and l[0].strip() == "SERIES_CODE"), None)
    if i is None:
        message = etat.get("MESSAGE", "réponse inattendue")
        raise ErreurSource(f"Banque du Japon : {message} (état {etat.get('STATUS', '?')})")
    entete = [c.strip() for c in lignes[i]]
    try:
        j_date, j_val = entete.index("SURVEY_DATES"), entete.index("VALUES")
    except ValueError:
        raise ErreurSource("Banque du Japon : colonnes SURVEY_DATES / VALUES absentes") from None
    observations = []
    for ligne in lignes[i + 1:]:
        if len(ligne) <= max(j_date, j_val):
            continue
        brut = ligne[j_date].strip()
        if len(brut) != 8 or not brut.isdigit():
            continue
        d = f"{brut[:4]}-{brut[4:6]}-{brut[6:]}"
        valeur = ligne[j_val].strip()
        try:
            observations.append((d, None if valeur.lower() in ("", "null", "nan") else float(valeur)))
        except ValueError:
            observations.append((d, None))
    return observations, suivante


def moyenne_mois_complets(observations: list[tuple[str, float | None]]) -> dict[str, float]:
    """Moyenne mensuelle des valeurs quotidiennes, mois complets seulement, datée au 1er du mois."""
    if not observations:
        return {}
    derniere = max(d for d, _ in observations)
    groupes: dict[str, list[float]] = {}
    for d, v in observations:
        if v is not None:
            groupes.setdefault(d[:7], []).append(v)
    sortie = []
    for mois, valeurs in groupes.items():
        annee, m = int(mois[:4]), int(mois[5:])
        dernier_jour = f"{mois}-{calendar.monthrange(annee, m)[1]:02d}"
        if derniere >= dernier_jour:
            sortie.append((mois + "-01", fmean(valeurs)))
    return serie_propre(sortie)


def telecharger_serie(code: str, debut: str = "1990-01", quotidien: bool = False) -> dict[str, float]:
    if "/" not in code:
        raise ErreurSource(f"Banque du Japon : code « {code} » invalide (attendu base/série)")
    base, serie = code.split("/", 1)
    params = {"format": "csv", "lang": "en", "db": base, "code": serie,
              "startDate": debut.replace("-", "")[:6]}
    observations: list[tuple[str, float | None]] = []
    for _ in range(20):  # pagination, garde-fou
        reponse = get(ADRESSE, params=params)
        refuser_html(reponse.content, "Banque du Japon")
        lot, suivante = lire_csv_boj(decoder(reponse.content))
        observations.extend(lot)
        if not suivante:
            break
        params["startPosition"] = suivante
    resultat = serie_propre(observations) if quotidien else moyenne_mois_complets(observations)
    if not resultat:
        raise ErreurSource(f"Banque du Japon {serie} : aucune valeur")
    return resultat


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for demande in demandes:
        try:
            resultats[demande["cle"]] = telecharger_serie(
                demande["code"], demande.get("debut", "1990-01"), bool(demande.get("quotidien", False)))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(erreur))
        except Exception as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(f"Banque du Japon : erreur inattendue ({type(erreur).__name__})"))
    return resultats
