"""Écriture de data/ : séries (historique / récent), catalogue, état, résumé, prévisions, CSV.

Écriture déterministe (clés triées, arrondi fixe, UTF-8, LF) : relancer la collecte sans donnée
nouvelle ne modifie aucun fichier sauf etat.js.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import calculs as C
import commun
import fusion
from commun import nettoyer

FICHIERS = ["taux", "inflation", "croissance", "banques", "bourses", "energie", "devises", "risques"]


def _arrondir_serie(serie: dict[str, float], decimales: int) -> dict[str, float]:
    return {d: commun.arrondir(v, decimales) for d, v in sorted(serie.items())}


def _format_serie(serie: dict[str, float]) -> dict:
    dates = sorted(serie)
    return {"dates": dates, "valeurs": [serie[d] for d in dates]}


def frequence_effective(ind: dict, etat: dict | None) -> str:
    remplace = (etat or {}).get("remplace") or {}
    return remplace.get("frequence", ind["frequence"])


def historique_depuis_native(native: dict[str, float], frequence: str, aujourd_hui: date,
                             avant_mensuel: dict[str, float] | None = None) -> dict[str, float]:
    """J et S : dernière observation de chaque mois complet (datée au 1er du mois) ;
    M, T, A : valeurs telles que publiées."""
    if frequence in ("J", "S"):
        mensuel = C.mois_complets(C.mensualiser(native, "fin"), aujourd_hui)
        if avant_mensuel:
            debut_natif = min(native) if native else "9999"
            prefixe = {C.cle_mois(d): v for d, v in avant_mensuel.items() if C.cle_mois(d) < C.cle_mois(debut_natif)}
            mensuel = {**prefixe, **mensuel}
        return dict(sorted(mensuel.items()))
    return dict(native)


def recent_depuis_native(native: dict[str, float], frequence: str, aujourd_hui: date, mois: int) -> dict[str, float]:
    if frequence not in ("J", "S"):
        return {}
    limite = C.recul(aujourd_hui.isoformat(), mois=mois)
    return {d: v for d, v in native.items() if d >= limite}


def mention(cfg, ind: dict, etat: dict | None = None) -> str:
    role = (etat or {}).get("role")
    source = ind.get("mention_source") or ind["source"]
    organisme = ind.get("organisme", "")
    if role == "secours" and ind.get("secours"):
        source = ind["secours"]["source"]
        organisme = ind["secours"].get("organisme", organisme)
    if source == "aucune":
        return ""
    gabarit = cfg.sources[source]["mention"]
    entrees = ", ".join(cfg.indicateurs[e]["nom_court"] for e in ind.get("entrees", []) or [])
    texte = gabarit.format(organisme=organisme or cfg.sources[source]["libelle"],
                           base="Perspectives de l'économie mondiale" if "WEO" in str(ind.get("code")) else "base de données",
                           entrees=entrees)
    if ind.get("rapide") and source != "aucune":
        texte += " Jours récents : " + cfg.sources[ind["rapide"]["source"]]["mention"].replace("Source : ", "")
    if ind.get("avant"):
        texte += f" Avant le {ind['avant']['jusqua']} : {ind['avant'].get('organisme', '')} via FRED®."
    if ind.get("mention_extra"):
        texte += " " + ind["mention_extra"]
    return texte


def ecrire(cfg, col, existant: dict, sortie, declencheur: str, jeux, forcer: set[str]) -> str:
    reg = cfg.reglages
    aujourd_hui = col.aujourd_hui
    ancien_etat = existant["etat"].get("series", {})
    historiques: dict[str, dict] = {f: {} for f in FICHIERS}
    recents: dict[str, dict] = {f: {} for f in FICHIERS}
    etats: dict[str, dict] = {}
    series_hist: dict[str, dict] = {}
    series_rec: dict[str, dict] = {}
    seuils_fraicheur = reg["fraicheur"]
    traitees = set(cfg.indicateurs) if col.seules is None else col.seules

    for ident, ind in cfg.indicateurs.items():
        if ind.get("auxiliaire"):
            continue
        fichier = cfg.fichier(ident)
        ancien_h = existant["historique"].get(ident, {})
        ancien_r = existant["recent"].get(ident, {})
        precedent = ancien_etat.get(ident, {})
        info = col.etats.get(ident, {}) if ident in traitees else {"inchange": True}
        dec = ind.get("decimales_stockage", 4)

        if ind["source"] == "aucune":
            etats[ident] = {"statut": "non_disponible", "message": ind.get("raison", ""), "echecs": 0,
                            "source": "", "role": None}
            continue

        freq = frequence_effective(ind, info if "remplace" in info else precedent)
        native = col.natives.get(ident) if ident in traitees else None
        if native is not None:
            nouveau_h = _arrondir_serie(historique_depuis_native(native, freq, aujourd_hui, info.get("avant_mensuel")), dec)
            nouveau_r = _arrondir_serie(recent_depuis_native(native, freq, aujourd_hui, reg["recent_mois"]), dec)
            if ident in forcer or info.get("remplace"):
                h, r = nouveau_h, nouveau_r
            elif info.get("role") == "secours" and freq in ("J", "S"):
                # Secours « prolonge » : la série du jour ne couvre que la fenêtre récente ;
                # on garde l'historique et on n'y ajoute que les mois nouvellement clos.
                dernier_mois = max(ancien_h) if ancien_h else ""
                h = {**ancien_h, **{d: v for d, v in nouveau_h.items() if d > dernier_mois}}
                r = nouveau_r
            else:
                h, anomalie_h = fusion.fusionner(ancien_h, nouveau_h)
                # La fenêtre « récente » glisse : on ne compare que la partie commune (pas de test de début).
                ancien_fenetre = {d: v for d, v in ancien_r.items() if nouveau_r and d >= min(nouveau_r)}
                r, anomalie_r = fusion.fusionner(ancien_fenetre, nouveau_r) if freq in ("J", "S") else ({}, None)
                for anomalie in (anomalie_h, anomalie_r):
                    if anomalie:
                        col.anomalies.append(("ATTENTION", f"{ident} : {anomalie}"))
                        info = {**info, "message": anomalie, "tronquee": True}
        else:
            h, r = ancien_h, ancien_r

        if h:
            historiques[fichier][ident] = _format_serie(h)
        if r:
            recents[fichier][ident] = _format_serie(r)
        series_hist[ident], series_rec[ident] = h, r

        # ---------------------------------------------------------------- statut
        derniere_serie = r if r else h
        derniere_date = max(derniere_serie) if derniere_serie else None
        echecs_avant = precedent.get("echecs", 0)
        if "erreur" in info:
            statut = "erreur"
            echecs = echecs_avant + 1 if declencheur == "schedule" else echecs_avant
            date_source = precedent.get("date_source") or derniere_date
            message = info["erreur"]
            source_txt, role = precedent.get("source", ""), precedent.get("role")
        elif info.get("inchange"):
            statut = precedent.get("statut", "ok") if precedent.get("statut") != "en_retard" else "ok"
            echecs = echecs_avant
            date_source = precedent.get("date_source") or derniere_date
            message = precedent.get("message", "")
            source_txt, role = precedent.get("source", ""), precedent.get("role")
        else:
            statut = info.get("statut_force", "ok")
            echecs = 0
            date_source = info.get("date_source") or derniere_date
            message = info.get("message", "")
            source_txt, role = info.get("source", ""), info.get("role")
        if not derniere_serie:
            statut = "erreur" if statut != "non_disponible" else statut
        elif statut in ("ok", "secours") and date_source:
            retard, detail = fusion.est_en_retard(date_source, freq, aujourd_hui, seuils_fraicheur, ind.get("retard_max_jours"))
            if retard:
                statut = "en_retard"
                message = (message + " ; " if message else "") + "dernière valeur ancienne : " + detail
        entree = {
            "statut": statut, "echecs": echecs, "source": source_txt, "role": role,
            "date": derniere_date, "valeur": derniere_serie[derniere_date] if derniere_date else None,
            "date_source": date_source, "message": nettoyer(message) if message else "",
        }
        for cle in ("raccord", "provisoire_depuis", "remplace"):
            valeur = info.get(cle) if cle in info else (precedent.get(cle) if info.get("inchange") else None)
            if valeur:
                entree[cle] = valeur
        if ind.get("calcule") or ind["source"] == "calcul":
            entree["calcule"] = True
        etats[ident] = entree

    # ------------------------------------------------------------- fichiers de séries
    changes = []
    for f in FICHIERS:
        if commun.ecrire_js(sortie / f"{f}_historique.js", f"{f}_historique", historiques[f]):
            changes.append(f"{f}_historique")
        if commun.ecrire_js(sortie / f"{f}_recent.js", f"{f}_recent", recents[f]):
            changes.append(f"{f}_recent")

    # ------------------------------------------------------------- catalogue
    catalogue = construire_catalogue(cfg, etats, series_hist, series_rec)
    if commun.ecrire_js(sortie / "catalogue.js", "catalogue", catalogue):
        changes.append("catalogue")

    # ------------------------------------------------------------- résumé, prévisions
    import resume as module_resume
    contenu_resume = module_resume.construire(cfg, col, series_hist, series_rec, etats, existant)
    if commun.ecrire_js(sortie / "resume.js", "resume", contenu_resume):
        changes.append("resume")
    etat_jeux = {}
    if jeux is not None:
        prev, etat_jeux = jeux
        if commun.ecrire_js(sortie / "previsions.js", "previsions", prev):
            changes.append("previsions")
    else:
        etat_jeux = existant["etat"].get("jeux", {})

    # ------------------------------------------------------------- CSV
    if ecrire_csv(cfg, series_hist, sortie / "donnees_mensuelles.csv", aujourd_hui):
        changes.append("donnees_mensuelles.csv")

    # ------------------------------------------------------------- état
    comptes = {}
    for e in etats.values():
        comptes[e["statut"]] = comptes.get(e["statut"], 0) + 1
    import verifier
    sources_appels = dict(existant["etat"].get("sources", {}))
    if col.weo not in (None, "cadence") and not hasattr(col.weo, "args"):
        sources_appels["fmi_weo"] = {"dernier_appel": aujourd_hui.isoformat(), "edition": col.weo.get("edition")}
    for nom, e in etat_jeux.items():
        if e.get("appel_du_jour"):
            sources_appels[f"jeu_{nom}"] = {"dernier_appel": aujourd_hui.isoformat()}
    etat = {
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declencheur": declencheur,
        "comptes": dict(sorted(comptes.items())),
        "series": etats,
        "jeux": {k: {kk: vv for kk, vv in v.items() if kk != "appel_du_jour"} for k, v in etat_jeux.items()},
        "sources": sources_appels,
        "anomalies": [{"gravite": g, "texte": nettoyer(t)} for g, t in col.anomalies],
    }
    etat["alerte"] = verifier.motifs_alerte(cfg, etat)
    commun.ecrire_js(sortie / "etat.js", "etat", etat)
    return (f"Terminé : {', '.join(f'{k} {v}' for k, v in sorted(comptes.items()))}. "
            f"Fichiers modifiés : {', '.join(changes) or 'aucun'} (+ etat.js).")


def construire_catalogue(cfg, etats, series_hist, series_rec) -> dict:
    indicateurs = {}
    for ident in cfg.publies():
        ind = cfg.indicateurs[ident]
        etat = etats.get(ident, {})
        remplace = etat.get("remplace") or {}
        serie = series_hist.get(ident) or series_rec.get(ident) or {}
        debut = min(serie) if serie else None
        if series_rec.get(ident) and series_hist.get(ident):
            debut = min(min(series_hist[ident]), min(series_rec[ident]))
        indicateurs[ident] = {
            "nom": ind["nom"], "nom_court": ind["nom_court"], "famille": ind["famille"], "fichier": cfg.fichier(ident),
            "type": remplace.get("type", ind["type"]), "unite": remplace.get("unite", ind.get("unite", "")),
            "pays": ind.get("pays"), "frequence": remplace.get("frequence", ind["frequence"]),
            "decimales": ind.get("decimales", 2), "priorite": ind.get("priorite", "S"),
            "source": etat.get("source") or cfg.sources.get(ind["source"], {}).get("libelle", ""),
            "mention": mention(cfg, ind, etat), "lien_source": cfg.sources.get(ind.get("mention_source") or ind["source"], {}).get("lien"),
            "debut": debut, "fiche": ind.get("fiche", ident), "calcule": ind["source"] == "calcul",
            "zone_horaire": ind.get("zone_horaire"), "particularite": remplace.get("note"),
            "raison": ind.get("raison"), "transformation": ind.get("transformation", "aucune"),
            "entrees": ind.get("entrees"),
        }
    familles = [{"id": k, "nom": v["nom"], "page": v["page"], "fichier": v["fichier"]} for k, v in cfg.familles.items()]
    jeux = {k: {"nom": v["nom"], "fiche": v.get("fiche"),
                "mention": cfg.sources[v["source"]]["mention"].format(organisme=v.get("organisme", cfg.sources[v["source"]]["libelle"]),
                                                                       base="Perspectives de l'économie mondiale", entrees="")}
            for k, v in cfg.jeux.items()}
    reg = cfg.reglages
    return {
        "familles": familles, "indicateurs": indicateurs, "ordre": cfg.publies(), "jeux": jeux, "accueil": cfg.accueil,
        "comparaisons": cfg.comparaisons,
        "evenements": [{**e, "date": str(e["date"])} for e in cfg.evenements],
        "reglages": {"comparateur": reg["comparateur"], "graphiques": reg["graphiques"], "percentile": reg["percentile"],
                     "anticipations": reg["anticipations"], "recent_mois": reg["recent_mois"], "jauges": reg["jauges"]},
        "sources": {k: {"libelle": v["libelle"], "mention": v["mention"], "lien": v.get("lien")} for k, v in cfg.sources.items()},
    }


def ecrire_csv(cfg, series_hist: dict[str, dict], chemin, aujourd_hui=None) -> bool:
    """Toutes les séries en mensuel (mois complets), séparateur « ; », virgule décimale, utf-8-sig."""
    colonnes = [i for i in cfg.publies() if series_hist.get(i)]
    par_mois: dict[str, dict[str, float]] = {}
    for ident in colonnes:
        freq = cfg.indicateurs[ident]["frequence"]
        for d, v in series_hist[ident].items():
            if freq == "T":
                d = C.ajouter_mois(d, 2)
            elif freq == "A":
                d = d[:4] + "-12-01"
            if aujourd_hui and d[:7] >= aujourd_hui.isoformat()[:7]:
                continue  # mois non terminé
            par_mois.setdefault(d[:7], {})[ident] = v
    entete = ["Mois"] + [f"{cfg.indicateurs[i]['nom_court']} ({cfg.indicateurs[i].get('unite', '')}) [{i}]" for i in colonnes]
    lignes = [";".join(entete)]
    for mois in sorted(par_mois):
        valeurs = par_mois[mois]
        lignes.append(";".join([mois] + [("" if i not in valeurs else repr(valeurs[i]).replace(".", ",")) for i in colonnes]))
    contenu = "﻿" + "\n".join(lignes) + "\n"
    return commun.ecrire_si_change(chemin, contenu)
