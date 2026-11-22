"""Tests HORS RÉSEAU des modules SDMX (bce, eurostat, bis, ocde, fmi) et de sdmx.py.

Les réponses d'exemple sont des extraits réduits de vraies réponses, enregistrés ici en chaînes ;
les appels HTTP sont remplacés par une fausse fonction qui note les adresses demandées.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import commun  # noqa: E402
from sources import bce, bis, eurostat, fmi, ocde, sdmx  # noqa: E402


class FausseReponse:
    def __init__(self, texte):
        self.text = texte
        self.status_code = 200

    def json(self):
        return json.loads(self.text)


class FauxHttp:
    """Remplace commun.telecharger : réponses choisies par une fonction de l'adresse et des paramètres."""

    def __init__(self, repondre):
        self.repondre = repondre
        self.appels = []

    def __call__(self, url, params=None, entetes=None, attente=4.0, **_):
        self.appels.append((url, params, entetes, attente))
        texte = self.repondre(url, params)
        if isinstance(texte, Exception):
            raise texte
        return FausseReponse(texte)


# ------------------------------------------------------------------ périodes
@pytest.mark.parametrize("periode, attendu", [
    ("2026-10", "2026-10-01"), ("2026-Q3", "2026-07-01"), ("2026Q4", "2026-10-01"),
    ("2026", "2026-01-01"), ("2026-11-20", "2026-11-20"), ("2026-M09", "2026-09-01"),
    ("2026-W46", "2026-11-09"), ("n'importe quoi", None),
])
def test_normaliser_periode(periode, attendu):
    assert sdmx.normaliser_periode(periode) == attendu


def test_semaine_iso_datee_du_vendredi():
    assert sdmx.normaliser_periode("2026-W46", jour_semaine=5) == "2026-11-13"
    assert sdmx.normaliser_periode("2020-W53", jour_semaine=5) == "2021-01-01"
    csv = "TIME_PERIOD,OBS_VALUE\n2026-W45,5900000\n2026-W46,5906258\n"
    assert sdmx.lire_csv(csv, jour_semaine=5) == {"2026-11-06": 5900000.0, "2026-11-13": 5906258.0}
    assert sdmx.lire_csv(csv) == {"2026-11-02": 5900000.0, "2026-11-09": 5906258.0}  # compatibilité


# ------------------------------------------------------------------ lecture et regroupement
CSV_BCE_EXR = """KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,OBS_STATUS,TITLE
EXR.D.JPY.EUR.SP00.A,D,JPY,EUR,SP00,A,2026-11-19,173.9,A,"Japanese yen/Euro, 2:15 pm"
EXR.D.JPY.EUR.SP00.A,D,JPY,EUR,SP00,A,2026-11-20,174.32,A,"Japanese yen/Euro, 2:15 pm"
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-11-19,1.0975,A,US dollar/Euro
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-11-20,1.0991,A,US dollar/Euro
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-11-21,,H,US dollar/Euro
"""

CSV_BIS = """STRUCTURE,STRUCTURE_ID,ACTION,FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,TITLE
dataflow,BIS:WS_CBPOL(1.0),I,M,CH,2026-09,0,368,Switzerland
dataflow,BIS:WS_CBPOL(1.0),I,M,CH,2026-10,0,368,Switzerland
dataflow,BIS:WS_CBPOL(1.0),I,M,CN,2026-09,3,368,China
dataflow,BIS:WS_CBPOL(1.0),I,M,CN,2026-10,3,368,China
dataflow,BIS:WS_CBPOL(1.0),I,M,US,2026-10,3.875,368,United States
"""


def test_lire_csv_series_par_cle():
    series = sdmx.lire_csv_series(CSV_BCE_EXR)
    assert set(series) == {"D.JPY.EUR.SP00.A", "D.USD.EUR.SP00.A"}
    assert series["D.USD.EUR.SP00.A"] == {"2026-11-19": 1.0975, "2026-11-20": 1.0991}  # valeur vide = trou
    series = sdmx.lire_csv_series(CSV_BIS)
    assert series["M.CN"] == {"2026-09-01": 3.0, "2026-10-01": 3.0}


