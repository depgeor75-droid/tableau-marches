"""Tests hors réseau du module Yahoo : la réponse de yfinance est simulée par des DataFrame."""
import logging
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commun import ErreurSource  # noqa: E402
from sources import yahoo  # noqa: E402

NAN = np.nan
# Dimanche 22 novembre 2026, 5 h 17 UTC : heure de la collecte planifiée
DIMANCHE = datetime(2026, 11, 22, 5, 17, tzinfo=timezone.utc)
CHAMPS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def tableau(par_code: dict, index) -> pd.DataFrame:
    """Imite yf.download(..., group_by="ticker") : colonnes (Ticker, Price)."""
    blocs, cles = [], []
    idx = pd.DatetimeIndex(pd.to_datetime(index), name="Date") if not isinstance(index, pd.DatetimeIndex) else index
    for code, closes in par_code.items():
        donnees = {c: closes for c in CHAMPS}
        donnees["Adj Close"] = [v * 0.9 if v == v else v for v in closes]  # ne doit jamais être lu
        blocs.append(pd.DataFrame(donnees, index=idx))
        cles.append(code)
    return pd.concat(blocs, axis=1, keys=cles, names=["Ticker", "Price"])


class FauxYahoo:
    """Remplace yf.download : réponses programmées par appel, journal des appels."""

    def __init__(self, reponses):
        self.reponses = list(reponses)  # chaque élément : DataFrame, Exception, ou (DataFrame, {code: msg})
        self.appels = []

    def __call__(self, codes, **kwargs):
        self.appels.append((list(codes), kwargs))
        rep = self.reponses.pop(0) if self.reponses else pd.DataFrame()
        if isinstance(rep, Exception):
            raise rep
        if isinstance(rep, tuple):
            rep, erreurs = rep
            journal = logging.getLogger("yfinance")
            for code, msg in erreurs.items():
                journal.error(f"\n1 Failed download:")
                journal.error(f"['{code}']: {msg}")
        return rep


@pytest.fixture
def faux(monkeypatch):
    def installer(reponses):
        f = FauxYahoo(reponses)
        monkeypatch.setattr(yahoo.yf, "download", f)
        monkeypatch.setattr(yahoo, "_dormir", lambda s: None)
        return f
    return installer


