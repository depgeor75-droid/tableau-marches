"""Fichiers publiés par des instituts (Fed de New York, Fed de Philadelphie, Caldara-Iacoviello,
Réserve fédérale, STOXX) : un téléchargement par fichier, quel que soit le nombre de séries.

Demande : {"cle": "J6_EBP", "code": "ebp", "colonne": "ebp"}.
`code` désigne le fichier ; l'option `colonne` désigne la colonne (valeur par défaut entre
parenthèses ; comparaison sans tenir compte de la casse) :

| code              | fichier                                   | colonne par défaut | dates rendues |
|-------------------|-------------------------------------------|--------------------|---------------|
| `gscpi`           | gscpi_data.xlsx (Fed de NY, en fait .xls) | `GSCPI`            | AAAA-MM-01    |
| `nyfed_recession` | allmonth.xls, feuille `rec_prob`          | `Rec_prob`         | AAAA-MM-01    |
| `gpr_mensuel`     | data_gpr_export.xls                       | `GPR`              | AAAA-MM-01    |
| `gpr_quotidien`   | data_gpr_daily_recent.xls                 | `GPRD`             | dates réelles |
| `ebp`             | ebp_csv.csv (Réserve fédérale)            | `gz_spread`        | AAAA-MM-01    |
| `vstoxx`          | h_v2tx.txt (STOXX, `;`, jj.mm.aaaa)       | `Indexvalue`       | dates réelles |

`nyfed_recession` : la colonne `Rec_prob` est rendue transformée pour D14 — série datée du
MOIS DE L'ÉCART t, valant Rec_prob(t + 12 mois) × 100 (dans le fichier, la probabilité est
inscrite sur la ligne du mois visé). Toute autre colonne (`Spread` : écart 10 ans − 3 mois en
équivalent obligataire, en points ; `10 Year Treasury Yield`…) est rendue telle quelle, datée
du mois de la ligne.

Les .xls sont lus avec xlrd, les .xlsx avec openpyxl ; le format est détecté par les premiers
octets. Une page HTML reçue à la place du fichier est une erreur.

`telecharger_spf_us()` rend le jeu `spf_us` (PLAN §6.5) depuis prob.xlsx, onglet `PRCCPI`.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime

from commun import ErreurSource, nettoyer, serie_propre, telecharger as get

try:
    from sources.formats import (decoder, lire_classeur, nombre, normaliser_nom, premier_du_mois,
                                 refuser_html)
except ImportError:
    from formats import decoder, lire_classeur, nombre, normaliser_nom, premier_du_mois, refuser_html

FICHIERS = {
    "gscpi": {"quoi": "GSCPI (Fed de New York)", "genre": "classeur", "date": "Date", "datation": "mois",
              "defaut": "GSCPI",
              "url": "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx"},
    "nyfed_recession": {"quoi": "probabilité de récession (Fed de New York)", "genre": "classeur",
                        "feuille": "rec_prob", "date": "Date", "datation": "mois", "defaut": "Rec_prob",
                        "url": "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/allmonth.xls"},
    "gpr_mensuel": {"quoi": "GPR mensuel", "genre": "classeur", "date": "month", "datation": "mois", "defaut": "GPR",
                    "url": "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"},
    "gpr_quotidien": {"quoi": "GPR quotidien", "genre": "classeur", "date": "DAY", "datation": "jour",
                      "defaut": "GPRD",
                      "url": "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"},
    "ebp": {"quoi": "EBP (Réserve fédérale)", "genre": "csv", "separateur": ",", "date": "date",
            "datation": "mois", "defaut": "gz_spread",
            "url": "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"},
    "vstoxx": {"quoi": "VSTOXX (STOXX)", "genre": "csv", "separateur": ";", "date": "Date", "datation": "jour",
               "defaut": "Indexvalue",
               "url": "https://www.stoxx.com/document/Indices/Current/HistoricalData/h_v2tx.txt"},
}

URL_SPF_US = ("https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/"
              "survey-of-professional-forecasters/historical-data/prob.xlsx")
# Grille des classes de PRCCPI (documentation SPF, tableau 8, valable depuis 2007-T1) :
# colonnes 1-10 = année de l'enquête, 11-20 = année suivante. Le fichier ne contient pas les
# libellés : seul leur nombre est vérifié (20 colonnes) ; une autre grille → erreur.
CLASSES_SPF_US = [
    {"min": 4.0, "max": None, "libelle": "4,0 % ou plus"},
    {"min": 3.5, "max": 3.9, "libelle": "3,5 à 3,9 %"},
    {"min": 3.0, "max": 3.4, "libelle": "3,0 à 3,4 %"},
    {"min": 2.5, "max": 2.9, "libelle": "2,5 à 2,9 %"},
    {"min": 2.0, "max": 2.4, "libelle": "2,0 à 2,4 %"},
    {"min": 1.5, "max": 1.9, "libelle": "1,5 à 1,9 %"},
    {"min": 1.0, "max": 1.4, "libelle": "1,0 à 1,4 %"},
    {"min": 0.5, "max": 0.9, "libelle": "0,5 à 0,9 %"},
    {"min": 0.0, "max": 0.4, "libelle": "0,0 à 0,4 %"},
    {"min": None, "max": -0.1, "libelle": "en baisse (moins de 0 %)"},
]


# ------------------------------------------------------------------ dates
def date_jour(valeur) -> str | None:
    """datetime, AAAAMMJJ (texte ou nombre), jj.mm.aaaa ou AAAA-MM-JJ → date ISO."""
    if isinstance(valeur, datetime):
        return valeur.date().isoformat()
    if isinstance(valeur, date):
        return valeur.isoformat()
    if isinstance(valeur, float) and valeur.is_integer():
        valeur = str(int(valeur))
    texte = str(valeur or "").strip()
    try:
        if re.fullmatch(r"\d{8}", texte):
            return date(int(texte[:4]), int(texte[4:6]), int(texte[6:])).isoformat()
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", texte)
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", texte):
            return date.fromisoformat(texte[:10]).isoformat()
    except ValueError:
        return None
    return None


def ajouter_mois(iso: str, n: int) -> str:
    total = int(iso[:4]) * 12 + int(iso[5:7]) - 1 + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}-01"


# ------------------------------------------------------------------ lecture générique
def series_depuis_lignes(lignes: list[list], colonne_date: str, datation: str) -> dict[str, dict[str, float]]:
    """{nom normalisé de colonne: série} ; la ligne d'en-tête est celle qui contient `colonne_date`."""
    cible = normaliser_nom(colonne_date)
    i_entete = next((i for i, l in enumerate(lignes[:30])
                     if any(normaliser_nom(c) == cible for c in l if isinstance(c, str))), None)
    if i_entete is None:
        raise ErreurSource(f"colonne de date « {colonne_date} » introuvable")
    entete = [normaliser_nom(c) for c in lignes[i_entete]]
    j_date = entete.index(cible)
    convertir = premier_du_mois if datation == "mois" else date_jour
    paires: dict[str, list] = {nom: [] for j, nom in enumerate(entete) if nom and j != j_date}
    for ligne in lignes[i_entete + 1:]:
        if len(ligne) <= j_date:
            continue
        d = convertir(ligne[j_date])
        if not d:
            continue
        for j, nom in enumerate(entete):
            if nom and j != j_date and j < len(ligne):
                paires[nom].append((d, nombre(ligne[j])))
    return {nom: serie_propre(p) for nom, p in paires.items()}


