"""Construction de data/resume.js : tout ce qui est précalculé pour l'Accueil et les cartes
(PLAN §6.3 et §8). Que des nombres et des codes : les phrases sont composées en JavaScript.
Rien ici ne dépend de l'heure d'exécution."""
from __future__ import annotations

from datetime import date, timedelta

import calculs as C
import commun

PAYS = ["US", "ZE", "DE", "FR", "IT", "BE", "JP", "CN", "UK"]


def _r(v, d=4):
    return None if v is None else commun.arrondir(v, d)


# ------------------------------------------------------------------ séries de travail
class Series:
    """Accès aux séries : native du jour si disponible, sinon reconstituée depuis data/."""

    def __init__(self, cfg, col, hist, rec):
        self.cfg, self.col, self.hist, self.rec = cfg, col, hist, rec

    def native(self, ident) -> dict[str, float]:
        if ident in self.col.natives and not self.cfg.indicateurs[ident].get("auxiliaire"):
            return self.col.natives[ident]
        freq = self.cfg.indicateurs[ident]["frequence"]
        if freq in ("J", "S") and self.rec.get(ident):
            return self.rec[ident]
        return self.hist.get(ident) or self.col.natives.get(ident) or {}

    def mensuelle(self, ident) -> dict[str, float]:
        """Historique mensuel (mois complets) + dernière valeur du mois en cours (provisoire)."""
        h = dict(self.hist.get(ident) or {})
        freq = self.cfg.indicateurs[ident]["frequence"]
        if freq in ("J", "S"):
            n = self.native(ident)
            if n:
                derniere = max(n)
                h[C.cle_mois(derniere)] = n[derniere]
        return dict(sorted(h.items()))


# ------------------------------------------------------------------ mini-courbes
def mini_courbe(serie: dict[str, float], freq: str) -> dict | None:
    if not serie:
        return None
    derniere = max(serie)
    if freq in ("J", "S"):
        par_semaine = {}
        for d, v in serie.items():
            j = date.fromisoformat(d)
            dimanche = j + timedelta(days=(6 - j.weekday()))
            par_semaine[dimanche.isoformat()] = v
        fin = date.fromisoformat(derniere)
        fin = fin + timedelta(days=(6 - fin.weekday()))
        cles = [(fin - timedelta(weeks=52 - i)).isoformat() for i in range(53)]
        return {"pas": "S", "duree": "1 an", "dates_fin": cles[-1], "valeurs": [_r(par_semaine.get(c)) for c in cles]}
    nombre, pas_mois, duree = {"M": (13, 1, "1 an"), "T": (13, 3, "3 ans"), "A": (11, 12, "10 ans")}[freq]
    cles = [C.ajouter_mois(derniere, -pas_mois * (nombre - 1 - i)) for i in range(nombre)]
    return {"pas": freq, "duree": duree, "dates_fin": derniere, "valeurs": [_r(serie.get(c)) for c in cles]}


# ------------------------------------------------------------------ cartes
def carte(cfg, ident, s: Series, etat: dict) -> dict | None:
    ind = cfg.indicateurs[ident]
    native = s.native(ident)
    if not native:
        return None
    freq = (etat.get("remplace") or {}).get("frequence", ind["frequence"])
    type_serie = (etat.get("remplace") or {}).get("type", ind["type"])
    derniere = max(native)
    var = C.variations_1m_1a(native, type_serie, freq)
    reg = cfg.reglages["percentile"]
    mensuel_complet = dict(s.hist.get(ident) or {})
    if freq in ("T", "A") or not mensuel_complet:
        mensuel_complet = mensuel_complet or native
    valeur_courante = var["1a"] if type_serie == "N" else native[derniere]
    pct = None
    if type_serie != "N" or valeur_courante is not None:
        pct = C.percentile_carte(mensuel_complet, type_serie, valeur_courante, reg["annees_max"], reg["annees_court"], reg["annees_min"])
    note = None
    if ind.get("transformation") == "glissement_annuel" and etat.get("date_source") and etat["date_source"] > derniere:
        brut = s.col.natives.get(ident)  # la série brute n'est pas conservée : on se fie à la date de la source
        note = f"ga_base_manquante:{etat['date_source'][:7]}"
    return {
        "valeur": _r(native[derniere]), "date": derniere,
        "provisoire_depuis": etat.get("provisoire_depuis"),
        "var_1m": _r(var["1m"]), "var_1a": _r(var["1a"]),
        "mini": mini_courbe(native, freq),
        "percentile": pct, "note": note,
    }


