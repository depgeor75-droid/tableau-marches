"""Essai EN RÉSEAU des modules boe, bundesbank, mof_japon, boj, ons, banque_mondiale, fichiers.

Lancer à la main : `python scripts/tests/essai_reseau_fichiers.py` (pas collecté par pytest).
Imprime pour chaque série : clé, nombre de points, première date, dernière date, dernière valeur ;
vérifie la formule de D14 sur les lignes du fichier, puis affiche le jeu spf_us.
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commun import ErreurSource, telecharger as get  # noqa: E402
from sources import banque_mondiale, boe, boj, bundesbank, fichiers, mof_japon, ons  # noqa: E402

CLE_B4 = "BBSIS/{}.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A"

ESSAIS = [
    (boe, [{"cle": "A4", "code": "IUDBEDR"}, {"cle": "B9", "code": "IUDMNPY"}]),
    (bundesbank, [{"cle": "B4", "code": CLE_B4.format("D")},
                  {"cle": "B4_avant", "code": CLE_B4.format("M"), "fin": "1997-07-01"}]),
    (mof_japon, [{"cle": "B10", "code": "10Y"}]),
    (boj, [{"cle": "A5_secours", "code": "FM01/STRDCLUCON"}]),
    (ons, [{"cle": "C11", "code": "d7g7/mm23", "frequence": "M"},
           {"cle": "E1_UK", "code": "abmi/pn2", "frequence": "T"},
           {"cle": "PIBN_UK", "code": "ybha/pn2", "frequence": "T"}]),
    (banque_mondiale, [{"cle": "H1_secours", "code": "Crude oil, Brent"},
                       {"cle": "H2_secours", "code": "Crude oil, WTI"},
                       {"cle": "H3_secours", "code": "Gold"},
                       {"cle": "H4_secours", "code": "Natural gas, Europe"},
                       {"cle": "H5_secours", "code": "Natural gas, US"},
                       {"cle": "H6_secours", "code": "Copper"}]),
    (fichiers, [{"cle": "D10", "code": "gscpi"},
                {"cle": "D14", "code": "nyfed_recession"},
                {"cle": "D14_ECART", "code": "nyfed_recession", "colonne": "Spread"},
                {"cle": "J3", "code": "gpr_mensuel", "colonne": "GPR"},
                {"cle": "J3_Q", "code": "gpr_quotidien", "colonne": "GPRD"},
                {"cle": "J6", "code": "ebp", "colonne": "gz_spread"},
                {"cle": "J6_EBP", "code": "ebp", "colonne": "ebp"},
                {"cle": "J2", "code": "vstoxx"}]),
]


def verifier_d14() -> bool:
    """P(t+12) = Φ(−0,5333 − 0,6330 × écart(t)) sur toutes les lignes du fichier."""
    table = fichiers.lire_fichier("nyfed_recession", get(fichiers.FICHIERS["nyfed_recession"]["url"]).content)
    ecart, prob = table["spread"], table["rec_prob"]
    phi = NormalDist().cdf
    ecarts = [abs(phi(-0.5333 - 0.6330 * e) - prob[fichiers.ajouter_mois(d, 12)]) * 100
              for d, e in ecart.items() if fichiers.ajouter_mois(d, 12) in prob]
    pire = max(ecarts) if ecarts else float("nan")
    ok = bool(ecarts) and pire < 0.01
    print(f"D14 formule : {len(ecarts)} lignes comparées, écart maximal {pire:.2e} point -> {'OK' if ok else 'ÉCHEC'}")
    return ok


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    echecs = 0
    for module, demandes in ESSAIS:
        resultats = module.telecharger(demandes)
        for demande in demandes:
            r = resultats.get(demande["cle"])
            if isinstance(r, ErreurSource) or not r:
                echecs += 1
                print(f"{demande['cle']:<11} ERREUR : {r}")
                continue
            dates = list(r)
            print(f"{demande['cle']:<11} {len(r):>6} points  {dates[0]} -> {dates[-1]}  dernière valeur {r[dates[-1]]:.4f}")
    if not verifier_d14():
        echecs += 1
    try:
        spf = fichiers.telecharger_spf_us()
        print("spf_us :", spf["enquete"], [(h["annee"], h["sous_2"], round(sum(h["probabilites"]), 2))
                                           for h in spf["horizons"]])
    except ErreurSource as erreur:
        echecs += 1
        print("spf_us ERREUR :", erreur)
    print("Échecs :", echecs)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