# ------------------------------------------------------------------ séries
def test_appel_groupe_nan_doublons_negatif(faux):
    idx = ["2020-04-17", "2020-04-20", "2020-04-20", "2020-04-21", "2020-04-22"]
    df = tableau({"CL=F": [18.27, NAN, -37.63, 10.01, NAN],
                  "^GSPC": [2874.56, 2823.16, NAN, 2736.56, 2799.31]}, idx)
    f = faux([df])
    r = yahoo.telecharger([{"cle": "H2", "code": "CL=F"}, {"cle": "G2", "code": "^GSPC"}],
                          attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert len(f.appels) == 1
    codes, kw = f.appels[0]
    assert sorted(codes) == ["CL=F", "^GSPC"]
    assert kw == {"start": "1989-01-01", "auto_adjust": False, "group_by": "ticker",
                  "threads": False, "progress": False}
    assert r["H2"] == {"2020-04-17": 18.27, "2020-04-20": -37.63, "2020-04-21": 10.01}
    assert r["G2"] == {"2020-04-17": 2874.56, "2020-04-20": 2823.16, "2020-04-21": 2736.56,
                       "2020-04-22": 2799.31}
    assert list(r["G2"]) == sorted(r["G2"])
    assert all(not math.isnan(v) for v in r["H2"].values())


def test_code_vide_rattrape_seul(faux):
    idx = ["2026-11-19", "2026-11-20"]
    groupe = tableau({"^GSPC": [7175.83, 6910.39], "AED.BR": [NAN, NAN]}, idx)
    seul = tableau({"AED.BR": [63.70, 63.60]}, idx)
    f = faux([groupe, seul])
    r = yahoo.telecharger([{"cle": "G2", "code": "^GSPC"}, {"cle": "K1", "code": "AED.BR"}],
                          attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert [a[0] for a in f.appels][1] == ["AED.BR"]
    assert len(f.appels) == 2
    assert r["K1"] == {"2026-11-19": 63.70, "2026-11-20": 63.60}
    assert r["G2"]["2026-11-20"] == 6910.39


def test_echec_isole_et_message_francais(faux):
    idx = ["2026-11-20"]
    groupe = (tableau({"^GSPC": [6910.39], "ZZZ.XX": [NAN]}, idx),
              {"ZZZ.XX": "possibly delisted; no timezone found"})
    vide = (pd.DataFrame(), {"ZZZ.XX": "possibly delisted; no timezone found"})
    f = faux([groupe, vide, vide, vide])
    r = yahoo.telecharger([{"cle": "G2", "code": "^GSPC"}, {"cle": "X", "code": "zzz.xx"}],
                          attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert r["G2"] == {"2026-11-20": 6910.39}
    assert isinstance(r["X"], ErreurSource)
    assert "code inconnu ou retiré" in str(r["X"]) and "ZZZ.XX" in str(r["X"])
    # code inconnu confirmé par un appel individuel : pas d'autre essai
    assert len(f.appels) == 2


def test_trois_essais_puis_erreur(faux):
    vide = pd.DataFrame()
    f = faux([vide] * 5)
    r = yahoo.telecharger([{"cle": "H4", "code": "TTF=F"}], attentes=(1, 2, 3), maintenant=DIMANCHE)
    assert len(f.appels) == 4  # appel groupé + 3 rattrapages
    assert "aucune donnée" in str(r["H4"]) and "4 essais" in str(r["H4"])


def test_attentes_respectees(faux, monkeypatch):
    f = faux([pd.DataFrame()] * 4)
    vues = []
    monkeypatch.setattr(yahoo, "_dormir", vues.append)
    yahoo.telecharger([{"cle": "H4", "code": "TTF=F"}], attentes=(20, 60, 180), maintenant=DIMANCHE)
    assert vues == [20, 60, 180]
    assert len(f.appels) == 4


def test_limite_de_debit_interrompt_le_tour(faux):
    idx = ["2026-11-20"]
    limite = (pd.DataFrame(), {"A": "YFRateLimitError('Too Many Requests. Rate limited.')"})
    f = faux([
        (pd.DataFrame(), {"A": "Too Many Requests", "B": "Too Many Requests"}),  # groupé
        limite,                                       # tour 1 : A bloqué -> B attend
        tableau({"A": [1.0]}, idx), tableau({"B": [2.0]}, idx),  # tour 2
    ])
    r = yahoo.telecharger([{"cle": "a", "code": "A"}, {"cle": "b", "code": "B"}],
                          attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert [a[0] for a in f.appels] == [["A", "B"], ["A"], ["A"], ["B"]]
    assert r == {"a": {"2026-11-20": 1.0}, "b": {"2026-11-20": 2.0}}


def test_panne_de_l_appel_groupe(faux):
    idx = ["2026-11-20"]
    f = faux([ConnectionError("Max retries exceeded with url: https://query2.finance.yahoo.com/v8?x=1"),
              tableau({"GC=F": [3515.4]}, idx), RuntimeError("boum")] + [RuntimeError("boum")] * 3)
    r = yahoo.telecharger([{"cle": "H3", "code": "GC=F"}, {"cle": "H5", "code": "NG=F"}],
                          attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert r["H3"] == {"2026-11-20": 3515.4}
    assert isinstance(r["H5"], ErreurSource)
    assert "https://" not in str(r["H5"])


def test_meme_code_pour_deux_cles_et_demande_sans_code(faux):
    f = faux([tableau({"BZ=F": [89.95]}, ["2026-11-20"])])
    r = yahoo.telecharger([{"cle": "H1", "code": "BZ=F"}, {"cle": "H1_bis", "code": "bz=f"},
                           {"cle": "vide", "code": ""}], attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert len(f.appels) == 1 and f.appels[0][0] == ["BZ=F"]
    assert r["H1"] == r["H1_bis"] == {"2026-11-20": 89.95}
    assert isinstance(r["vide"], ErreurSource)


def test_colonnes_sans_niveau_ticker_pour_un_seul_code(faux):
    idx = pd.DatetimeIndex(["2026-11-19", "2026-11-20"], name="Date")
    plat = pd.DataFrame({"Close": [103.5, 103.81], "Adj Close": [1.0, 1.0]}, index=idx)
    faux([plat])
    r = yahoo.telecharger([{"cle": "I6", "code": "DX-Y.NYB"}], attentes=(0, 0, 0), maintenant=DIMANCHE)
    assert r["I6"] == {"2026-11-19": 103.5, "2026-11-20": 103.81}


# ------------------------------------------------------------------ dates et séance en cours
def test_index_avec_fuseau_date_locale_de_la_bourse():
    idx = pd.DatetimeIndex(["2026-11-19 00:00", "2026-11-20 00:00"]).tz_localize("Asia/Tokyo")
    df = tableau({"^N225": [48000.0, 48500.0]}, idx)
    s = yahoo.serie_depuis_tableau(df, "^N225", DIMANCHE)
    assert s == {"2026-11-19": 48000.0, "2026-11-20": 48500.0}  # pas le 18 et le 19 (UTC)


def test_seance_asiatique_ouverte_a_5h17_utc():
    # vendredi 20 novembre 2026, 5 h 17 UTC = 14 h 17 à Tokyo, 13 h 17 à Shanghai
    vendredi = datetime(2026, 11, 20, 5, 17, tzinfo=timezone.utc)
    idx = ["2026-11-19", "2026-11-20"]
    df = tableau({"^N225": [48000.0, 48100.0], "510300.SS": [4.5, 4.6], "^GSPC": [7175.83, NAN]}, idx)
    assert yahoo.serie_depuis_tableau(df, "^N225", vendredi) == {"2026-11-19": 48000.0}
    assert yahoo.serie_depuis_tableau(df, "510300.SS", vendredi) == {"2026-11-19": 4.5}
    # après la clôture de Tokyo (16 h locale = 7 h UTC), la ligne du jour est gardée
    plus_tard = datetime(2026, 11, 20, 7, 30, tzinfo=timezone.utc)
    assert yahoo.serie_depuis_tableau(df, "^N225", plus_tard)["2026-11-20"] == 48100.0


def test_ligne_datee_du_lendemain_ecartee():
    # contrats à terme de New York : à 23 h UTC le 20 (18 h à New York), une ligne du 21 est écartée
    soir = datetime(2026, 11, 20, 23, 0, tzinfo=timezone.utc)
    s = {"2026-11-20": 89.95, "2026-11-21": 90.1}
    assert yahoo.ecarter_seance_en_cours(s, "BZ=F", soir) == {"2026-11-20": 89.95}
    matin = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)  # 9 h à New York
    assert yahoo.ecarter_seance_en_cours(s, "BZ=F", matin) == {}


def test_tableau_vide_ou_absent():
    assert yahoo.serie_depuis_tableau(None, "X", DIMANCHE) == {}
    assert yahoo.serie_depuis_tableau(pd.DataFrame(), "X", DIMANCHE) == {}
    df = tableau({"A": [1.0]}, ["2026-11-20"])
    assert yahoo.serie_depuis_tableau(df, "B", DIMANCHE) == {}


# ------------------------------------------------------------------ courbe du pétrole
def test_liste_des_contrats():
    liste = yahoo.contrats_brent(date(2026, 11, 22))
    assert len(liste) == 13
    assert liste[0] == ("2026-12", "BZZ26.NYM")
    assert liste[1] == ("2027-01", "BZF27.NYM")
    assert liste[5] == ("2027-05", "BZK27.NYM")
    assert liste[11] == ("2027-11", "BZX27.NYM")
    assert liste[-1] == ("2027-12", "BZZ27.NYM")
    assert yahoo.contrats_brent(date(2026, 12, 5))[0] == ("2027-01", "BZF27.NYM")
    assert yahoo.contrats_brent(date(2027, 1, 31))[-1] == ("2028-02", "BZG28.NYM")


def test_jours_ouvrables_avant():
    assert yahoo.jours_ouvrables_avant(date(2026, 11, 22), 5) == date(2026, 11, 16)
    assert yahoo.jours_ouvrables_avant(date(2026, 11, 25), 5) == date(2026, 11, 18)


def test_choix_des_echeances():
    jour = date(2026, 11, 22)
    pts = [{"echeance": e, "prix": p} for e, p in
           [("2027-04", 85.0), ("2027-05", 84.37), ("2027-06", 83.0), ("2027-11", 78.08)]]
    assert yahoo.choisir_echeance(pts, jour, 6) == {"echeance": "2027-05", "prix": 84.37}
    assert yahoo.choisir_echeance(pts, jour, 12) == {"echeance": "2027-11", "prix": 78.08}
    sans_mai = [p for p in pts if p["echeance"] != "2027-05"]
    assert yahoo.choisir_echeance(sans_mai, jour, 6)["echeance"] == "2027-04"  # ± 1 mois, le plus tôt
    juin_seul = [p for p in pts if p["echeance"] in ("2027-06", "2027-11")]
    assert yahoo.choisir_echeance(juin_seul, jour, 6)["echeance"] == "2027-06"
    assert yahoo.choisir_echeance([{"echeance": "2027-08", "prix": 1.0}], jour, 6) is None
    assert yahoo.choisir_echeance([{"echeance": "2027-12", "prix": 77.35}], jour, 12)["echeance"] == "2027-12"


def _courbe_simulee(manquants=(), perime=()):
    idx = ["2026-11-10", "2026-11-19", "2026-11-20"]
    donnees = {"BZ=F": [88.0, 90.1, 89.95]}
    for i, (echeance, code) in enumerate(yahoo.contrats_brent(date(2026, 11, 22))):
        if code in manquants:
            donnees[code] = [NAN, NAN, NAN]
        elif code in perime:
            donnees[code] = [80.0, NAN, NAN]
        else:
            donnees[code] = [NAN, 93.0 - i, 92.57 - i]
    return tableau(donnees, idx)


def test_courbe_petrole_complete(faux):
    f = faux([_courbe_simulee(manquants=("BZZ26.NYM",), perime=("BZJ27.NYM",))])
    c = yahoo.telecharger_courbe_petrole(date(2026, 11, 22), maintenant=DIMANCHE)
    assert len(f.appels) == 1 and len(f.appels[0][0]) == 14  # BZ=F + 13 contrats, un seul appel
    assert f.appels[0][1]["start"] == "2026-11-01"
    assert c["statut"] == "ok" and c["produit"] == "Brent" and c["unite"] == "USD/baril"
    assert c["date"] == "2026-11-20"
    assert c["comptant"] == {"valeur": 89.95, "contrat": "BZ=F"}
    echeances = [p["echeance"] for p in c["points"]]
    assert echeances == sorted(echeances)
    assert "2026-12" not in echeances and "2027-04" not in echeances  # absent ; périmé (10 nov.)
    assert len(c["points"]) == 11
    assert c["points"][0] == {"echeance": "2027-01", "contrat": "BZF27.NYM", "prix": 91.57}
    assert c["dans_6_mois"]["echeance"] == "2027-05"
    assert c["dans_12_mois"]["echeance"] == "2027-11"


def test_courbe_trop_courte(faux):
    codes = [c for _, c in yahoo.contrats_brent(date(2026, 11, 22))]
    faux([_courbe_simulee(manquants=codes[:8])])
    c = yahoo.telecharger_courbe_petrole(date(2026, 11, 22), maintenant=DIMANCHE)
    assert isinstance(c, ErreurSource)
    assert "5 contrat(s)" in str(c)


def test_courbe_appel_en_panne(faux):
    faux([TimeoutError("read timed out")])
    c = yahoo.telecharger_courbe_petrole(date(2026, 11, 22), maintenant=DIMANCHE)
    assert isinstance(c, ErreurSource) and "délai" in str(c)