# ------------------------------------------------------------------ « ce qui a bougé »
def bouge(cfg, s: Series, col) -> dict:
    reg = cfg.reglages["mouvement"]
    candidats = []
    dates_j = [max(col.natives[i]) for i, ind in cfg.indicateurs.items()
               if ind["frequence"] == "J" and col.natives.get(i) and not ind.get("auxiliaire")]
    donnees_au = max(dates_j) if dates_j else None
    if not donnees_au:
        return {"du": None, "au": None, "calme": True, "liste": []}
    for ident, ind in cfg.indicateurs.items():
        if not ind.get("mouvement") or ind["frequence"] != "J" or ident not in col.natives:
            continue
        if ind["famille"] == "A" or ident == "J3_Q" or ident.startswith(("IC_", "E4_")):
            continue
        serie = col.rapides.get(ident) or col.natives[ident]
        if not serie or (date.fromisoformat(donnees_au) - date.fromisoformat(max(serie))).days > 7:
            continue
        score = C.score_mouvement(serie, ind["type"], reg["annees"], reg["jours"])
        if score:
            candidats.append({"id": ident, "groupe": ind.get("groupe_mouvement") or ident, **score})
    meilleurs = {}
    for c in candidats:
        g = c["groupe"]
        if g not in meilleurs or abs(c["rapport"]) > abs(meilleurs[g]["rapport"]):
            meilleurs[g] = c
    liste = sorted((c for c in meilleurs.values() if abs(c["rapport"]) > reg["seuil"]),
                   key=lambda c: -abs(c["rapport"]))[:reg["nombre"]]
    return {
        "du": C.recul(donnees_au, jours=reg["jours"]), "au": donnees_au, "calme": not liste,
        "liste": [{"id": c["id"], "variation": _r(c["variation"]), "rapport": _r(c["rapport"], 2),
                   "depuis": c["depuis"], "jusqua": c["jusqua"]} for c in liste],
    }


# ------------------------------------------------------------------ anticipations, courbe, QE/QT
def anticipations(cfg, s: Series) -> dict:
    seuil = cfg.reglages["anticipations"]["seuil_points"]
    sortie = {}
    for cle, ident in (("fed", "DC_FED"), ("bce", "DC_BCE")):
        n = s.native(ident)
        if not n:
            sortie[cle] = None
            continue
        d = max(n)
        e = n[d]
        sortie[cle] = {"ecart": _r(e, 2), "date": d, "lecture": "baisses" if e < -seuil else "hausses" if e > seuil else "stabilite"}
    return sortie


def courbe_us(s: Series) -> dict | None:
    series = {"3M": s.native("B3"), "2A": s.native("B2"), "10A": s.native("B1")}
    if not all(series.values()):
        return None
    communes = sorted(set(series["3M"]) & set(series["2A"]) & set(series["10A"]))
    if not communes:
        return None
    d = communes[-1]
    il_y_a = C.recul(d, mois=12)
    points_avant = {k: C.valeur_a_date(v, il_y_a, 7) for k, v in series.items()}
    avant = None
    if all(points_avant.values()):
        avant = {"date": max(p[0] for p in points_avant.values()), "points": {k: _r(p[1], 2) for k, p in points_avant.items()}}
    return {"date": d, "points": {k: _r(v[d], 2) for k, v in series.items()}, "il_y_a_1_an": avant}