def lire_fichier(code: str, octets: bytes) -> dict[str, dict[str, float]]:
    """Octets d'un fichier du tableau FICHIERS → {colonne normalisée: série brute}."""
    spec = FICHIERS[code]
    if spec["genre"] == "csv":
        refuser_html(octets, spec["quoi"])
        lignes = list(csv.reader(io.StringIO(decoder(octets)), delimiter=spec["separateur"]))
        return series_depuis_lignes(lignes, spec["date"], spec["datation"])
    feuilles = lire_classeur(octets, spec["quoi"])
    if spec.get("feuille"):
        if spec["feuille"] not in feuilles:
            raise ErreurSource(f"{spec['quoi']} : feuille « {spec['feuille']} » absente")
        feuilles = {spec["feuille"]: feuilles[spec["feuille"]]}
    derniere = None
    for lignes in feuilles.values():
        try:
            return series_depuis_lignes(lignes, spec["date"], spec["datation"])
        except ErreurSource as erreur:
            derniere = erreur
    raise ErreurSource(f"{spec['quoi']} : {derniere}")


def probabilite_recession_d14(rec_prob: dict[str, float]) -> dict[str, float]:
    """Rec_prob inscrite sur la ligne du mois visé (fraction) → série datée du mois de l'écart
    t = mois visé − 12, en %."""
    return serie_propre((ajouter_mois(d, -12), v * 100) for d, v in rec_prob.items())


