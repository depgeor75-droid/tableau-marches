"""Tests HORS RÉSEAU des modules boe, bundesbank, mof_japon, boj, ons, banque_mondiale, fichiers :
analyse d'extraits de réponses enregistrés ici en chaînes ou octets."""
import io
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commun import ErreurSource  # noqa: E402
from sources import banque_mondiale, boe, boj, bundesbank, fichiers, formats, mof_japon, ons  # noqa: E402

PAGE_OBJECT_MOVED = (b"<head><title>Object moved</title></head><body><h1>Object Moved</h1>This object may "
                     b"be found <a HREF=\"https://www.bankofengland.co.uk/boeapps/database/x.asp?a=1\">here</a>.</body>")


class FausseReponse:
    def __init__(self, contenu: bytes):
        self.content = contenu
        self.status_code = 200


# ------------------------------------------------------------------ Banque d'Angleterre
def test_iadb_dates_anglaises():
    brut = b"DATE,IUDBEDR\r\n02 Jan 1990,14.875\r\n03 Jan 1990,14.875\r\n05 Nov 2026,4\r\n06 Nov 2026,\r\n"
    serie = boe.lire_csv_iadb(brut, "IUDBEDR")
    assert serie == {"1990-01-02": 14.875, "1990-01-03": 14.875, "2026-11-05": 4.0}


def test_iadb_page_html_detectee():
    with pytest.raises(ErreurSource, match="HTML"):
        boe.lire_csv_iadb(PAGE_OBJECT_MOVED, "IUDBEDR")
    with pytest.raises(ErreurSource, match="HTML"):
        boe.lire_csv_iadb(b"\r\n<!DOCTYPE html><html><body>Bank of England</body></html>", "IUDMNPY")


def test_iadb_html_met_la_serie_en_erreur_sans_adresse(monkeypatch):
    monkeypatch.setattr(boe, "get", lambda *a, **k: FausseReponse(PAGE_OBJECT_MOVED))
    resultat = boe.telecharger([{"cle": "A4", "code": "IUDBEDR"}])["A4"]
    assert isinstance(resultat, ErreurSource)
    assert "http" not in str(resultat) and "HTML" in str(resultat)


# ------------------------------------------------------------------ Bundesbank
ENTETE_BUBA = ('﻿"";BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A;'
               'BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A_FLAGS\n'
               '"";Zinsstruktur am Rentenmarkt / 10,0 Jahre;\nEinheit;Prozent;\nDezimalstellen;2;\n'
               'Stand vom;2026-11-20 12:29:02;\n')


def test_bundesbank_virgule_decimale_et_point_virgule():
    texte = ENTETE_BUBA + "2026-11-19;3,45;\n2026-11-21;.;Kein Wert vorhanden\n2026-11-20;3,39;\n"
    assert bundesbank.lire_csv_bundesbank(texte) == {"2026-11-19": 3.45, "2026-11-20": 3.39}


def test_bundesbank_variante_anglaise_et_mensuelle():
    texte = ('﻿"",BBSIS.M.I.ZST,BBSIS.M.I.ZST_FLAGS\nDecimals,2,\nlast update,2026-11-02 12:47:46,\n'
             "1990-01,7.88,\n1997-07,5.76,\n")
    assert bundesbank.lire_csv_bundesbank(texte) == {"1990-01-01": 7.88, "1997-07-01": 5.76}


# ------------------------------------------------------------------ MoF Japon
def test_mof_cp932_tirets_et_dates_non_completees():
    texte = ("国債金利情報 (令和8年11月),,,,\r\nDate,1Y,2Y,10Y,40Y\r\n"
             "1986/7/5,4.8,4.9,5.1,-\r\n2026/11/2,1.671,1.88,2.817,3.96\r\n2026/11/4,1.676,-,2.855,-\r\n"
             ",,,,\r\n\"※最新のデータは… please clear the browser's cache\",,,,\r\n")
    tables = mof_japon.lire_csv_mof(texte.encode("cp932"))
    assert tables["10Y"] == {"1986-07-05": 5.1, "2026-11-02": 2.817, "2026-11-04": 2.855}
    assert tables["2Y"] == {"1986-07-05": 4.9, "2026-11-02": 1.88}
    assert tables["40Y"] == {"2026-11-02": 3.96}


