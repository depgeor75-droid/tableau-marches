"""Office for National Statistics (Royaume-Uni) — séries chronologiques en CSV.

Demande : {"cle": "C11", "code": "d7g7/mm23", "frequence": "M" (facultatif),
           "chemin": "/economy/…" (facultatif)}.
- `code` = « série/jeu » (CDID/jeu en minuscules ou majuscules).
- `frequence` : "M" (lignes « 2026 OCT »), "T" (« 2026 Q3 ») ou "A" (« 2026 ») ; par défaut la
  plus fine présente dans le fichier (M, puis T, puis A). Dates au 1er jour de la période.
- `chemin` : rubrique du site qui précède `/timeseries/` ; connue pour les jeux `mm23` et `pn2`,
  obligatoire pour les autres.
Le CSV a ~8 lignes d'en-tête (Title, CDID, Release date…), puis `"période","valeur"`.
L'ONS limite le débit (429) : 3 essais espacés de 30 s puis 60 s, pause entre deux séries.
Exemples : C11 `d7g7/mm23` (M), E1_UK `abmi/pn2` (T, niveau), PIBN_UK `ybha/pn2` (T, M£).
"""
from __future__ import annotations

import csv
import io
import re
import time

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import MOIS_ANGLAIS, decoder, refuser_html
except ImportError:
    from formats import MOIS_ANGLAIS, decoder, refuser_html

ADRESSE = "https://www.ons.gov.uk/generator"
CHEMINS = {
    "mm23": "/economy/inflationandpriceindices",
    "pn2": "/economy/grossdomesticproductgdp",
    "ukea": "/economy/grossdomesticproductgdp",
    "qna": "/economy/grossdomesticproductgdp",
}
ATTENTE_ESSAIS = 30  # secondes (×1 puis ×2) — PLAN §2 C10
PAUSE_ENTRE_SERIES = 3


def lire_csv_ons(texte: str, frequence: str | None = None) -> dict[str, float]:
    groupes: dict[str, list] = {"M": [], "T": [], "A": []}
    for ligne in csv.reader(io.StringIO(texte.lstrip("﻿"))):
        if len(ligne) < 2:
            continue
        periode, valeur = ligne[0].strip().upper(), ligne[1].strip()
        m = re.fullmatch(r"(\d{4}) ([A-Z]{3})", periode)
        if m and m.group(2) in MOIS_ANGLAIS:
            groupes["M"].append((f"{m.group(1)}-{MOIS_ANGLAIS[m.group(2)]:02d}-01", valeur))
            continue
        m = re.fullmatch(r"(\d{4}) Q([1-4])", periode)
        if m:
            groupes["T"].append((f"{m.group(1)}-{(int(m.group(2)) - 1) * 3 + 1:02d}-01", valeur))
            continue
        if re.fullmatch(r"\d{4}", periode):
            groupes["A"].append((f"{periode}-01-01", valeur))
    if frequence:
        choix = frequence.upper()
        if choix not in groupes:
            raise ErreurSource(f"ONS : fréquence « {frequence} » inconnue (M, T ou A)")
    else:
        choix = next((f for f in ("M", "T", "A") if groupes[f]), "M")
    return serie_propre(groupes[choix])


def telecharger_serie(code: str, frequence: str | None = None, chemin: str | None = None) -> dict[str, float]:
    morceaux = code.strip().lower().split("/")
    if len(morceaux) != 2:
        raise ErreurSource(f"ONS : code « {code} » invalide (attendu série/jeu)")
    serie, jeu = morceaux
    chemin = chemin or CHEMINS.get(jeu)
    if not chemin:
        raise ErreurSource(f"ONS : rubrique inconnue pour le jeu « {jeu} » (option chemin)")
    uri = f"{chemin.rstrip('/')}/timeseries/{serie}/{jeu}"
    reponse = get(ADRESSE, params={"format": "csv", "uri": uri}, attente=ATTENTE_ESSAIS)
    refuser_html(reponse.content, f"ONS {serie.upper()}")
    resultat = lire_csv_ons(decoder(reponse.content), frequence)
    if not resultat:
        raise ErreurSource(f"ONS {serie.upper()} : aucune valeur à la fréquence demandée")
    return resultat


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    for n, demande in enumerate(demandes):
        if n:
            time.sleep(PAUSE_ENTRE_SERIES)
        try:
            resultats[demande["cle"]] = telecharger_serie(
                demande["code"], demande.get("frequence"), demande.get("chemin"))
        except ErreurSource as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(erreur))
        except Exception as erreur:
            resultats[demande["cle"]] = ErreurSource(nettoyer(f"ONS : erreur inattendue ({type(erreur).__name__})"))
    return resultats