def test_cle_correspond_et_choix():
    assert sdmx.cle_correspond("M.CN", "M.CN+CH")
    assert sdmx.cle_correspond("USA.M.LI.IX._Z.AA.IX._Z.H", "USA.M.LI...AA...H")
    assert not sdmx.cle_correspond("M.US", "M.CN+CH")
    series = sdmx.lire_csv_series(CSV_BIS)
    with pytest.raises(commun.ErreurSource, match="ambiguë"):
        sdmx.choisir_serie(series, "M.", "BIS")
    with pytest.raises(commun.ErreurSource, match="absente"):
        sdmx.choisir_serie(series, "M.JP", "BIS")


def test_reponse_html_refusee():
    with pytest.raises(commun.ErreurSource, match="HTML"):
        sdmx.lire_csv_series("<html><body>Your access has been blocked</body></html>")


def test_regrouper_cles():
    exr = [f"D.{d}.EUR.SP00.A" for d in ("USD", "JPY", "CNY", "GBP", "CHF")]
    assert sdmx.regrouper_cles(exr) == [("D.CHF+CNY+GBP+JPY+USD.EUR.SP00.A", [0, 1, 2, 3, 4])]
    hicp = ["M.U2.N.000000.4D0.ANR", "M.U2.N.XEF000.4D0.ANR", "M.BE.N.000000.4D0.ANR",
            "M.DE.N.000000.4D0.ANR", "M.FR.N.000000.4D0.ANR", "M.IT.N.000000.4D0.ANR"]
    groupes = sdmx.regrouper_cles(hicp)
    assert groupes[0] == ("M.BE+DE+FR+IT+U2.N.000000.4D0.ANR", [0, 2, 3, 4, 5])
    assert groupes[1] == ("M.U2.N.XEF000.4D0.ANR", [1])
    # deux dimensions différentes : pas de produit croisé
    assert len(sdmx.regrouper_cles(["D.U2.SS_CIN.IDX", "D.U2.SS_BMN.CON"])) == 2


# ------------------------------------------------------------------ BCE
def test_escalier_jours_ouvrables_jusqua_aujourdhui():
    changements = {"2026-06-17": 2.25, "2026-09-16": 2.5, "2026-12-16": 2.75}  # le dernier est futur
    serie = bce.escalier(changements, date(2026, 11, 22))  # un dimanche
    dates = list(serie)
    assert dates[0] == "2026-06-17" and dates[-1] == "2026-11-20"  # vendredi, jamais au-delà
    assert all(date.fromisoformat(d).weekday() < 5 for d in dates)
    assert serie["2026-09-15"] == 2.25 and serie["2026-09-16"] == 2.5
    assert 2.75 not in serie.values()
    assert serie == bce.escalier(changements, date(2026, 11, 20))
    assert bce.escalier({"2027-01-01": 3.0}, date(2026, 11, 22)) == {}


def test_bce_escalier_par_telecharger(monkeypatch):
    csv = ("KEY,FREQ,REF_AREA,CURRENCY,PROVIDER_FM,INSTRUMENT_FM,PROVIDER_FM_ID,DATA_TYPE_FM,TIME_PERIOD,OBS_VALUE\n"
           "FM.B.U2.EUR.4F.KR.DFR.LEV,B,U2,EUR,4F,KR,DFR,LEV,1999-01-01,2\n"
           "FM.B.U2.EUR.4F.KR.DFR.LEV,B,U2,EUR,4F,KR,DFR,LEV,1999-01-04,2.75\n")
    faux = FauxHttp(lambda url, params: csv)
    monkeypatch.setattr(bce, "http", faux)
    r = bce.telecharger([{"cle": "A2", "code": "FM/B.U2.EUR.4F.KR.DFR.LEV", "escalier": True,
                          "debut": "1990-01-01"}], aujourdhui=date(1999, 1, 8))
    assert r["A2"] == {"1999-01-01": 2.0, "1999-01-04": 2.75, "1999-01-05": 2.75,
                       "1999-01-06": 2.75, "1999-01-07": 2.75, "1999-01-08": 2.75}
    assert "startPeriod" not in faux.appels[0][1]  # historique complet pour l'escalier