def test_mof_deux_fichiers_une_fois(monkeypatch):
    fichiers_mof = {
        "historical/jgbcme_all.csv": b"Interest Rate,,\r\nDate,1Y,10Y\r\n2026/10/30,1.659,2.817\r\n",
        "jgbcme.csv": b"Interest Rate (November 2026),,\r\nDate,1Y,10Y\r\n2026/11/2,1.671,2.817\r\n",
    }
    appels = []

    def faux_get(url, **_):
        appels.append(url)
        return FausseReponse(fichiers_mof[url.replace(mof_japon.BASE, "")])

    monkeypatch.setattr(mof_japon, "get", faux_get)
    r = mof_japon.telecharger([{"cle": "B10", "code": "10Y"}, {"cle": "X", "code": "1Y"}])
    assert len(appels) == 2
    assert r["B10"] == {"2026-10-30": 2.817, "2026-11-02": 2.817}
    assert list(r["X"]) == ["2026-10-30", "2026-11-02"]


# ------------------------------------------------------------------ Banque du Japon
CSV_BOJ = """STATUS,200
MESSAGEID,M181000I
MESSAGE,Successfully completed
NEXTPOSITION,
SERIES_CODE,NAME_OF_TIME_SERIES,UNIT,FREQUENCY,CATEGORY,LAST_UPDATE,SURVEY_DATES,VALUES
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20260929,0.50
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20260930,0.70
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20261001,1.00
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20261003,null
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20261031,2.00
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20261102,1.227
STRDCLUCON,"Call Rate, Uncollateralized Overnight, Average (Daily)",percent per annum,DAILY,Call Rate,20261120,20261118,1.227
"""


def test_boj_moyenne_des_mois_complets():
    observations, suivante = boj.lire_csv_boj(CSV_BOJ)
    assert suivante is None
    assert ("2026-10-03", None) in observations
    serie = boj.moyenne_mois_complets(observations)
    # septembre (0,5 et 0,7) et octobre (1 et 2 ; le null est ignoré) ; novembre incomplet exclu
    assert serie == {"2026-09-01": pytest.approx(0.6), "2026-10-01": pytest.approx(1.5)}


def test_boj_mois_complet_par_son_dernier_jour():
    obs = [("2026-10-30", 1.0), ("2026-10-31", 3.0)]
    assert boj.moyenne_mois_complets(obs) == {"2026-10-01": 2.0}
    assert boj.moyenne_mois_complets(obs[:1]) == {}


def test_boj_erreur_api():
    with pytest.raises(ErreurSource, match="Banque du Japon"):
        boj.lire_csv_boj("STATUS,400\nMESSAGEID,M181005E\nMESSAGE,Invalid code\n")


# ------------------------------------------------------------------ ONS
CSV_ONS = ('"Title","CPI ANNUAL RATE 00: ALL ITEMS 2015=100"\n"CDID","D7G7"\n"Release date","18-11-2026"\n'
           '"Important notes",\n"1989","5.2"\n"1989 Q1","4.9"\n"1989 JAN","4.9"\n"1989 FEB","5.0"\n'
           '"2026 Q3","3.2"\n"2026 OCT","3.6"\n')


def test_ons_mois_trimestres_annees():
    assert ons.lire_csv_ons(CSV_ONS) == {"1989-01-01": 4.9, "1989-02-01": 5.0, "2026-10-01": 3.6}
    assert ons.lire_csv_ons(CSV_ONS, "T") == {"1989-01-01": 4.9, "2026-07-01": 3.2}
    assert ons.lire_csv_ons(CSV_ONS, "A") == {"1989-01-01": 5.2}


# ------------------------------------------------------------------ Banque mondiale
def test_banque_mondiale_periode_1960M01():
    assert banque_mondiale.periode_iso("1960M01") == "1960-01-01"
    assert banque_mondiale.periode_iso("2026M10") == "2026-10-01"
    assert banque_mondiale.periode_iso("2026M13") is None
    assert banque_mondiale.periode_iso(None) is None