def qe_qt(cfg, s: Series) -> dict:
    reg = cfg.reglages["qe_qt"]
    sortie = {}
    for ident in ("F1", "F2", "F3", "F4"):
        n = s.native(ident)
        if not n:
            sortie[ident] = None
            continue
        d = max(n)
        point = C.valeur_a_date(n, C.recul(d, mois=reg["mois"]), 10)
        if not point:
            sortie[ident] = {"statut": None, "date": d}
            continue
        var = C.variation("N", point[1], n[d])
        statut = "QE" if var > reg["seuil_pourcent"] else "QT" if var < -reg["seuil_pourcent"] else "stable"
        sortie[ident] = {"statut": statut, "variation_3m": _r(var, 2), "date": d, "date_reference": point[0]}
    return sortie


def recession(s: Series) -> dict | None:
    n = s.native("D14")
    if not n:
        return None
    d = max(n)
    return {"probabilite": _r(n[d], 1), "mois_ecart": d[:7], "mois_vise": C.ajouter_mois(d, 12)[:7], "origine": "fichier"}


# ------------------------------------------------------------------ signaux d'inflation
SIGNAUX = [
    ("brent_1a", "H1", "H2", "ga"),
    ("gaz", "H4", "H5", "niveau"),
    ("prix_production", "D9", "D8", "points"),
    ("gscpi", "D10", "D10", "points"),
    ("inflation_anticipee", "D5_LT", "D1", "points"),
    ("salaires", "D12", "D11", "points"),
    ("menages", None, "D4", "points"),
]


def signaux(cfg, s: Series) -> dict:
    reg = cfg.reglages["direction"]
    sortie = {}
    for zone, rang in (("ZE", 1), ("US", 2)):
        liste = []
        for cle, ze, us, mesure in SIGNAUX:
            ident = ze if zone == "ZE" else us
            res = None
            if ident and ident in cfg.indicateurs:
                m = s.mensuelle(ident) if cfg.indicateurs[ident]["frequence"] in ("J", "S") else s.native(ident)
                if mesure == "ga":
                    res = C.direction(C.glissement_annuel(m), "T", reg["part_ecart_type"], reg["mois"])
                elif mesure == "niveau":
                    res = C.direction(m, "N", reg["part_ecart_type"], reg["mois"])
                else:
                    res = C.direction(m, "T", reg["part_ecart_type"], reg["mois"])
            liste.append({"cle": cle, "id": ident, "fleche": res["fleche"] if res else None,
                          "variation": _r(res["variation"], 2) if res else None,
                          "seuil": _r(res["seuil"], 2) if res else None, "date": res["date"] if res else None})
        evalues = [x for x in liste if x["fleche"]]
        hausse = sum(1 for x in evalues if x["fleche"] == "▲")
        baisse = sum(1 for x in evalues if x["fleche"] == "▼")
        stable = sum(1 for x in evalues if x["fleche"] == "▶")
        synthese = "baisse" if baisse > len(evalues) / 2 else "hausse" if hausse > len(evalues) / 2 else "partage"
        sortie[zone] = {"liste": liste, "hausse": hausse, "baisse": baisse, "stable": stable,
                        "non_evalues": len(liste) - len(evalues), "synthese": synthese if evalues else None}
    return sortie


# ------------------------------------------------------------------ jauges QE
CONDITIONS = {
    "ZE": {"inflation": "C5", "peur": "J2", "stress": "J5", "dette": "BC_IT_DE", "credit": "J7", "taux": "A2"},
    "US": {"inflation": "C3", "peur": "J1", "stress": "J4", "dette": "B1", "credit": "J6", "taux": "A1"},
}


