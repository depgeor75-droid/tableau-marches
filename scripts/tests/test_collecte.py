"""Tests de robustesse de la collecte (§12) : aucune clé dans les fichiers écrits, écriture
déterministe, accents conservés, compteur d'échecs, calculs du résumé sans connaissance du futur."""
import os
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sources"))

import calculs as C  # noqa: E402
import collect  # noqa: E402
import commun  # noqa: E402
import config as configuration  # noqa: E402
import ecriture  # noqa: E402
import resume  # noqa: E402
from commun import ErreurSource  # noqa: E402

CLE = "0123456789abcdef0123456789abcdef"


def mois(debut_annee, n, f):
    return {f"{debut_annee + i // 12}-{i % 12 + 1:02d}-01": f(i) for i in range(n)}


def jours(debut: date, n, f):
    from datetime import timedelta
    sortie, d, i = {}, debut, 0
    while len(sortie) < n:
        if d.weekday() < 5:
            sortie[d.isoformat()] = f(i)
            i += 1
        d += timedelta(days=1)
    return sortie


class ModuleQuiPlante:
    """Simule une panne réseau dont le message contient l'adresse d'appel avec la clé."""

    @staticmethod
    def telecharger(demandes):
        raise RuntimeError(f"HTTPSConnectionPool : https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={CLE} timed out")


def collecte_vide(tmp_path, declencheur="local", monkeypatch=None, etat_precedent=None):
    cfg = configuration.charger()
    existant = {"historique": {}, "recent": {}, "etat": etat_precedent or {}, "resume": {}, "previsions": {}, "catalogue": {}}
    col = collect.Collecte(cfg, existant, declencheur, date(2026, 11, 22), lambda m: None, None)
    tele = collect.Telechargements(lambda m: None)
    col._tele = tele
    monkeypatch.setattr(collect, "_module", lambda source: ModuleQuiPlante)
    tele.lancer(col.specs())
    col.weo = "cadence"
    col.assembler(tele)
    col.calculer()
    return cfg, col, existant


