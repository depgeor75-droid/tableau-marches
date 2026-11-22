"""BCE — portail de données (data-api.ecb.europa.eu), format CSV « csvdata », sans clé.

Interface : telecharger(demandes) -> {cle: série | ErreurSource}.

Une demande : {"cle": "B5_2A", "code": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y", …options}
  code          « FLUX/CLE » (clé SDMX complète, autant de champs que de dimensions du jeu,
                sinon la BCE répond par une page HTML et le code 400).
  debut         « AAAA-MM-JJ » facultatif : startPeriod = année de début, puis coupure exacte.
  escalier      true (A2) : la source ne donne que les dates de changement ; renvoie la série
                des jours ouvrables (lundi-vendredi) du premier changement à AUJOURD'HUI inclus
                (date d'exécution, heure belge), avec le dernier taux en vigueur. Un changement
                annoncé pour une date future est ignoré (PLAN §7.3).
  jour_semaine  jour daté pour les séries hebdomadaires « AAAA-Wss » (1 = lundi … 5 = vendredi) ;
                défaut 5 pour le jeu ILM (bilan de l'Eurosystème, arrêté le vendredi), 1 sinon.

Regroupement : les demandes d'un même jeu dont les clés ne diffèrent que par une dimension
partent en un seul appel (ex. EXR « D.CHF+CNY+GBP+JPY+USD.EUR.SP00.A ») ; un échec d'appel
met en erreur chacune de ses séries, jamais les autres. Les demandes `escalier` partent seules
(historique complet nécessaire).

Jeu particulier : telecharger_spf() → dict `spf_bce` (PLAN §6.5), ErreurSource si le contrôle
de somme (99 à 101) échoue.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from commun import ErreurSource, maintenant_belge, nettoyer, telecharger as http
from sources.sdmx import annee_debut, lignes_csv, lire_csv_series, normaliser_periode, traiter_demandes

URL = "https://data-api.ecb.europa.eu/service/data/{flux}/{cle}"
ATTENTE = 4.0
NOM = "BCE"


def _jour_semaine(demande: dict) -> int:
    flux = str(demande.get("code", "")).split("/")[0]
    return int(demande.get("jour_semaine") or (5 if flux == "ILM" else 1))


def _options(demande: dict) -> tuple:
    # Une demande en escalier part seule (clé unique dans le groupe) et sans startPeriod.
    return (_jour_semaine(demande), demande["cle"] if demande.get("escalier") else None)


def _appel(flux: str, cle: str, debut: str | None, options: tuple) -> dict[str, dict[str, float]]:
    jour, escalier = options
    params = {"format": "csvdata"}
    if debut and not escalier:
        params["startPeriod"] = annee_debut(debut)
    reponse = http(URL.format(flux=flux, cle=cle), params=params, attente=ATTENTE)
    return lire_csv_series(reponse.text, jour_semaine=jour)


def escalier(changements: dict[str, float], aujourdhui: date) -> dict[str, float]:
    """Jours ouvrables du premier changement à `aujourdhui` inclus, avec le dernier taux en vigueur."""
    dates = sorted(d for d in changements if d <= aujourdhui.isoformat())
    if not dates:
        return {}
    sortie: dict[str, float] = {}
    jour = date.fromisoformat(dates[0])
    i, taux = 0, None
    while jour <= aujourdhui:
        iso = jour.isoformat()
        while i < len(dates) and dates[i] <= iso:
            taux = changements[dates[i]]
            i += 1
        if jour.weekday() < 5:
            sortie[iso] = taux
        jour += timedelta(days=1)
    return sortie


def telecharger(demandes: list[dict], aujourdhui: date | None = None) -> dict[str, dict[str, float] | ErreurSource]:
    jour = aujourdhui or maintenant_belge().date()

    def apres(demande: dict, serie: dict[str, float]) -> dict[str, float]:
        if demande.get("escalier"):
            serie = escalier(serie, jour)
            if not serie:
                raise ErreurSource(f"{NOM} : aucun changement de taux antérieur à aujourd'hui")
        return serie

    return traiter_demandes(demandes, NOM, _appel, _options, apres)


# ------------------------------------------------------------------ SPF (jeu spf_bce, D5)
_BORNE = r"N?\d+_\d+"


def borne(texte: str) -> float:
    """« N0_8 » → -0.8 ; « 2_2 » → 2.2."""
    signe = -1 if texte.startswith("N") else 1
    return signe * float(texte.lstrip("N").replace("_", "."))


def lire_classe(code: str) -> dict | None:
    """« F1_8T2_2 » → {code, min 1.8, max 2.2} ; « TN0_8 » → max -0.8 ; « F4_8 » → min 4.8."""
    m = re.fullmatch(rf"(?:F({_BORNE}))?(?:T({_BORNE}))?", code)
    if not m or not (m.group(1) or m.group(2)):
        return None
    return {"code": code,
            "min": borne(m.group(1)) if m.group(1) else None,
            "max": borne(m.group(2)) if m.group(2) else None}


def _arrondi(v: float | None) -> float | None:
    return None if v is None else round(v, 4)


def analyser_spf(texte: str) -> dict:
    """Construit le jeu `spf_bce` à partir d'une réponse csvdata SPF (AVG, et NUM si présent)."""
    entetes, lignes = lignes_csv(texte)
    for c in ("TIME_PERIOD", "OBS_VALUE", "FCT_BREAKDOWN", "FCT_HORIZON", "FCT_SOURCE"):
        if c not in entetes:
            raise ErreurSource("SPF : format inattendu (colonne absente)")
    obs = []
    for ligne in lignes:
        valeur = (ligne.get("OBS_VALUE") or "").strip()
        if valeur in ("", "NaN"):
            continue
        obs.append((ligne["TIME_PERIOD"], ligne["FCT_HORIZON"], ligne["FCT_BREAKDOWN"],
                    ligne["FCT_SOURCE"], float(valeur)))
    avg = [o for o in obs if o[3] == "AVG"]
    if not avg:
        raise ErreurSource("SPF : aucune probabilité moyenne dans la réponse")
    enquete = max(avg, key=lambda o: normaliser_periode(o[0]) or "")[0]
    annee = int(enquete[:4])
    du_jour = [o for o in obs if o[0] == enquete]
    horizons_numeriques = sorted({int(o[1]) for o in du_jour if o[1].isdigit()})
    annee_lt = max((h for h in horizons_numeriques if h > annee + 2), default=None)
    voulus = [h for h in (str(annee), str(annee + 1), str(annee + 2), "LT")
              if any(o[1] == h for o in du_jour)]

    # Grille de classes : celles qui ont une probabilité moyenne à la dernière enquête.
    classes = {}
    for _, h, b, s, _ in du_jour:
        if s == "AVG" and h in voulus and b != "POINT":
            c = lire_classe(b)
            if c is None:
                raise ErreurSource(f"SPF : classe illisible ({b})")
            classes[b] = c
    grille = sorted(classes.values(), key=lambda c: -1e9 if c["min"] is None else c["min"])
    if not grille:
        raise ErreurSource("SPF : aucune classe de probabilité")

    def valeur(h: str, b: str, s: str) -> float | None:
        for _, hh, bb, ss, v in du_jour:
            if (hh, bb, ss) == (h, b, s):
                return v
        return None

    sortie_horizons = []
    for h in voulus:
        probas = [valeur(h, c["code"], "AVG") for c in grille]
        somme = sum(p for p in probas if p is not None)
        if not 99 <= somme <= 101:
            raise ErreurSource(f"SPF {enquete} horizon {h} : somme des probabilités {somme:.1f} hors de 99-101")
        sous, proche, dessus = 0.0, 0.0, 0.0
        for c, p in zip(grille, probas):
            if p is None:
                continue
            if c["max"] is not None and c["max"] < 1.8 - 1e-9:
                sous += p
            elif c["min"] is not None and c["min"] > 2.2 + 1e-9:
                dessus += p
            elif c["min"] is not None and c["max"] is not None and c["min"] >= 1.8 - 1e-9 and c["max"] <= 2.2 + 1e-9:
                proche += p
            else:
                raise ErreurSource(f"SPF : la classe {c['code']} chevauche les seuils 1,8 / 2,2")
        nums = [valeur(h, c["code"], "NUM") for c in grille]
        nums = [n for n in nums if n is not None]
        reponses = valeur(h, "POINT", "NUM")
        sortie_horizons.append({
            "cle": h,
            "annee": annee_lt if h == "LT" else int(h),
            "probabilites": [_arrondi(p) for p in probas],
            "moyenne": _arrondi(valeur(h, "POINT", "AVG")),
            "reponses": int(reponses) if reponses is not None else None,
            "reponses_probabilites": int(max(nums)) if nums else None,
            "sous_1_8": _arrondi(sous), "proche_de_2": _arrondi(proche), "au_dessus_de_2_2": _arrondi(dessus),
        })
    return {"enquete": enquete, "classes": grille, "horizons": sortie_horizons}


def telecharger_spf(aujourdhui: date | None = None) -> dict:
    """Dernière enquête SPF (inflation IPCH) : un seul appel, toutes classes et tous horizons.

    Clé « Q.U2.HICP...Q.AVG+NUM » (7 champs) depuis l'année précédente ; la dernière enquête
    présente est retenue.
    """
    jour = aujourdhui or maintenant_belge().date()
    try:
        reponse = http(URL.format(flux="SPF", cle="Q.U2.HICP...Q.AVG+NUM"),
                       params={"format": "csvdata", "startPeriod": str(jour.year - 1)}, attente=ATTENTE)
        return analyser_spf(reponse.text)
    except ErreurSource as erreur:
        raise ErreurSource(nettoyer(f"{NOM} : {erreur}")) from None
    except (ValueError, KeyError) as erreur:
        raise ErreurSource(nettoyer(f"{NOM} SPF : réponse illisible ({type(erreur).__name__})")) from None