def _percentile_fenetre(mensuel: dict[str, float], t: str, valeur: float, annees_max: int, annees_min: int):
    debut = f"{int(t[:4]) - annees_max}{t[4:]}"
    fenetre = [v for d, v in mensuel.items() if debut < d <= t]
    dates = [d for d in mensuel if debut < d <= t]
    if not dates or (date.fromisoformat(t) - date.fromisoformat(min(dates))).days / 365.25 < annees_min:
        return None, None
    return C.rang_percentile(fenetre, valeur), min(dates)[:4]


def evaluer_conditions(zone: str, series_m: dict[str, dict], t: str, reg: dict, courant: dict | None = None) -> list[dict]:
    """Évalue les 6 conditions au mois t avec les seules données connues à t (pas de connaissance du futur).
    `courant` : valeurs du jour (pour la jauge actuelle) qui remplacent la valeur du mois t."""
    ids = CONDITIONS[zone]
    sortie = []

    def val(ident, mois=t):
        if courant and mois == t and ident in courant:
            return courant[ident]
        return series_m.get(ident, {}).get(mois)

    # 1. inflation sous 2 % ou en net recul
    ident = ids["inflation"]
    v, v3 = val(ident), series_m.get(ident, {}).get(C.ajouter_mois(t, -3))
    if v is None:
        sortie.append({"n": 1, "ok": None, "id": ident})
    else:
        recul = v - v3 if v3 is not None else None
        ok = v < reg["inflation_cible"] or (recul is not None and recul <= reg["recul_3m"])
        sortie.append({"n": 1, "ok": ok, "id": ident, "valeur": _r(v, 2), "variation_3m": _r(recul, 2)})
    # 2, 3, 5. percentile > 90
    for n, cle in ((2, "peur"), (3, "stress"), (5, "credit")):
        ident = ids[cle]
        v = val(ident)
        if v is None:
            sortie.append({"n": n, "ok": None, "id": ident})
            continue
        p, depuis = _percentile_fenetre(series_m.get(ident, {}), t, v, 30, reg["annees_min"])
        sortie.append({"n": n, "ok": None if p is None else p > reg["percentile_stress"], "id": ident,
                       "valeur": _r(v, 3), "percentile": None if p is None else round(p), "depuis": depuis})
    sortie.sort(key=lambda c: c["n"])
    # 4. tensions sur la dette
    ident = ids["dette"]
    v, v1 = val(ident), series_m.get(ident, {}).get(C.ajouter_mois(t, -1))
    if v is None or v1 is None:
        sortie.insert(3, {"n": 4, "ok": None, "id": ident})
    elif zone == "ZE":
        p, depuis = _percentile_fenetre(series_m.get(ident, {}), t, v, 30, reg["annees_min"])
        ok = None if p is None else (p > reg["percentile_ecart"] and v - v1 > reg["hausse_ecart_1m"])
        sortie.insert(3, {"n": 4, "ok": ok, "id": ident, "valeur": _r(v, 2), "variation_1m": _r(v - v1, 2),
                          "percentile": None if p is None else round(p), "depuis": depuis})
    else:
        sortie.insert(3, {"n": 4, "ok": v - v1 > reg["hausse_us10_1m"], "id": ident, "valeur": _r(v, 2), "variation_1m": _r(v - v1, 2)})
    # 6. taux directeur déjà bas
    ident = ids["taux"]
    v = val(ident)
    sortie.append({"n": 6, "ok": None if v is None else v <= reg["taux_bas"], "id": ident, "valeur": _r(v, 2)})
    return sortie


def lecture_score(score: int, evaluees: int) -> str | None:
    if not evaluees:
        return None
    part = score / evaluees
    return "faible" if part < 1 / 3 - 1e-9 else "possible" if part < 2 / 3 - 1e-9 else "eleve"


