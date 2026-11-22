"""Outils de lecture partagés par les modules « fichiers » (boe, bundesbank, mof_japon, boj,
ons, banque_mondiale, fichiers) : décodage, détection d'une page HTML renvoyée à la place
des données, lecture des classeurs .xls (xlrd) et .xlsx (openpyxl) selon leurs premiers octets,
conversion des dates.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime

from commun import ErreurSource

SIGNATURE_XLS = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # OLE2 (Excel 97-2003)
SIGNATURE_XLSX = b"PK\x03\x04"  # archive zip (Office Open XML)

MOIS_ANGLAIS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}


# ------------------------------------------------------------------ texte et HTML
def decoder(octets: bytes, encodages: tuple[str, ...] = ("utf-8-sig", "cp1252")) -> str:
    """Décode en essayant les encodages dans l'ordre (le dernier remplace les caractères fautifs)."""
    for encodage in encodages[:-1]:
        try:
            return octets.decode(encodage)
        except UnicodeDecodeError:
            continue
    return octets.decode(encodages[-1], errors="replace")


def est_html(octets: bytes) -> bool:
    """Vrai si la réponse est une page HTML (« Object moved », page d'erreur, épreuve anti-robot)."""
    debut = octets[:2048].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    return (debut.startswith(b"<") or b"<html" in debut or b"<!doctype" in debut
            or b"object moved" in debut)


def refuser_html(octets: bytes, quoi: str) -> None:
    if est_html(octets):
        raise ErreurSource(f"{quoi} : page HTML reçue au lieu des données (accès refusé ou redirection)")


# ------------------------------------------------------------------ dates
def iso_mois(annee: int, mois: int) -> str:
    return f"{int(annee):04d}-{int(mois):02d}-01"


def date_anglaise(texte: str) -> str | None:
    """« 02 Jan 1990 » ou « 31-Jan-1998 » → date ISO."""
    m = re.fullmatch(r"\s*(\d{1,2})[ -]([A-Za-z]{3})[ -](\d{4})\s*", texte)
    if not m or m.group(2).upper() not in MOIS_ANGLAIS:
        return None
    try:
        return date(int(m.group(3)), MOIS_ANGLAIS[m.group(2).upper()], int(m.group(1))).isoformat()
    except ValueError:
        return None


def premier_du_mois(valeur) -> str | None:
    """Date (datetime, date, texte ISO ou anglais) → premier jour du mois, en ISO."""
    if isinstance(valeur, (datetime, date)):
        return iso_mois(valeur.year, valeur.month)
    if isinstance(valeur, str):
        texte = valeur.strip()
        m = re.match(r"(\d{4})-(\d{2})", texte)
        if m:
            return iso_mois(int(m.group(1)), int(m.group(2)))
        d = date_anglaise(texte)
        if d:
            return d[:8] + "01"
    return None


def nombre(valeur) -> float | None:
    """Valeur de cellule → float, ou None pour « - », « . », « #N/A », vide, texte."""
    if valeur is None or isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        return float(valeur)
    texte = str(valeur).strip().replace(" ", "")
    if not texte:
        return None
    try:
        return float(texte)
    except ValueError:
        return None


# ------------------------------------------------------------------ classeurs
def format_classeur(octets: bytes) -> str:
    if octets.startswith(SIGNATURE_XLS):
        return "xls"
    if octets.startswith(SIGNATURE_XLSX):
        return "xlsx"
    return "inconnu"


def lire_classeur(octets: bytes, quoi: str = "classeur") -> dict[str, list[list]]:
    """{nom de feuille: lignes} ; les cellules date sont rendues en datetime.

    Le format est détecté par les premiers octets, pas par l'extension (le GSCPI « .xlsx »
    est en réalité un .xls)."""
    refuser_html(octets, quoi)
    genre = format_classeur(octets)
    try:
        if genre == "xls":
            import xlrd
            classeur = xlrd.open_workbook(file_contents=octets)
            feuilles = {}
            for feuille in classeur.sheets():
                lignes = []
                for r in range(feuille.nrows):
                    ligne = []
                    for cellule in feuille.row(r):
                        if cellule.ctype == xlrd.XL_CELL_DATE:
                            ligne.append(xlrd.xldate_as_datetime(cellule.value, classeur.datemode))
                        elif cellule.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                            ligne.append(None)
                        else:
                            ligne.append(cellule.value)
                    lignes.append(ligne)
                feuilles[feuille.name] = lignes
            return feuilles
        if genre == "xlsx":
            import openpyxl
            classeur = openpyxl.load_workbook(io.BytesIO(octets), read_only=True, data_only=True)
            try:
                return {nom: [list(l) for l in classeur[nom].iter_rows(values_only=True)]
                        for nom in classeur.sheetnames}
            finally:
                classeur.close()
    except ErreurSource:
        raise
    except Exception as erreur:  # fichier corrompu ou tronqué
        raise ErreurSource(f"{quoi} illisible ({type(erreur).__name__})") from None
    raise ErreurSource(f"{quoi} : format de fichier inattendu")


def normaliser_nom(nom) -> str:
    return re.sub(r"\s+", " ", str(nom or "").replace("*", "")).strip().casefold()


def trouver_entete(lignes: list[list], noms: list[str], maximum: int = 30) -> tuple[int, dict[str, int]]:
    """Cherche dans les premières lignes celle qui contient toutes les colonnes demandées.

    Retourne (indice de la ligne d'en-tête, {nom demandé: indice de colonne})."""
    voulus = {normaliser_nom(n): n for n in noms}
    for i, ligne in enumerate(lignes[:maximum]):
        index = {normaliser_nom(c): j for j, c in enumerate(ligne) if c not in (None, "")}
        if all(v in index for v in voulus):
            return i, {nom: index[cle] for cle, nom in voulus.items()}
    raise ErreurSource(f"colonne introuvable : {', '.join(noms)}")