def test_bce_regroupement_et_echec_isole(monkeypatch):
    def repondre(url, params):
        if "/EXR/" in url:
            return CSV_BCE_EXR
        return commun.ErreurSource("échec du téléchargement (réponse HTTP 503)")
    faux = FauxHttp(repondre)
    monkeypatch.setattr(bce, "http", faux)
    r = bce.telecharger([
        {"cle": "I1", "code": "EXR/D.USD.EUR.SP00.A", "debut": "1990-01-01"},
        {"cle": "IC_EURJPY", "code": "EXR/D.JPY.EUR.SP00.A", "debut": "1990-01-01"},
        {"cle": "B5_2A", "code": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"},
        {"cle": "B5_10A", "code": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"},
        {"cle": "MAL", "code": "pas de barre oblique"},
    ])
    assert len(faux.appels) == 2  # un appel EXR groupé, un appel YC groupé
    url_exr = [u for u, *_ in faux.appels if "/EXR/" in u][0]
    assert url_exr.endswith("/EXR/D.JPY+USD.EUR.SP00.A")
    assert [p for u, p, *_ in faux.appels if "/EXR/" in u][0]["startPeriod"] == "1990"
    assert r["I1"]["2026-11-20"] == 1.0991 and r["IC_EURJPY"]["2026-11-20"] == 174.32
    for cle in ("B5_2A", "B5_10A", "MAL"):
        assert isinstance(r[cle], commun.ErreurSource)
    assert "503" in str(r["B5_2A"]) and str(r["B5_2A"]) == str(r["B5_10A"])
    assert "://" not in str(r["B5_2A"])


def test_bce_ilm_date_du_vendredi(monkeypatch):
    csv = ("KEY,FREQ,REF_AREA,BS_REP_SECTOR,BS_ITEM,COUNT_AREA,CURRENCY_TRANS,TIME_PERIOD,OBS_VALUE\n"
           "ILM.W.U2.C.T000000.Z5.Z01,W,U2,C,T000000,Z5,Z01,2026-W46,5906258\n")
    monkeypatch.setattr(bce, "http", FauxHttp(lambda url, params: csv))
    r = bce.telecharger([{"cle": "F2", "code": "ILM/W.U2.C.T000000.Z5.Z01"}])
    assert r["F2"] == {"2026-11-13": 5906258.0}


CSV_SPF = """KEY,FREQ,REF_AREA,FCT_TOPIC,FCT_BREAKDOWN,FCT_HORIZON,SURVEY_FREQ,FCT_SOURCE,TIME_PERIOD,OBS_VALUE
SPF.Q.U2.HICP.T1_7.2027.Q.AVG,Q,U2,HICP,T1_7,2027,Q,AVG,2026-Q3,30
SPF.Q.U2.HICP.T1_7.2027.Q.AVG,Q,U2,HICP,T1_7,2027,Q,AVG,2026-Q4,26.8
SPF.Q.U2.HICP.F1_8T2_2.2027.Q.AVG,Q,U2,HICP,F1_8T2_2,2027,Q,AVG,2026-Q4,15.5
SPF.Q.U2.HICP.F2_3.2027.Q.AVG,Q,U2,HICP,F2_3,2027,Q,AVG,2026-Q4,57.7
SPF.Q.U2.HICP.POINT.2027.Q.AVG,Q,U2,HICP,POINT,2027,Q,AVG,2026-Q4,2.6
SPF.Q.U2.HICP.POINT.2027.Q.NUM,Q,U2,HICP,POINT,2027,Q,NUM,2026-Q4,51
SPF.Q.U2.HICP.F2_3.2027.Q.NUM,Q,U2,HICP,F2_3,2027,Q,NUM,2026-Q4,38
SPF.Q.U2.HICP.F2_0T2_4.2027.Q.PFC,Q,U2,HICP,F2_0T2_4,2027,Q,PFC,2026-Q4,20
SPF.Q.U2.HICP.T1_7.LT.Q.AVG,Q,U2,HICP,T1_7,LT,Q,AVG,2026-Q4,30.8
SPF.Q.U2.HICP.F1_8T2_2.LT.Q.AVG,Q,U2,HICP,F1_8T2_2,LT,Q,AVG,2026-Q4,33.8
SPF.Q.U2.HICP.F2_3.LT.Q.AVG,Q,U2,HICP,F2_3,LT,Q,AVG,2026-Q4,35.4
SPF.Q.U2.HICP.T1_7.2031.Q.AVG,Q,U2,HICP,T1_7,2031,Q,AVG,2026-Q4,30.8
"""


def test_lire_classe():
    assert bce.lire_classe("TN0_8") == {"code": "TN0_8", "min": None, "max": -0.8}
    assert bce.lire_classe("FN0_7TN0_3") == {"code": "FN0_7TN0_3", "min": -0.7, "max": -0.3}
    assert bce.lire_classe("F4_8") == {"code": "F4_8", "min": 4.8, "max": None}
    assert bce.lire_classe("POINT") is None


def test_analyser_spf():
    spf = bce.analyser_spf(CSV_SPF)
    assert spf["enquete"] == "2026-Q4"
    assert [c["code"] for c in spf["classes"]] == ["T1_7", "F1_8T2_2", "F2_3"]  # PFC et POINT exclus
    h2027, hlt = spf["horizons"]
    assert h2027["cle"] == "2027" and h2027["annee"] == 2027
    assert h2027["probabilites"] == [26.8, 15.5, 57.7] and h2027["moyenne"] == 2.6
    assert h2027["reponses"] == 51 and h2027["reponses_probabilites"] == 38
    assert (h2027["sous_1_8"], h2027["proche_de_2"], h2027["au_dessus_de_2_2"]) == (26.8, 15.5, 57.7)
    assert hlt["cle"] == "LT" and hlt["annee"] == 2031 and hlt["moyenne"] is None
    assert len(spf["horizons"]) == 2  # 2031 n'est pas repris en double du long terme


def test_spf_somme_controlee():
    faux = CSV_SPF.replace("2026-Q4,57.7", "2026-Q4,40")
    with pytest.raises(commun.ErreurSource, match="somme"):
        bce.analyser_spf(faux)


# ------------------------------------------------------------------ Eurostat
JSONSTAT = {
    "version": "2.0", "class": "dataset", "id": ["freq", "int_rt", "geo", "time"], "size": [1, 1, 2, 3],
    "dimension": {
        "freq": {"category": {"index": {"M": 0}}},
        "int_rt": {"category": {"index": {"MCBY": 0}}},
        "geo": {"category": {"index": {"BE": 0, "FR": 1}}},
        "time": {"category": {"index": {"2026-08": 0, "2026-09": 1, "2026-10": 2}}},
    },
    "value": {"0": 3.76, "1": 4.12, "2": 4.38, "3": 4.0, "5": 4.89},
}


def test_eurostat_extraire_serie():
    assert eurostat.extraire_serie(JSONSTAT, {"geo": "FR"}) == {"2026-08-01": 4.0, "2026-10-01": 4.89}
    assert eurostat.extraire_serie(JSONSTAT, {"geo": "BE"})["2026-10-01"] == 4.38
    with pytest.raises(commun.ErreurSource, match="filtre manquant"):
        eurostat.extraire_serie(JSONSTAT, {})
    with pytest.raises(commun.ErreurSource, match="geo=IT"):
        eurostat.extraire_serie(JSONSTAT, {"geo": "IT"})
    trimestriel = dict(JSONSTAT, id=["geo", "time"], size=[1, 2], value=[88.4, 88.8],
                       dimension={"geo": {"category": {"index": {"EA21": 0}}},
                                  "time": {"category": {"index": {"2026-Q1": 0, "2026-Q2": 1}}}})
    assert eurostat.extraire_serie(trimestriel, {"geo": "EA21"}) == {"2026-01-01": 88.4, "2026-04-01": 88.8}


def test_eurostat_regroupement(monkeypatch):
    faux = FauxHttp(lambda url, params: json.dumps(JSONSTAT) if "irt_lt" in url
                    else commun.ErreurSource("échec du téléchargement (réponse HTTP 500)"))
    monkeypatch.setattr(eurostat, "http", faux)
    r = eurostat.telecharger([
        {"cle": "B6", "code": "irt_lt_mcby_m", "filtres": {"geo": "BE"}},
        {"cle": "B7", "code": "irt_lt_mcby_m", "filtres": {"geo": "FR"}, "debut": "2026-09-01"},
        {"cle": "E1_ZE", "code": "namq_10_gdp", "filtres": {"geo": "EA21", "unit": "CLV_PCH_SM"}},
    ])
    assert len(faux.appels) == 2
    params = [p for u, p, *_ in faux.appels if "irt_lt" in u][0]
    assert ("geo", "BE") in params and ("geo", "FR") in params
    assert r["B6"]["2026-10-01"] == 4.38 and r["B7"] == {"2026-10-01": 4.89}
    assert isinstance(r["E1_ZE"], commun.ErreurSource) and "500" in str(r["E1_ZE"])


# ------------------------------------------------------------------ BIS, OCDE
def test_bis_filtre_non_strict_et_attente(monkeypatch):
    faux = FauxHttp(lambda url, params: CSV_BIS)
    monkeypatch.setattr(bis, "http", faux)
    r = bis.telecharger([{"cle": "A6", "code": "WS_CBPOL/M.CN"}, {"cle": "A7", "code": "WS_CBPOL/M.CH"}])
    assert len(faux.appels) == 1 and faux.appels[0][0].endswith("/WS_CBPOL/1.0/M.CH+CN")
    assert r["A6"] == {"2026-09-01": 3.0, "2026-10-01": 3.0} and r["A7"]["2026-10-01"] == 0.0


def test_ocde_regroupement_attente(monkeypatch):
    csv = ("DATAFLOW,REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,ADJUSTMENT,TRANSFORMATION,TIME_HORIZ,METHODOLOGY,"
           "TIME_PERIOD,OBS_VALUE\n"
           "OECD.SDD.STES:DSD_STES@DF_CLI(4.1),USA,M,LI,IX,_Z,AA,IX,_Z,H,2026-10,100.96\n"
           "OECD.SDD.STES:DSD_STES@DF_CLI(4.1),CHN,M,LI,IX,_Z,AA,IX,_Z,H,2026-10,97.13\n")
    faux = FauxHttp(lambda url, params: csv)
    monkeypatch.setattr(ocde, "http", faux)
    code = "OECD.SDD.STES,DSD_STES@DF_CLI/{}.M.LI...AA...H"
    r = ocde.telecharger([{"cle": "D13_US", "code": code.format("USA")},
                          {"cle": "D13_CN", "code": code.format("CHN")},
                          {"cle": "D13_JP", "code": code.format("JPN")}])
    assert len(faux.appels) == 1 and faux.appels[0][3] == 10.0
    assert faux.appels[0][0].endswith("/CHN+JPN+USA.M.LI...AA...H")
    assert r["D13_US"] == {"2026-10-01": 100.96}
    assert isinstance(r["D13_JP"], commun.ErreurSource) and "absente" in str(r["D13_JP"])


# ------------------------------------------------------------------ FMI
CSV_WEO = """DATAFLOW,COUNTRY,INDICATOR,FREQUENCY,TIME_PERIOD,OBS_VALUE,SCALE,LATEST_ACTUAL_ANNUAL_DATA,PUBLICATION_DATE
IMF.RES:WEO(9.0.0),JPN,GGXWDG_NGDP,A,2025,204.78,0,2024,2026-10-13T02:00:00Z
IMF.RES:WEO(9.0.0),JPN,GGXWDG_NGDP,A,2024,213.59,0,2024,2026-10-13T02:00:00Z
IMF.RES:WEO(9.0.0),USA,GGXWDG_NGDP,A,2026,126.79,0,2025,2026-10-13T02:00:00Z
IMF.RES:WEO(9.0.0),USA,GGXWDG_NGDP,A,2025,124.38,0,2025,2026-10-13T02:00:00Z
IMF.RES:WEO(9.0.0),USA,GGXWDG_NGDP,A,2024,122.33,0,2025,2026-10-13T02:00:00Z
IMF.RES:WEO(9.0.0),G163,GGXWDG_NGDP,A,2025,87.34,0,2025,2026-10-13T02:00:00Z
"""


@pytest.fixture
def fmi_propre(monkeypatch):
    fmi.vider_cache()
    monkeypatch.setattr(fmi, "PAUSE", 0)
    yield
    fmi.vider_cache()


def test_fmi_annees_observees_et_cache(monkeypatch, fmi_propre):
    faux = FauxHttp(lambda url, params: CSV_WEO)
    monkeypatch.setattr(fmi, "http", faux)
    r = fmi.telecharger([{"cle": f"E3_{p}", "code": f"WEO/{c}.GGXWDG_NGDP.A"}
                         for p, c in (("US", "USA"), ("JP", "JPN"), ("ZE", "G163"))])
    assert len(faux.appels) == 1 and faux.appels[0][3] == 20.0
    assert "/IMF.RES,WEO/G163+JPN+USA.GGXWDG_NGDP.A" in faux.appels[0][0]
    assert r["E3_US"] == {"2024-01-01": 122.33, "2025-01-01": 124.38}  # 2026 = prévision, exclue
    assert r["E3_JP"] == {"2024-01-01": 213.59}
    # Sous-ensemble des pays déjà demandés : aucune nouvelle requête
    r = fmi.telecharger([{"cle": "E3_US", "code": "WEO/USA.GGXWDG_NGDP.A", "observees_seulement": False}])
    assert len(faux.appels) == 1 and r["E3_US"]["2026-01-01"] == 126.79


def test_fmi_telecharger_weo(monkeypatch, fmi_propre):
    faux = FauxHttp(lambda url, params: CSV_WEO)
    monkeypatch.setattr(fmi, "http", faux)
    weo = fmi.telecharger_weo(["GGXWDG_NGDP"], {"US": "USA", "JP": "JPN", "ZE": "G163"})
    assert weo["edition"] == "2026-10" and weo["publiee_le"] == "2026-10-13"
    assert weo["derniere_annee_observee"] == 2025
    assert weo["derniere_annee_par_pays"] == {"JP": 2024, "US": 2025, "ZE": 2025}
    assert weo["valeurs"]["GGXWDG_NGDP"]["US"] == {2024: 122.33, 2025: 124.38, 2026: 126.79}
    assert len(faux.appels) == 1


def test_fmi_cpi_mensuel_et_echec(monkeypatch, fmi_propre):
    csv = ("DATAFLOW,COUNTRY,INDEX_TYPE,COICOP_1999,TYPE_OF_TRANSFORMATION,FREQUENCY,TIME_PERIOD,OBS_VALUE\n"
           "IMF.STA:CPI(5.0.0),JPN,CPI,_T,YOY_PCH_PA_PT,M,2026-M08,1.96\n"
           "IMF.STA:CPI(5.0.0),JPN,CPI,_T,YOY_PCH_PA_PT,M,2026-M09,2.23\n")
    monkeypatch.setattr(fmi, "http", FauxHttp(lambda url, params: csv))
    r = fmi.telecharger([{"cle": "C12", "code": "CPI/JPN.CPI._T.YOY_PCH_PA_PT.M"}])
    assert r["C12"] == {"2026-08-01": 1.96, "2026-09-01": 2.23}
    fmi.vider_cache()
    monkeypatch.setattr(fmi, "http", FauxHttp(
        lambda url, params: commun.ErreurSource("échec du téléchargement (réponse HTTP 429)")))
    r = fmi.telecharger([{"cle": "C12", "code": "CPI/JPN.CPI._T.YOY_PCH_PA_PT.M"},
                         {"cle": "C13_secours", "code": "CPI/CHN.CPI._T.YOY_PCH_PA_PT.M"}])
    assert all(isinstance(v, commun.ErreurSource) and "429" in str(v) for v in r.values())
    with pytest.raises(commun.ErreurSource, match="PCPIPCH"):
        fmi.telecharger_weo(["PCPIPCH"], {"US": "USA"})


def test_commun_telecharger_attente(monkeypatch):
    """L'argument `attente` règle l'espacement des essais (C10) ; 404 n'est pas réessayé."""
    pauses = []

    class Session:
        def __init__(self, codes):
            self.codes = list(codes)

        def get(self, *a, **k):
            r = FausseReponse("ok")
            r.status_code = self.codes.pop(0)
            return r

    monkeypatch.setattr(commun.time, "sleep", pauses.append)
    s = Session([429, 429, 200])
    monkeypatch.setattr(commun, "session", lambda: s)
    assert commun.telecharger("https://exemple.org/x", attente=20).text == "ok"
    assert pauses == [20, 40]
    s = Session([404])
    monkeypatch.setattr(commun, "session", lambda: s)
    with pytest.raises(commun.ErreurSource, match="404") as erreur:
        commun.telecharger("https://exemple.org/x?api_key=SECRET", attente=10)
    assert pauses == [20, 40] and "SECRET" not in str(erreur.value)