def test_banque_mondiale_feuille_et_lien():
    lignes = [
        ["World Bank Commodity Price Data (The Pink Sheet)", None, None],
        ["Updated on November 03, 2026", None, None],
        [None, "Crude oil, Brent", "Crude oil, WTI", "Coal, South African **", "Gold"],
        [None, "($/bbl)", "($/bbl)", "($/mt)", "($/troy oz)"],
        ["1960M01", 1.6, "…", "…", 35],
        ["2026M10", 125, 97.7, 100, 4105],
    ]
    table = banque_mondiale.lire_prix_mensuels(lignes)
    assert table["crude oil, brent"] == {"1960-01-01": 1.6, "2026-10-01": 125.0}
    assert table["crude oil, wti"] == {"2026-10-01": 97.7}
    assert table[formats.normaliser_nom("Coal, South African")] == {"2026-10-01": 100.0}
    html = ('<a href="https://thedocs.worldbank.org/en/doc/abc-0050012026/related/'
            'CMO-Historical-Data-Monthly.xlsx">Monthly prices (XLS)</a>')
    assert banque_mondiale.extraire_lien(html).endswith("/CMO-Historical-Data-Monthly.xlsx")
    with pytest.raises(ErreurSource):
        banque_mondiale.extraire_lien("<html>rien</html>")


# ------------------------------------------------------------------ fichiers : D14
def test_d14_decalage_de_12_mois():
    lignes = [
        ["Date", "10 Year Treasury Yield", "3 Month Treasury Yield",
         "3 Month Treasury Yield (Bond Equivalent Basis)", "Spread", "Rec_prob", "NBER_Rec"],
        [datetime(2026, 9, 30), 5.0, 4.0, 4.09, 0.91, 0.20, 0.0],
        [datetime(2026, 10, 31), 5.13, 4.05, 4.1487, 0.9813, 0.265, 0.0],
        [datetime(2027, 9, 30), None, None, None, None, 0.13, None],
        [datetime(2027, 10, 31), None, None, None, None, 0.124158, None],
    ]
    table = fichiers.series_depuis_lignes(lignes, "Date", "mois")
    d14 = fichiers.extraire("nyfed_recession", table, None)
    # datée du mois de l'écart (octobre 2026), valeur = Rec_prob de la ligne 2027-10 × 100
    assert d14["2026-10-01"] == pytest.approx(12.4158)
    assert d14["2026-09-01"] == pytest.approx(13.0)
    assert d14["2025-10-01"] == pytest.approx(26.5)  # ligne 2026-10 = prévision faite il y a un an
    assert max(d14) == "2026-10-01"
    ecart = fichiers.extraire("nyfed_recession", table, "Spread")
    assert ecart == {"2026-09-01": 0.91, "2026-10-01": 0.9813}


def test_ajouter_mois():
    assert fichiers.ajouter_mois("2027-01-01", -12) == "2026-01-01"
    assert fichiers.ajouter_mois("2027-01-01", -1) == "2026-12-01"
    assert fichiers.ajouter_mois("2026-12-01", 1) == "2027-01-01"


# ------------------------------------------------------------------ fichiers : STOXX, EBP, GPR
def test_vstoxx_dates_jj_mm_aaaa():
    brut = b"Date;Symbol;Indexvalue\r\n04.01.1999;V2TX;18.2033\r\n05.01.1999;V2TX;29.6912\r\n20.11.2026;V2TX;28.3629\r\n"
    table = fichiers.lire_fichier("vstoxx", brut)
    assert fichiers.extraire("vstoxx", table, None) == {
        "1999-01-04": 18.2033, "1999-01-05": 29.6912, "2026-11-20": 28.3629}


