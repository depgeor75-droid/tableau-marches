"""Contrôles : rapport court (--verifier), règle d'alerte (--alerte), couverture (--couverture)."""
from __future__ import annotations

from statistics import pstdev

import commun

GRAVITE = {"ALERTE": 0, "ATTENTION": 1, "INFO": 2}


def motifs_alerte(cfg, etat: dict) -> dict:
    """Alerte si une série (ou un jeu) essentielle, non calculée, est en erreur depuis 3 exécutions
    planifiées de suite, ou en retard. « non_disponible » et « secours » n'alertent jamais."""
    seuil = cfg.reglages["alerte"]["echecs_planifies"]
    motifs = []
    for ident, e in etat.get("series", {}).items():
        ind = cfg.indicateurs.get(ident)
        if not ind or ind.get("priorite") != "E" or e.get("calcule") or ind["source"] == "calcul":
            continue
        if e["statut"] == "erreur" and e.get("echecs", 0) >= seuil:
            motifs.append(f"{ident} ({ind['nom_court']}) en erreur depuis {e['echecs']} exécutions planifiées")
        elif e["statut"] == "en_retard":
            motifs.append(f"{ident} ({ind['nom_court']}) en retard")
    for nom, e in etat.get("jeux", {}).items():
        if cfg.jeux.get(nom, {}).get("priorite") == "E":
            if e.get("statut") == "erreur" and e.get("echecs", 0) >= seuil:
                motifs.append(f"jeu {nom} en erreur depuis {e['echecs']} exécutions planifiées")
            elif e.get("statut") == "en_retard":
                motifs.append(f"jeu {nom} en retard")
    return {"declenchee": bool(motifs), "motifs": motifs}


def _lire(sortie):
    etat = commun.lire_js(sortie / "etat.js")
    if not etat:
        raise SystemExit("Aucun fichier etat.js : lancez d'abord la collecte.")
    return etat


def _controles_series(cfg, sortie) -> list[tuple[str, str]]:
    """Dates triées et uniques ; sauts anormaux (signalés, jamais supprimés)."""
    anomalies = []
    k = cfg.reglages["saut_anormal"]["ecarts_types"]
    for f in ("taux", "inflation", "croissance", "banques", "bourses", "energie", "devises", "risques"):
        for genre in ("historique",):  # les séries en escalier (taux directeurs) font de faux sauts au quotidien
            contenu = commun.lire_js(sortie / f"{f}_{genre}.js") or {}
            for ident, s in contenu.items():
                dates = s["dates"]
                if dates != sorted(set(dates)):
                    anomalies.append(("ALERTE", f"{ident} ({genre}) : dates non triées ou en double"))
                v = s["valeurs"]
                if len(v) > 60:
                    diffs = [b - a for a, b in zip(v, v[1:])]
                    et = pstdev(diffs)
                    if et:
                        for i, d in enumerate(diffs):
                            if abs(d) > k * et:
                                anomalies.append(("INFO", f"{ident} ({genre}) : saut anormal le {dates[i + 1]} (vérifier)"))
                                break
    return anomalies


def rapport(cfg, sortie) -> int:
    etat = _lire(sortie)
    series = etat["series"]
    comptes = etat.get("comptes", {})
    lignes = ["Contrôle des données — " + etat.get("genere_le", "?") + " (UTC)",
              "Statuts : " + " · ".join(f"{k} {v}" for k, v in sorted(comptes.items()))]
    anomalies = []
    for ident, e in series.items():
        ind = cfg.indicateurs.get(ident, {})
        essentielle = ind.get("priorite") == "E"
        if e["statut"] == "erreur":
            anomalies.append(("ALERTE" if essentielle else "ATTENTION", f"{ident} en erreur : {e.get('message', '')}"))
        elif e["statut"] == "en_retard":
            anomalies.append(("ALERTE" if essentielle else "ATTENTION", f"{ident} en retard ({e.get('date_source')})"))
        elif e["statut"] == "secours":
            anomalies.append(("ATTENTION", f"{ident} sur source de secours"))
    for nom, e in etat.get("jeux", {}).items():
        if e.get("statut") not in ("ok", None):
            anomalies.append(("ATTENTION", f"jeu {nom} : {e.get('statut')} {e.get('message', '')}"))
    anomalies += [(a["gravite"], a["texte"]) for a in etat.get("anomalies", [])]
    anomalies += _controles_series(cfg, sortie)
    anomalies.sort(key=lambda a: GRAVITE.get(a[0], 3))
    for gravite, texte in anomalies[:27]:
        lignes.append(f"[{gravite}] {texte}"[:160])
    if len(anomalies) > 27:
        lignes.append(f"… et {len(anomalies) - 27} autre(s) anomalie(s)")
    print("\n".join(lignes))
    essentielle_en_erreur = any(e["statut"] == "erreur" and cfg.indicateurs.get(i, {}).get("priorite") == "E"
                                and cfg.indicateurs.get(i, {}).get("source") != "calcul" for i, e in series.items())
    return 1 if essentielle_en_erreur else 0


def alerte(cfg, sortie) -> int:
    etat = _lire(sortie)
    motifs = motifs_alerte(cfg, etat)
    if motifs["declenchee"]:
        print("ALERTE — séries essentielles à vérifier :")
        for m in motifs["motifs"]:
            print(" - " + m)
        return 1
    print("Aucune alerte.")
    return 0


def couverture(cfg, sortie) -> int:
    etat = _lire(sortie)
    catalogue = commun.lire_js(sortie / "catalogue.js") or {"indicateurs": {}}
    lignes = ["# Couverture des données", "", f"Généré le {etat['genere_le']} (UTC).", "",
              "| id | indicateur | statut | source | début | dernière date |", "|---|---|---|---|---|---|"]
    for ident in cfg.publies():
        e = etat["series"].get(ident, {})
        c = catalogue["indicateurs"].get(ident, {})
        lignes.append(f"| {ident} | {cfg.indicateurs[ident]['nom_court']} | {e.get('statut', '?')} | "
                      f"{e.get('source') or c.get('source', '')} | {c.get('debut') or '—'} | {e.get('date') or '—'} |")
    commun.ecrire_si_change(commun.RACINE / "docs" / "couverture.md", "\n".join(lignes) + "\n")
    print("docs/couverture.md écrit.")
    return 0
