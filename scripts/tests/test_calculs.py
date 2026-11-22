"""Tests des calculs et de la fusion (§12)."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import calculs as c  # noqa: E402
import fusion as f  # noqa: E402


def mois(debut_annee, n, valeurs):
    sortie = {}
    for i in range(n):
        a, m = debut_annee + i // 12, i % 12 + 1
        sortie[f"{a}-{m:02d}-01"] = valeurs(i)
    return sortie


def test_glissement_annuel_apparie_par_date():
    s = mois(2024, 24, lambda i: 100 + i)
    g = c.glissement_annuel(s)
    assert "2024-12-01" not in g
    assert abs(g["2025-01-01"] - (112 / 100 - 1) * 100) < 1e-12


def test_glissement_annuel_mois_manquant_reste_manquant():
    s = mois(2024, 24, lambda i: 100 + i)
    del s["2024-10-01"]  # comme l'IPC américain d'octobre 2025
    g = c.glissement_annuel(s)
    assert "2025-10-01" not in g          # pas de valeur un an plus tôt
    assert "2024-10-01" not in g
    assert "2025-11-01" in g               # le mois suivant reste calculable
    # pas de décalage de ligne : novembre 2025 est comparé à novembre 2024
    assert abs(g["2025-11-01"] - (s["2025-11-01"] / s["2024-11-01"] - 1) * 100) < 1e-12


def test_ecart_et_croise():
    a = {"2026-01-01": 3.5, "2026-02-01": 3.6, "2026-03-01": 3.7}
    b = {"2026-01-01": 2.5, "2026-03-01": 2.0}
    assert c.ecart(a, b) == {"2026-01-01": 1.0, "2026-03-01": 1.7000000000000002}
    jpy_par_eur = {"2026-01-02": 160.0}
    usd_par_eur = {"2026-01-02": 1.0, "2026-01-03": 1.1}
    assert c.croise(jpy_par_eur, usd_par_eur) == {"2026-01-02": 160.0}


def test_pourcentage_pib():
    bilan = {"2026-01-01": 7000.0}
    pib = {"2026-01-01": 28000.0}
    assert c.produit(bilan, c.inverse(pib), 100) == {"2026-01-01": 25.0}


def test_valeur_nulle_ou_negative():
    assert c.variation("N", -37.6, 20.0) is None
    assert c.variation("N", 0, 5) is None
    assert c.variation("T", -0.5, 0.25) == 0.75
    s = {"2020-03-01": 20.0, "2020-04-01": -37.63, "2021-04-01": 60.0}
    g = c.glissement_annuel(s)
    assert "2021-04-01" not in g  # base négative : pas de variation en %


def test_percentiles_types_T_et_N():
    # T : rang du niveau
    s = mois(1990, 400, lambda i: float(i % 100))
    p = c.percentile_carte(s, "T")
    assert p["base"] == "niveau" and 0 <= p["valeur"] <= 100
    assert p["depuis"] == "1993"  # dernière valeur avr. 2023 : 30 ans au plus
    # N : rang de la variation sur 12 mois, pas du niveau (une tendance de fond n'est pas « au plus haut »)
    tendance = mois(1990, 400, lambda i: 100 * 1.003 ** i * (1.05 if i == 399 else 1))
    pn = c.percentile_carte(tendance, "N")
    assert pn["base"] == "variation_12m"
    assert pn["valeur"] == 100 or pn["libelle"] == "très élevé"
    # moins de 5 ans → pas de percentile ; moins de 10 ans → historique court
    assert c.percentile_carte(mois(2023, 40, float), "T")["valeur"] is None
    assert c.percentile_carte(mois(2018, 90, float), "T")["court"] is True
    assert c.libelle_percentile(5) == "très bas" and c.libelle_percentile(85) == "élevé"


def test_fusion_garde_les_anciennes_donnees_en_cas_de_panne():
    ancienne = mois(2000, 100, float)
    serie, anomalie = f.fusionner(ancienne, None)
    assert serie == ancienne and anomalie is None
    serie, _ = f.fusionner(ancienne, {})
    assert serie == ancienne


def test_fusion_remplace_par_une_serie_valide_revisee():
    ancienne = mois(2000, 100, float)
    nouvelle = dict(ancienne)
    nouvelle["2005-01-01"] = 999.0  # révision officielle
    nouvelle["2008-05-01"] = 100.0  # point nouveau
    serie, anomalie = f.fusionner(ancienne, nouvelle)
    assert serie == nouvelle and anomalie is None


def test_garde_fou_reponse_tronquee():
    ancienne = mois(1990, 400, float)
    debut_tardif = {d: v for d, v in ancienne.items() if d >= "2000-01-01"}
    serie, anomalie = f.fusionner(ancienne, debut_tardif)
    assert serie == ancienne and "tronquée" in anomalie
    trouee = {d: v for i, (d, v) in enumerate(ancienne.items()) if i % 10}
    serie, anomalie = f.fusionner(ancienne, trouee)
    assert serie == ancienne and "tronquée" in anomalie


def test_controle_des_raccords():
    principale = {"2026-11-13": 1.10, "2026-11-14": 1.11}
    rapide = {"2026-11-14": 1.12, "2026-11-17": 1.13, "2026-11-18": 1.14}
    serie, provisoires, info = f.raccorder("N", principale, rapide)
    assert provisoires == ["2026-11-17", "2026-11-18"]
    assert serie["2026-11-14"] == 1.11  # la source principale prime à la jonction
    assert info["date"] == "2026-11-14" and info["alerte"] is None
    _, _, info = f.raccorder("N", {"2026-11-14": 100.0}, {"2026-11-14": 103.0})
    assert info["alerte"]  # 3 % > 2 %
    _, _, info = f.raccorder("T", {"2026-11-14": 4.00}, {"2026-11-14": 4.12})
    assert info["alerte"]  # 0,12 point > 0,10


def test_detection_des_retards():
    aujourd_hui = date(2026, 11, 22)
    assert f.est_en_retard("2026-11-20", "J", aujourd_hui)[0] is False
    assert f.est_en_retard("2026-11-10", "J", aujourd_hui)[0] is True
    assert f.est_en_retard("2026-11-06", "S", aujourd_hui)[0] is True
    assert f.est_en_retard("2026-09-01", "M", aujourd_hui)[0] is False   # fin sept. + 52 j
    assert f.est_en_retard("2026-08-01", "M", aujourd_hui)[0] is True    # fin août + 83 j
    assert f.est_en_retard("2026-07-01", "T", aujourd_hui)[0] is False   # T3 : fin sept. + 52 j
    assert f.est_en_retard("2026-01-01", "T", aujourd_hui)[0] is True
    assert f.est_en_retard("2025-01-01", "A", aujourd_hui)[0] is False   # fin 2025 + 11 mois
    assert f.est_en_retard("2024-01-01", "A", aujourd_hui)[0] is True
    assert f.est_en_retard("2026-07-01", "M", aujourd_hui, retard_max_jours=150)[0] is False


def test_probabilite_recession():
    assert abs(c.probabilite_recession(0.0, 0.0, -1.0) - 50.0) < 1e-9
    assert c.probabilite_recession(-1.0, -0.5333, -0.6330) > c.probabilite_recession(1.0, -0.5333, -0.6330)
