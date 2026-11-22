"""Vérification EN RÉSEAU des modules bce, eurostat, bis, ocde, fmi (non collecté par pytest).

    python scripts/tests/essai_reseau_sdmx.py            # tout
    python scripts/tests/essai_reseau_sdmx.py bce bis    # quelques sources

Imprime pour chaque série : clé, nombre de points, première date, dernière date, dernière valeur.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import commun  # noqa: E402
from sources import bce, bis, eurostat, fmi, ocde  # noqa: E402

DEBUT = "1990-01-01"

HICP = "HICP/M.{}.N.{}.4D0.ANR"
CLI = "OECD.SDD.STES,DSD_STES@DF_CLI/{}.M.LI...AA...H"
QNA = "OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_G20,1.1/Q.Y.{}.S1.S1.B1GQ._Z._Z._Z.PC.L.GY.T0102"
PAYS_UE = {"BE": "BE", "DE": "DE", "FR": "FR", "IT": "IT", "ZE": "EA21"}
PAYS_FMI = fmi.PAYS_WEO

DEMANDES = {
    "bce": [
        {"cle": "A2", "code": "FM/B.U2.EUR.4F.KR.DFR.LEV", "escalier": True},
        {"cle": "A3", "code": "FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA"},
        {"cle": "B5_2A", "code": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"},
        {"cle": "B5_10A", "code": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"},
        {"cle": "C5", "code": HICP.format("U2", "000000")},
        {"cle": "C6", "code": HICP.format("U2", "XEF000")},
        {"cle": "C7", "code": HICP.format("BE", "000000")},
        {"cle": "C8", "code": HICP.format("DE", "000000")},
        {"cle": "C9", "code": HICP.format("FR", "000000")},
        {"cle": "C10", "code": HICP.format("IT", "000000")},
        {"cle": "D5_LT", "code": "SPF/Q.U2.HICP.POINT.LT.Q.AVG"},
        {"cle": "D12", "code": "INW/Q.U2.N.INWR.000000.4F0.GY.IX"},
        {"cle": "F2", "code": "ILM/W.U2.C.T000000.Z5.Z01"},
        {"cle": "F7", "code": "BSI/M.U2.Y.V.M30.X.I.U2.2300.Z01.A"},
        {"cle": "I1", "code": "EXR/D.USD.EUR.SP00.A"},
        {"cle": "IC_EURGBP", "code": "EXR/D.GBP.EUR.SP00.A"},
        {"cle": "IC_EURCHF", "code": "EXR/D.CHF.EUR.SP00.A"},
        {"cle": "IC_EURJPY", "code": "EXR/D.JPY.EUR.SP00.A"},
        {"cle": "IC_EURCNY", "code": "EXR/D.CNY.EUR.SP00.A"},
        {"cle": "J5", "code": "CISS/D.U2.Z0Z.4F.EC.SS_CIN.IDX"},
        {"cle": "J7", "code": "CISS/D.U2.Z0Z.4F.EC.SS_BMN.CON"},
    ],
    "eurostat": [
        *[{"cle": c, "code": "irt_lt_mcby_m", "filtres": {"geo": g}}
          for c, g in (("B6", "BE"), ("B7", "FR"), ("B8", "IT"), ("X_DE10A_M", "DE"))],
        *[{"cle": f"{c}_secours", "code": "prc_hicp_minr",
           "filtres": {"geo": g, "coicop18": k, "unit": "RCH_A"}}
          for c, g, k in (("C5", "EA", "TOTAL"), ("C6", "EA", "TOT_X_NRG_FOOD"), ("C7", "BE", "TOTAL"),
                          ("C8", "DE", "TOTAL"), ("C9", "FR", "TOTAL"), ("C10", "IT", "TOTAL"))],
        {"cle": "D9", "code": "sts_inppd_m", "filtres": {"indic_bt": "PRC_PRR_DOM", "nace_r2": "B-E36",
                                                          "s_adj": "NSA", "unit": "PCH_SM", "geo": "EA20"}},
        {"cle": "E1_ZE", "code": "namq_10_gdp",
         "filtres": {"unit": "CLV_PCH_SM", "s_adj": "SCA", "na_item": "B1GQ", "geo": "EA21"}},
        {"cle": "PIBN_ZE", "code": "namq_10_gdp",
         "filtres": {"unit": "CP_MEUR", "s_adj": "SCA", "na_item": "B1GQ", "geo": "EA21"}},
        *[{"cle": f"E3T_{p}", "code": "gov_10q_ggdebt",
           "filtres": {"unit": "PC_GDP", "sector": "S13", "na_item": "GD", "geo": g}} for p, g in PAYS_UE.items()],
        *[{"cle": f"E4_{p}", "code": "gov_10q_ggdebt",
           "filtres": {"unit": "MIO_EUR", "sector": "S13", "na_item": "GD", "geo": g}} for p, g in PAYS_UE.items()],
    ],
    "bis": [
        {"cle": "A4_secours", "code": "WS_CBPOL/D.GB"},
        {"cle": "A6", "code": "WS_CBPOL/M.CN"},
        {"cle": "A7", "code": "WS_CBPOL/M.CH"},
        {"cle": "F4", "code": "WS_CBTA/M.GB.B.XDC.GBP.B"},
    ],
    "ocde": [
        {"cle": "C13", "code": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/CHN.M.N.CPI.PA._T.N.GY"},
        *[{"cle": f"D13_{p}", "code": CLI.format(c)}
          for p, c in (("US", "USA"), ("CN", "CHN"), ("JP", "JPN"), ("UK", "GBR"), ("DE", "DEU"), ("G4E", "G4E"))],
        {"cle": "E1_JP", "code": QNA.format("JPN")},
        {"cle": "E1_CN", "code": QNA.format("CHN")},
    ],
    "fmi": [
        {"cle": "C12", "code": "CPI/JPN.CPI._T.YOY_PCH_PA_PT.M"},
        {"cle": "C11_secours", "code": "CPI/GBR.CPI._T.YOY_PCH_PA_PT.M"},
        {"cle": "C13_secours", "code": "CPI/CHN.CPI._T.YOY_PCH_PA_PT.M"},
        *[{"cle": f"E3_{p}", "code": f"WEO/{c}.GGXWDG_NGDP.A"} for p, c in PAYS_FMI.items()],
        *[{"cle": f"E5_{p}", "code": f"WEO/{c}.GGXCNL_NGDP.A"} for p, c in PAYS_FMI.items()],
        *[{"cle": f"X_NGDP_{p}", "code": f"WEO/{PAYS_FMI[p]}.NGDP.A"} for p in ("JP", "CN", "UK")],
    ],
}
MODULES = {"bce": bce, "eurostat": eurostat, "bis": bis, "ocde": ocde, "fmi": fmi}


def afficher(cle: str, resultat) -> bool:
    if isinstance(resultat, commun.ErreurSource):
        print(f"  {cle:<14} ERREUR  {resultat}")
        return False
    dates = list(resultat)
    print(f"  {cle:<14} {len(dates):>6} pts  {dates[0]} → {dates[-1]}  dernière = {resultat[dates[-1]]:.4g}")
    return True


def main(sources: list[str]) -> int:
    commun.charger_env()
    echecs = 0
    for nom in sources:
        demandes = [dict(d, debut=DEBUT) for d in DEMANDES[nom]]
        t0 = time.monotonic()
        resultats = MODULES[nom].telecharger(demandes)
        print(f"{nom} ({time.monotonic() - t0:.1f} s)")
        for d in demandes:
            echecs += not afficher(d["cle"], resultats.get(d["cle"], commun.ErreurSource("aucun résultat")))
        if nom == "bce":
            try:
                spf = bce.telecharger_spf()
                print(f"  spf_bce        enquête {spf['enquete']}, {len(spf['classes'])} classes")
                for h in spf["horizons"]:
                    print(f"    {h['cle']:<5} année {h['annee']}  moyenne {h['moyenne']}  réponses {h['reponses']}"
                          f"/{h['reponses_probabilites']}  somme {sum(p or 0 for p in h['probabilites']):.2f}"
                          f"  <1,8 {h['sous_1_8']:.1f}  ≈2 {h['proche_de_2']:.1f}  >2,2 {h['au_dessus_de_2_2']:.1f}")
            except commun.ErreurSource as erreur:
                echecs += 1
                print(f"  spf_bce        ERREUR  {erreur}")
        if nom == "fmi":
            try:
                t0 = time.monotonic()
                weo = fmi.telecharger_weo()
                print(f"  fmi (WEO)      édition {weo['edition']} ({weo['publiee_le']}), dernière année observée "
                      f"{weo['derniere_annee_observee']} {weo['derniere_annee_par_pays']} ({time.monotonic() - t0:.1f} s)")
                for ind, par_pays in weo["valeurs"].items():
                    us = par_pays.get("US", {})
                    print(f"    {ind:<12} {len(par_pays)} pays ; US {sorted(us)[:1]}…{sorted(us)[-1:]} "
                          f"2026 = {us.get(2026)}")
            except commun.ErreurSource as erreur:
                echecs += 1
                print(f"  fmi (WEO)      ERREUR  {erreur}")
    print(f"{echecs} échec(s)")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or list(DEMANDES)))