def jauges(cfg, s: Series) -> dict:
    reg = cfg.reglages["jauges"]
    sortie = {}
    for zone, ids in CONDITIONS.items():
        series_m = {i: s.mensuelle(i) for i in ids.values() if i in cfg.indicateurs}
        courant = {}
        for i in ids.values():
            n = s.native(i)
            if n:
                courant[i] = n[max(n)]
        t = max((max(m) for m in series_m.values() if m), default=None)
        if not t:
            sortie[zone] = None
            continue
        conditions = evaluer_conditions(zone, series_m, t, reg, courant)
        for c in conditions:
            n = s.native(c["id"])
            c["date"] = max(n) if n else None
        evaluees = sum(1 for c in conditions if c["ok"] is not None)
        score = sum(1 for c in conditions if c["ok"])
        # Historique : chaque fin de mois avec les seules données connues à cette date
        tous = sorted({d for m in series_m.values() for d in m})
        scores, evals, debut = [], [], None
        for mois in tous:
            if mois >= C.cle_mois(t):
                break
            cs = evaluer_conditions(zone, series_m, mois, reg)
            ev = sum(1 for c in cs if c["ok"] is not None)
            if ev < reg["conditions_min_historique"]:
                if debut is None:
                    continue
                scores.append(None)
                evals.append(ev)
                continue
            debut = debut or mois
            scores.append(sum(1 for c in cs if c["ok"]))
            evals.append(ev)
        sortie[zone] = {"score": score, "evaluees": evaluees, "lecture": lecture_score(score, evaluees),
                        "conditions": conditions,
                        "historique": {"debut": debut, "scores": scores, "evaluees": evals} if debut else None}
    return sortie


# ------------------------------------------------------------------ tableau des pays
def pays(cfg, s: Series) -> dict:
    sortie = {}
    for p in PAYS:
        ligne = {}
        for cle, prefixe in (("croissance", "E1_"), ("dette", "E3_"), ("deficit", "E5_"), ("dette_trimestrielle", "E3T_")):
            ident = prefixe + p
            if ident in cfg.indicateurs:
                n = s.native(ident)
                if n:
                    d = max(n)
                    ligne[cle] = {"valeur": _r(n[d], 2), "date": d, "id": ident}
        montant = f"E4_{p}"
        if montant in cfg.indicateurs:
            n = s.native(montant)
            if n:
                d = max(n)
                entree = {"valeur": _r(n[d], 1), "date": d, "id": montant, "unite": cfg.indicateurs[montant].get("unite")}
                eur = s.native(f"E4_{p}_EUR") if f"E4_{p}_EUR" in cfg.indicateurs else None
                if eur and d in eur:
                    entree["en_euros"] = _r(eur[d], 1)
                ligne["dette_montant"] = entree
        sortie[p] = ligne
    return sortie


# ------------------------------------------------------------------ assemblage
def construire(cfg, col, hist, rec, etats, existant) -> dict:
    s = Series(cfg, col, hist, rec)
    ancien = existant.get("resume", {}).get("cartes", {})
    cartes = {}
    for ident in cfg.publies():
        etat = etats.get(ident, {})
        if etat.get("statut") == "non_disponible":
            continue
        if ident in col.natives:
            c = carte(cfg, ident, s, etat)
        else:
            c = ancien.get(ident) or carte(cfg, ident, s, etat)
        if c:
            cartes[ident] = c
    ancien_bouge = existant.get("resume", {}).get("bouge")
    if col.seules is not None and ancien_bouge:
        b = ancien_bouge  # collecte partielle (--serie) : « ce qui a bougé » exige toutes les séries du jour
    else:
        b = bouge(cfg, s, col)
    return {
        "donnees_au": b["au"],
        "cartes": cartes,
        "bouge": b,
        "anticipations": anticipations(cfg, s),
        "courbe_us": courbe_us(s),
        "qe_qt": qe_qt(cfg, s),
        "recession": recession(s),
        "signaux": signaux(cfg, s),
        "jauges": jauges(cfg, s),
        "pays": pays(cfg, s),
    }
