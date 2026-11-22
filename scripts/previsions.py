"""Jeux particuliers (data/previsions.js) : distributions SPF (BCE, Fed de Philadelphie),
prévisions du FMI, courbe à terme du pétrole (PLAN §6.5). Non sélectionnables dans le comparateur."""
from __future__ import annotations

from datetime import date

import fusion
from commun import ErreurSource, nettoyer

PAYS = {"US": "USA", "ZE": "G163", "DE": "DEU", "FR": "FRA", "IT": "ITA", "BE": "BEL", "JP": "JPN", "CN": "CHN", "UK": "GBR"}


def _appel(fonction, *args, **kwargs):
    try:
        resultat = fonction(*args, **kwargs)
        if isinstance(resultat, ErreurSource):
            return resultat
        return resultat
    except ErreurSource as erreur:
        return erreur
    except Exception as erreur:  # jamais d'arrêt de la collecte
        return ErreurSource(nettoyer(f"erreur inattendue ({type(erreur).__name__} : {erreur})"))


def _fmi_depuis_weo(weo: dict) -> dict:
    derniere = weo["derniere_annee_observee"]
    annees = [derniere, derniere + 1, derniere + 2, derniere + 3]
    sortie = {"edition": weo["edition"], "derniere_annee_observee": derniere, "annees": annees, "pays": list(PAYS)}
    for cle, indicateur in (("inflation", "PCPIPCH"), ("croissance", "NGDP_RPCH"), ("dette", "GGXWDG_NGDP"), ("solde", "GGXCNL_NGDP")):
        valeurs = weo["valeurs"].get(indicateur, {})
        sortie[cle] = {p: [(None if valeurs.get(p, {}).get(a, valeurs.get(p, {}).get(str(a))) is None
                            else round(float(valeurs[p].get(a, valeurs[p].get(str(a)))), 2)) for a in annees] for p in PAYS}
    if weo.get("publiee_le"):
        sortie["publiee_le"] = weo["publiee_le"]
    return sortie


def collecter(cfg, col, existant) -> tuple[dict, dict]:
    ancien = existant.get("previsions", {}) or {}
    ancien_etat = existant.get("etat", {}).get("jeux", {})
    aujourd_hui = col.aujourd_hui
    prev, etats = {}, {}

    def enregistrer(nom, resultat, date_obs=None, appel=True):
        precedent = ancien_etat.get(nom, {})
        jeu = cfg.jeux[nom]
        if isinstance(resultat, ErreurSource):
            if ancien.get(nom):
                prev[nom] = ancien[nom]
            echecs = precedent.get("echecs", 0) + (1 if col.declencheur == "schedule" else 0)
            etats[nom] = {"statut": "erreur", "echecs": echecs, "message": str(resultat), "date": precedent.get("date")}
            return
        prev[nom] = resultat
        statut = "ok"
        message = ""
        if date_obs and jeu.get("retard_max_jours"):
            retard, detail = fusion.est_en_retard(date_obs, "J", aujourd_hui, None, jeu["retard_max_jours"])
            if retard:
                statut, message = "en_retard", "dernière enquête ou édition ancienne : " + detail
        etats[nom] = {"statut": statut, "echecs": 0, "message": message, "date": date_obs, "appel_du_jour": appel}

    def cadence(nom):
        return col.cadence_ok(f"jeu_{nom}", cfg.jeux[nom].get("cadence_jours", 1))

    def garder(nom):
        if ancien.get(nom):
            prev[nom] = ancien[nom]
        etats[nom] = {**ancien_etat.get(nom, {"statut": "ok", "echecs": 0, "message": ""})}

    # SPF de la BCE
    if cadence("spf_bce"):
        import bce
        r = _appel(bce.telecharger_spf)
        enregistrer("spf_bce", r, _date_enquete(r) if not isinstance(r, ErreurSource) else None)
    else:
        garder("spf_bce")
    # SPF de la Fed de Philadelphie
    if cadence("spf_us"):
        import fichiers
        r = _appel(fichiers.telecharger_spf_us)
        enregistrer("spf_us", r, _date_enquete(r) if not isinstance(r, ErreurSource) else None)
    else:
        garder("spf_us")
    # FMI (le WEO a déjà été téléchargé par la collecte, une fois par semaine)
    if col.weo == "cadence" or col.weo is None:
        garder("fmi")
    elif isinstance(col.weo, ErreurSource):
        enregistrer("fmi", col.weo)
    else:
        r = _appel(_fmi_depuis_weo, col.weo)
        enregistrer("fmi", r, (col.weo.get("publiee_le") or col.weo["edition"] + "-01") if not isinstance(r, ErreurSource) else None)
    # Courbe à terme du pétrole
    import yahoo
    r = _appel(yahoo.telecharger_courbe_petrole, aujourd_hui)
    enregistrer("courbe_petrole", r, r.get("date") if isinstance(r, dict) else None)
    return prev, etats


def _date_enquete(jeu: dict) -> str | None:
    """« 2026-Q4 » → premier jour du trimestre de l'enquête."""
    e = jeu.get("enquete") if isinstance(jeu, dict) else None
    if not e:
        return None
    if "-Q" in e:
        annee, q = e.split("-Q")
        return f"{annee}-{(int(q) - 1) * 3 + 1:02d}-01"
    return e[:10]