def test_ebp_un_seul_telechargement_pour_deux_series(monkeypatch):
    brut = b"date,gz_spread,ebp,est_prob\n2026-09-01,0.9268,-0.3833,0.09\n2026-10-01,1.0045,-0.2653,0.12\n"
    appels = []

    def faux_get(url, **_):
        appels.append(url)
        if "gpr" in url:
            raise ErreurSource("échec du téléchargement (réponse HTTP 503)")
        return FausseReponse(brut)

    monkeypatch.setattr(fichiers, "get", faux_get)
    r = fichiers.telecharger([
        {"cle": "J6", "code": "ebp", "colonne": "gz_spread"},
        {"cle": "J6_EBP", "code": "ebp", "colonne": "ebp"},
        {"cle": "J3", "code": "gpr_mensuel", "colonne": "GPR"},
        {"cle": "Z", "code": "ebp", "colonne": "inexistante"},
    ])
    assert len([a for a in appels if "ebp" in a]) == 1
    assert r["J6"] == {"2026-09-01": 0.9268, "2026-10-01": 1.0045}
    assert r["J6_EBP"]["2026-10-01"] == -0.2653
    assert isinstance(r["J3"], ErreurSource) and "GPR" in str(r["J3"])
    assert isinstance(r["Z"], ErreurSource)


def test_gpr_quotidien_colonne_day():
    lignes = [["DAY", "N10D", "GPRD", "date"],
              ["19850101", 216.0, 230.04, datetime(1985, 1, 1)],
              [20261116.0, 367.0, 189.55, datetime(2026, 11, 16)]]
    table = fichiers.series_depuis_lignes(lignes, "DAY", "jour")
    assert table["gprd"] == {"1985-01-01": 230.04, "2026-11-16": 189.55}


def test_gscpi_format_detecte_par_les_octets():
    import openpyxl
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.title = "GSCPI Monthly Data"
    feuille.append(["Date", "GSCPI"])
    feuille.append([None, None])
    feuille.append(["31-Jan-1998", -1.179])
    feuille.append(["31-Oct-2026", 1.2619])
    tampon = io.BytesIO()
    classeur.save(tampon)
    octets = tampon.getvalue()
    assert formats.format_classeur(octets) == "xlsx"
    assert formats.format_classeur(formats.SIGNATURE_XLS + b"\x00" * 10) == "xls"
    table = fichiers.lire_fichier("gscpi", octets)  # fichier « .xlsx » quel que soit son vrai format
    assert fichiers.extraire("gscpi", table, None) == {"1998-01-01": -1.179, "2026-10-01": 1.2619}
    with pytest.raises(ErreurSource, match="HTML"):
        fichiers.lire_fichier("gscpi", b"<html><body>Access denied</body></html>")
    with pytest.raises(ErreurSource, match="format"):
        fichiers.lire_fichier("gscpi", b"ceci n'est pas un classeur")


# ------------------------------------------------------------------ SPF de Philadelphie
def test_spf_us_derniere_enquete_et_sous_2():
    entete = ["YEAR", "QUARTER"] + [f"PRCCPI{i}" for i in range(1, 21)]
    vide = [2007.0, 1.0] + ["#N/A"] * 20
    t3 = [2026.0, 3.0] + [10.0] * 20
    t4 = [2026.0, 4.0, 1.7463, 6.6508, 21.6405, 57.2334, 10.7306, 1.7786, 0.2198, 0.0, 0.0, 0.0,
          2.387, 7.3064, 18.4826, 31.5631, 29.8391, 8.1217, 1.9217, 0.3739, 0.0043, 0.0]
    futur = [2027.0, 1.0] + ["#N/A"] * 20
    jeu = fichiers.lire_spf_us([entete, vide, t3, t4, futur])
    assert jeu["enquete"] == "2026-Q4"
    assert len(jeu["classes"]) == 10 and jeu["classes"][0] == {"min": 4.0, "max": None, "libelle": "4,0 % ou plus"}
    en_cours, suivante = jeu["horizons"]
    assert (en_cours["cle"], en_cours["annee"], suivante["annee"]) == ("annee_en_cours", 2026, 2027)
    assert en_cours["probabilites"][3] == 57.2334
    assert en_cours["sous_2"] == 2.0  # classes 1,5-1,9 et en dessous : 1,7786 + 0,2198
    assert suivante["sous_2"] == 10.42


def test_spf_us_grille_modifiee_refusee():
    entete = ["YEAR", "QUARTER"] + [f"PRCCPI{i}" for i in range(1, 23)]
    with pytest.raises(ErreurSource, match="grille"):
        fichiers.lire_spf_us([entete, [2026.0, 4.0] + [5.0] * 22])