def extraire(code: str, table: dict[str, dict[str, float]], colonne: str | None) -> dict[str, float]:
    spec = FICHIERS[code]
    nom = normaliser_nom(colonne or spec["defaut"])
    if nom not in table:
        raise ErreurSource(f"{spec['quoi']} : colonne « {colonne or spec['defaut']} » absente")
    serie = table[nom]
    if code == "nyfed_recession" and nom == "rec_prob":
        serie = probabilite_recession_d14(serie)
    if not serie:
        raise ErreurSource(f"{spec['quoi']} : colonne « {colonne or spec['defaut']} » vide")
    return serie


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    par_fichier: dict[str, list[dict]] = {}
    for demande in demandes:
        if demande["code"] not in FICHIERS:
            resultats[demande["cle"]] = ErreurSource(f"fichier « {demande['code']} » inconnu")
        else:
            par_fichier.setdefault(demande["code"], []).append(demande)
    for code, groupe in par_fichier.items():
        spec = FICHIERS[code]
        try:
            table = lire_fichier(code, get(spec["url"]).content)
        except Exception as erreur:
            message = str(erreur) if isinstance(erreur, ErreurSource) else f"erreur inattendue ({type(erreur).__name__})"
            if not message.startswith(spec["quoi"]):
                message = f"{spec['quoi']} : {message}"
            e = ErreurSource(nettoyer(message))
            for demande in groupe:
                resultats[demande["cle"]] = e
            continue
        for demande in groupe:
            try:
                resultats[demande["cle"]] = extraire(code, table, demande.get("colonne"))
            except ErreurSource as erreur:
                resultats[demande["cle"]] = ErreurSource(nettoyer(erreur))
    return resultats


# ------------------------------------------------------------------ SPF de Philadelphie (D6)
def lire_spf_us(lignes: list[list], onglet: str = "PRCCPI") -> dict:
    """Lignes de l'onglet PRCCPI → jeu `spf_us` (dernière enquête renseignée)."""
    if not lignes:
        raise ErreurSource("SPF Philadelphie : onglet vide")
    entete = [str(c or "").strip().upper() for c in lignes[0]]
    if "YEAR" not in entete or "QUARTER" not in entete:
        raise ErreurSource("SPF Philadelphie : colonnes YEAR / QUARTER absentes")
    j_annee, j_trim = entete.index("YEAR"), entete.index("QUARTER")
    colonnes = sorted(((int(c[len(onglet):]), j) for j, c in enumerate(entete)
                       if c.startswith(onglet) and c[len(onglet):].isdigit()))
    n = len(CLASSES_SPF_US)
    if [k for k, _ in colonnes] != list(range(1, 2 * n + 1)):
        raise ErreurSource(f"SPF Philadelphie : {len(colonnes)} colonnes de classes au lieu de {2 * n} "
                           "(grille modifiée : à vérifier dans la documentation)")
    derniere = None
    for ligne in lignes[1:]:
        valeurs = [nombre(ligne[j]) if j < len(ligne) else None for _, j in colonnes]
        annee, trim = nombre(ligne[j_annee]), nombre(ligne[j_trim])
        if annee and trim and all(v is not None for v in valeurs):
            derniere = (int(annee), int(trim), valeurs)
    if derniere is None:
        raise ErreurSource("SPF Philadelphie : aucune enquête complète")
    annee, trim, valeurs = derniere
    horizons = []
    for k, (cle, an) in enumerate((("annee_en_cours", annee), ("annee_suivante", annee + 1))):
        probas = valeurs[k * n:(k + 1) * n]
        total = sum(probas)
        if not 99 <= total <= 101:
            raise ErreurSource(f"SPF Philadelphie : probabilités de {an} sommant à {total:.1f} %")
        sous_2 = sum(p for p, c in zip(probas, CLASSES_SPF_US) if c["max"] is not None and c["max"] < 2.0)
        horizons.append({"cle": cle, "annee": an, "probabilites": [round(p, 4) for p in probas],
                         "sous_2": round(sous_2, 2)})
    return {"enquete": f"{annee}-Q{trim}", "mesure": "IPC sous-jacent (T4 sur T4)",
            "classes": [dict(c) for c in CLASSES_SPF_US], "horizons": horizons}


def telecharger_spf_us() -> dict:
    """Jeu `spf_us` du PLAN §6.5 ; lève ErreurSource (message nettoyé) en cas d'échec."""
    try:
        feuilles = lire_classeur(get(URL_SPF_US).content, "SPF Philadelphie")
        if "PRCCPI" not in feuilles:
            raise ErreurSource("SPF Philadelphie : onglet PRCCPI absent")
        return lire_spf_us(feuilles["PRCCPI"])
    except ErreurSource as erreur:
        raise ErreurSource(nettoyer(erreur)) from None
    except Exception as erreur:
        raise ErreurSource(nettoyer(f"SPF Philadelphie : erreur inattendue ({type(erreur).__name__})")) from None