def test_aucune_cle_dans_les_fichiers_ecrits(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FRED_API_KEY", CLE)
    cfg, col, existant = collecte_vide(tmp_path, monkeypatch=monkeypatch)
    ecriture.ecrire(cfg, col, existant, tmp_path, "local", None, set())
    sortie = capsys.readouterr()
    for fichier in tmp_path.iterdir():
        contenu = fichier.read_text(encoding="utf-8")
        assert CLE not in contenu, fichier.name
        assert "api.stlouisfed.org/fred" not in contenu, fichier.name
    assert CLE not in sortie.out + sortie.err
    etat = commun.lire_js(tmp_path / "etat.js")
    assert etat["series"]["B1"]["statut"] == "erreur"
    assert "clé masquée" in etat["series"]["B1"]["message"] or "masqué" in etat["series"]["B1"]["message"]


def test_nettoyer_retire_cle_et_adresse(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", CLE)
    texte = commun.nettoyer(f"Échec : https://api.stlouisfed.org/x?api_key={CLE}&file_type=json (délai dépassé)")
    assert CLE not in texte and "api_key=" not in texte.replace("api_key=«masqué»", "")
    assert "[api.stlouisfed.org]" in texte and "Échec" in texte and "délai" in texte


def test_compteur_echecs_planifies_seulement(tmp_path, monkeypatch):
    precedent = {"series": {"B1": {"statut": "erreur", "echecs": 2}}}
    cfg, col, existant = collecte_vide(tmp_path, "schedule", monkeypatch, precedent)
    ecriture.ecrire(cfg, col, existant, tmp_path, "schedule", None, set())
    etat = commun.lire_js(tmp_path / "etat.js")
    assert etat["series"]["B1"]["echecs"] == 3
    assert etat["alerte"]["declenchee"] is True  # B1 essentielle, 3 échecs planifiés
    autre = tmp_path / "manuel"
    autre.mkdir()
    cfg, col, existant = collecte_vide(autre, "workflow_dispatch", monkeypatch, precedent)
    ecriture.ecrire(cfg, col, existant, autre, "workflow_dispatch", None, set())
    assert commun.lire_js(autre / "etat.js")["series"]["B1"]["echecs"] == 2  # inchangé lors d'un échec manuel


def test_ecriture_deterministe_et_accents(tmp_path, monkeypatch):
    cfg, col, existant = collecte_vide(tmp_path, monkeypatch=monkeypatch)
    col.natives["B1"] = jours(date(2020, 1, 1), 1800, lambda i: 1 + (i % 50) / 10)
    col.etats["B1"] = {"source": "Trésor américain via FRED", "role": "principale", "message": "", "date_source": max(col.natives["B1"])}
    col.natives["C5"] = mois(1997, 359, lambda i: 2 + (i % 24) / 10)
    col.etats["C5"] = {"source": "BCE", "role": "principale", "message": "", "date_source": max(col.natives["C5"])}
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(); b.mkdir()
    ecriture.ecrire(cfg, col, existant, a, "local", None, set())
    ecriture.ecrire(cfg, col, existant, b, "local", None, set())
    for f in a.iterdir():
        if f.name == "etat.js":
            continue
        assert f.read_bytes() == (b / f.name).read_bytes(), f.name
    catalogue = (a / "catalogue.js").read_text(encoding="utf-8")
    assert "Taux de dépôt BCE" in catalogue and "Pétrole Brent" in catalogue
    assert "\\u00e9" not in catalogue  # accents écrits tels quels
    csv = (a / "donnees_mensuelles.csv").read_bytes()
    assert csv.startswith(b"\xef\xbb\xbf")  # utf-8-sig : accents corrects dans Excel
    assert "Inflation zone euro" in csv.decode("utf-8-sig")
    # Relancer sans donnée nouvelle ne modifie rien (hors etat.js)
    avant = {f.name: f.read_bytes() for f in a.iterdir()}
    existant2 = collect.lire_existant(a)
    ecriture.ecrire(cfg, col, existant2, a, "local", None, set())
    for f in a.iterdir():
        if f.name != "etat.js":
            assert f.read_bytes() == avant[f.name], f.name


def test_historique_mois_complets_et_recent():
    native = jours(date(2026, 9, 1), 60, float)
    h = ecriture.historique_depuis_native(native, "J", date(2026, 11, 22))
    assert "2026-11-01" not in h and "2026-10-01" in h  # novembre n'est pas terminé
    r = ecriture.recent_depuis_native(native, "J", date(2026, 11, 22), 36)
    assert r == native


def test_pourcentage_pib_trimestre_manquant():
    bilan = {"2025-03-26": 7000.0, "2025-06-25": 7100.0, "2025-09-24": 6900.0}
    pib = {"2024-04-01": 100.0, "2024-07-01": 100.0, "2024-10-01": 100.0, "2025-01-01": 100.0, "2025-04-01": 120.0}
    r = collect.pourcentage_pib(bilan, pib, "somme")
    assert r["2025-01-01"] == pytest.approx(7000 / 400 * 100)
    assert r["2025-04-01"] == pytest.approx(7100 / 420 * 100)
    assert "2025-07-01" not in r  # PIB du 3e trimestre absent : aucun report d'un PIB ancien
    r = collect.pourcentage_pib(bilan, pib, "moyenne")
    assert r["2025-01-01"] == pytest.approx(7000 / 100 * 100)


def test_jauge_historique_sans_connaissance_du_futur():
    reg = configuration.charger().reglages["jauges"]
    base = {
        "C3": mois(1990, 420, lambda i: 2 + (i % 30) / 10),
        "J1": mois(1990, 420, lambda i: 15 + (i % 40)),
        "J4": mois(1990, 420, lambda i: (i % 20) / 10 - 1),
        "B1": mois(1990, 420, lambda i: 4 + (i % 10) / 10),
        "J6": mois(1990, 420, lambda i: 1 + (i % 15) / 10),
        "A1": mois(1990, 420, lambda i: (i % 60) / 10),
    }
    t = "2010-06-01"
    tronquees = {k: {d: v for d, v in s.items() if d <= t} for k, s in base.items()}
    assert resume.evaluer_conditions("US", base, t, reg) == resume.evaluer_conditions("US", tronquees, t, reg)
    # moins de 10 ans d'historique : condition « non évaluée »
    jeune = {k: {d: v for d, v in s.items() if d >= "2005-01-01"} for k, s in base.items()}
    c = resume.evaluer_conditions("US", jeune, t, reg)
    assert c[1]["ok"] is None  # peur (percentile) non évaluée


def test_lecture_du_score():
    assert resume.lecture_score(1, 6) == "faible"
    assert resume.lecture_score(2, 6) == "possible"
    assert resume.lecture_score(4, 6) == "eleve"
    assert resume.lecture_score(2, 5) == "possible"
    assert resume.lecture_score(0, 0) is None


def test_mouvement_sept_jours_calendaires_serie_continue():
    from datetime import timedelta
    d0 = date(2020, 1, 1)
    serie = {(d0 + timedelta(days=i)).isoformat(): 3.0 + (0.01 if i % 2 else 0) for i in range(2500)}  # 7 jours sur 7
    derniere = max(serie)
    serie[derniere] = 4.0
    s = C.score_mouvement(serie, "T")
    assert s["depuis"] == C.recul(derniere, jours=7)
    assert s["rapport"] > 10


def test_direction_trimestrielle_par_date():
    serie = {f"{2000 + i // 4}-{(i % 4) * 3 + 1:02d}-01": float(i % 5) for i in range(100)}
    r = resume.C.direction(serie, "T")
    derniere = max(serie)
    assert r["variation"] == serie[derniere] - serie[C.ajouter_mois(derniere, -3)]
