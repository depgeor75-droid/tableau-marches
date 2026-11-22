"""Collecte des données du tableau de bord des marchés.

Usage :
  python scripts/collect.py                      collecte complète, écrit data/
  python scripts/collect.py --serie B4           une seule série (et ses dépendances)
  python scripts/collect.py --verifier           contrôle sans téléchargement (rapport court)
  python scripts/collect.py --alerte             code 1 si une série essentielle justifie une alerte
  python scripts/collect.py --sortie cache/essai écrit ailleurs que data/ (essais en local)
  python scripts/collect.py --couverture         écrit docs/couverture.md

Règles : aucune donnée inventée ; un trou reste un trou ; une source en panne n'efface
jamais de bonnes données ; aucune clé ni adresse d'appel dans les fichiers produits.
"""
from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "sources"))

import calculs as C  # noqa: E402
import commun  # noqa: E402
import config as configuration  # noqa: E402
import fusion  # noqa: E402
from commun import ErreurSource, RACINE, nettoyer  # noqa: E402

FICHIERS = ["taux", "inflation", "croissance", "banques", "bourses", "energie", "devises", "risques"]


# ====================================================================== téléchargement
def _module(source: str):
    nom = "fichiers" if source == "stoxx" else source
    return importlib.import_module(nom)


def _cle_demande(spec: dict) -> tuple:
    return (spec["source"], spec.get("code"), repr(sorted((spec.get("options") or {}).items())))


class Telechargements:
    """Regroupe les demandes par source, évite les doublons, appelle chaque module une fois."""

    def __init__(self, journal):
        self.journal = journal
        self.resultats: dict[tuple, object] = {}

    def lancer(self, specs: list[dict]) -> None:
        par_source: dict[str, dict[tuple, dict]] = {}
        for spec in specs:
            cle = _cle_demande(spec)
            if cle in self.resultats:
                continue
            par_source.setdefault(spec["source"], {})[cle] = spec
        ordre = ["bce", "eurostat", "fred", "boe", "bundesbank", "mof_japon", "boj", "ons", "fichiers",
                 "ocde", "bis", "fmi", "banque_mondiale", "yahoo"]
        for source in sorted(par_source, key=lambda s: ordre.index(s) if s in ordre else 99):
            demandes = []
            index = {}
            for i, (cle, spec) in enumerate(par_source[source].items()):
                cle_txt = f"d{i}"
                index[cle_txt] = cle
                demandes.append({"cle": cle_txt, "code": spec.get("code"), **(spec.get("options") or {})})
            self.journal(f"  {source} : {len(demandes)} demande(s)")
            try:
                retour = _module(source).telecharger(demandes)
            except Exception as erreur:  # une source qui plante n'arrête jamais la collecte
                message = nettoyer(f"{source} : erreur inattendue ({type(erreur).__name__} : {erreur})")
                retour = {d["cle"]: ErreurSource(message) for d in demandes}
            for cle_txt, cle in index.items():
                self.resultats[cle] = retour.get(cle_txt, ErreurSource(f"{source} : aucune réponse"))

    def obtenir(self, spec: dict):
        return self.resultats.get(_cle_demande(spec), ErreurSource("non demandé"))


def appliquer_facteur(serie: dict[str, float], facteur) -> dict[str, float]:
    if not facteur or facteur == 1:
        return serie
    return {d: v * facteur for d, v in serie.items()}


# ====================================================================== état précédent
def lire_existant(sortie: Path) -> dict:
    existant = {"historique": {}, "recent": {}, "etat": {}, "resume": {}, "previsions": {}, "catalogue": {}}
    for f in FICHIERS:
        for genre in ("historique", "recent"):
            contenu = commun.lire_js(sortie / f"{f}_{genre}.js") or {}
            for ident, s in contenu.items():
                existant[genre][ident] = dict(zip(s["dates"], s["valeurs"]))
    for nom in ("etat", "resume", "previsions", "catalogue"):
        existant[nom] = commun.lire_js(sortie / f"{nom}.js") or {}
    return existant


# ====================================================================== assemblage
class Collecte:
    def __init__(self, cfg, existant, declencheur: str, aujourd_hui: date, journal, seules: set[str] | None):
        self.cfg = cfg
        self.existant = existant
        self.declencheur = declencheur
        self.aujourd_hui = aujourd_hui
        self.journal = journal
        self.seules = seules
        self.reg = cfg.reglages
        self.natives: dict[str, dict[str, float]] = {}       # séries obtenues aujourd'hui (fréquence native)
        self.etats: dict[str, dict] = {}
        self.rapides: dict[str, dict[str, float]] = {}       # source rapide seule (pour « ce qui a bougé »)
        self.anomalies: list[tuple[str, str]] = []
        self.weo = None

    # ------------------------------------------------------------ demandes
    def specs(self) -> list[dict]:
        specs = []
        for ident, ind in self.cfg.indicateurs.items():
            if not self._a_traiter(ident) or ind["source"] in ("calcul", "aucune"):
                if ind["source"] == "calcul" and self._a_traiter(ident):
                    for bloc in ("avant",):
                        if ind.get(bloc):
                            specs.append(ind[bloc])
                continue
            if ind["source"] == "fmi" and str(ind.get("code", "")).startswith("WEO/"):
                continue  # via le jeu WEO (un appel par indicateur, une fois par semaine)
            specs.append(ind)
            for bloc in ("avant", "avant_mensuel", "rapide"):
                if ind.get(bloc):
                    specs.append(ind[bloc])
        return specs

    def _a_traiter(self, ident: str) -> bool:
        return self.seules is None or ident in self.seules

    # ------------------------------------------------------------ cadence (jeux lents)
    def cadence_ok(self, nom: str, jours: int) -> bool:
        if self.seules is not None:
            return True
        dernier = (self.existant["etat"].get("sources", {}).get(nom, {}) or {}).get("dernier_appel")
        if not dernier:
            return True
        return (self.aujourd_hui - date.fromisoformat(dernier)).days >= jours

    # ------------------------------------------------------------ séries téléchargées
    def assembler(self, tele: Telechargements) -> None:
        secours_a_demander = []
        for ident, ind in self.cfg.indicateurs.items():
            if not self._a_traiter(ident) or ind["source"] in ("calcul", "aucune"):
                continue
            if ind["source"] == "fmi" and str(ind.get("code", "")).startswith("WEO/"):
                self._depuis_weo(ident, ind)
                continue
            brut = tele.obtenir(ind)
            if isinstance(brut, ErreurSource):
                self.etats[ident] = {"erreur": str(brut)}
                if ind.get("secours"):
                    secours_a_demander.append(ind["secours"])
                continue
            serie = appliquer_facteur(brut, ind.get("facteur"))
            serie = C.filtrer_depuis(serie, ind.get("debut", "1990-01-01"))
            info = {"source": self._libelle_source(ind), "role": "principale", "message": ""}
            if ind.get("avant"):
                serie, msg = self._prefixer(ind, serie, tele.obtenir(ind["avant"]), ind["avant"])
                if msg:
                    info["message"] = msg
            if ind.get("rapide"):
                rapide = tele.obtenir(ind["rapide"])
                if isinstance(rapide, ErreurSource):
                    info["message"] = "jours récents indisponibles (source rapide en échec)"
                else:
                    self.rapides[ident] = rapide
                    r = self.reg["raccord"]
                    serie, provisoires, raccord = fusion.raccorder(ind["type"], serie, rapide, r["N_pourcent"], r["T_points"])
                    info["raccord"] = raccord
                    if raccord and raccord.get("alerte"):
                        info["message"] = raccord["alerte"]
                        self.anomalies.append(("ATTENTION", f"{ident} : {raccord['alerte']}"))
                    if provisoires:
                        info["role"] = "principale+rapide"
                        info["provisoire_depuis"] = provisoires[0]
                        info["source"] += " + " + self.cfg.sources[ind["rapide"]["source"]]["libelle"]
                        info["message"] = f"{len(provisoires)} jour(s) récent(s) provisoire(s)"
            info["date_source"] = max(serie) if serie else None
            if ind["transformation"] == "glissement_annuel":
                serie = C.glissement_annuel(serie)
            if ind.get("avant_mensuel"):
                avant = tele.obtenir(ind["avant_mensuel"])
                if not isinstance(avant, ErreurSource):
                    info["avant_mensuel"] = {d: v for d, v in avant.items() if d <= ind["avant_mensuel"]["jusqua"]}
            self.natives[ident] = serie
            self.etats[ident] = info
        # Secours (deuxième passage, seulement pour les séries en échec)
        if secours_a_demander:
            self.journal("  secours :")
            tele.lancer(secours_a_demander)
            for ident, ind in self.cfg.indicateurs.items():
                if ident in self.etats and "erreur" in self.etats[ident] and ind.get("secours"):
                    self._appliquer_secours(ident, ind, tele.obtenir(ind["secours"]))

    def _libelle_source(self, ind: dict) -> str:
        source = ind.get("mention_source") or ind["source"]
        libelle = self.cfg.sources[source]["libelle"]
        if ind.get("organisme") and source in ("fred", "fichiers"):
            return f"{ind['organisme']} via FRED" if source == "fred" else ind["organisme"]
        return libelle

    def _prefixer(self, ind, serie, avant, spec):
        if isinstance(avant, ErreurSource):
            return serie, f"historique ancien indisponible ({spec['source']})"
        coupure = spec["jusqua"]
        prefixe = {d: v for d, v in avant.items() if d <= coupure and d >= ind.get("debut", "1990-01-01")}
        suite = {d: v for d, v in serie.items() if d > coupure}
        if prefixe and suite:
            premier = min(suite)
            dernier_avant = max(prefixe)
            ecart = fusion.ecart_raccord(ind["type"], prefixe[dernier_avant], suite[premier])
            msg = f"raccord à date fixe le {premier} (écart {ecart:.2f} {'%' if ind['type'] == 'N' else 'pt'})"
        else:
            msg = ""
        return dict(sorted({**prefixe, **suite}.items())), msg

    def _appliquer_secours(self, ident, ind, brut):
        sec = ind["secours"]
        if isinstance(brut, ErreurSource):
            self.etats[ident]["erreur"] += f" ; secours en échec : {brut}"
            return
        serie = appliquer_facteur(brut, sec.get("facteur", ind.get("facteur") if sec["source"] == ind["source"] else None))
        if ind["transformation"] == "glissement_annuel" and sec.get("source") == ind["source"]:
            serie = C.glissement_annuel(serie)
        ancien = self._ancienne_native(ident)
        echecs = (self.existant["etat"].get("series", {}).get(ident, {}) or {}).get("echecs", 0)
        if sec.get("mode", "prolonge") == "prolonge":
            if not ancien:
                return  # rien à prolonger
            communes = sorted(set(ancien) & set(serie))
            if communes:
                d = communes[-1]
                ecart = fusion.ecart_raccord(ind["type"], ancien[d], serie[d])
                seuil = self.reg["raccord"]["N_pourcent"] if ind["type"] == "N" else self.reg["raccord"]["T_points"]
                if ecart >= seuil:
                    self.etats[ident]["erreur"] += f" ; secours refusé (écart {ecart:.2f} au {d})"
                    return
            nouveau = {**ancien, **{d: v for d, v in serie.items() if d > max(ancien)}}
            self.natives[ident] = nouveau
            self.etats[ident] = {"source": self.cfg.sources[sec["source"]]["libelle"], "role": "secours",
                                 "statut_force": "secours", "date_source": max(nouveau),
                                 "message": f"source principale en échec ; prolongée par {self.cfg.sources[sec['source']]['libelle']}"}
        else:  # remplace
            seuil = self.reg["secours"]["remplace_apres_echecs"]
            if ancien and echecs + 1 < seuil:
                return
            self.natives[ident] = C.filtrer_depuis(serie, ind.get("debut", "1990-01-01"))
            self.etats[ident] = {"source": self.cfg.sources[sec["source"]]["libelle"], "role": "secours", "statut_force": "secours",
                                 "date_source": max(serie), "remplace": {k: sec[k] for k in ("frequence", "unite", "note", "type") if k in sec},
                                 "message": f"série remplacée par la source de secours : {sec.get('note', '')}".strip(" :")}

    def _ancienne_native(self, ident) -> dict[str, float]:
        ind = self.cfg.indicateurs[ident]
        if ind["frequence"] in ("J", "S"):
            return dict(self.existant["recent"].get(ident, {}))
        return dict(self.existant["historique"].get(ident, {}))

    # ------------------------------------------------------------ FMI WEO
    def charger_weo(self) -> None:
        besoin = [i for i, ind in self.cfg.indicateurs.items()
                  if ind["source"] == "fmi" and str(ind.get("code", "")).startswith("WEO/") and self._a_traiter(i)]
        if not besoin and self.seules is not None:
            return
        if not self.cadence_ok("fmi_weo", self.cfg.sources["fmi"].get("cadence_jours", 7)):
            self.weo = "cadence"
            return
        try:
            import fmi
            pays = {"US": "USA", "ZE": "G163", "DE": "DEU", "FR": "FRA", "IT": "ITA", "BE": "BEL", "JP": "JPN", "CN": "CHN", "UK": "GBR"}
            self.weo = fmi.telecharger_weo(["PCPIPCH", "NGDP_RPCH", "GGXWDG_NGDP", "GGXCNL_NGDP", "NGDP"], pays)
            if isinstance(self.weo, ErreurSource):
                raise self.weo
        except ErreurSource as erreur:
            self.weo = erreur
        except Exception as erreur:
            self.weo = ErreurSource(nettoyer(f"FMI : erreur inattendue ({type(erreur).__name__})"))

    def _depuis_weo(self, ident, ind):
        if self.weo == "cadence" or self.weo is None:
            self.etats[ident] = {"inchange": True}
            return
        if isinstance(self.weo, ErreurSource):
            self.etats[ident] = {"erreur": str(self.weo)}
            return
        indicateur = ind["code"].split("/", 1)[1]
        code_pays = ind["options"]["pays"]
        court = {"USA": "US", "G163": "ZE", "DEU": "DE", "FRA": "FR", "ITA": "IT", "BEL": "BE", "JPN": "JP", "CHN": "CN", "GBR": "UK"}[code_pays]
        valeurs = (self.weo["valeurs"].get(indicateur) or {}).get(court) or {}
        derniere = (self.weo.get("derniere_annee_par_pays") or {}).get(court, self.weo["derniere_annee_observee"])
        serie = {f"{int(a)}-01-01": float(v) for a, v in valeurs.items()
                 if v is not None and int(a) <= derniere and int(a) >= 1990}
        if not serie:
            self.etats[ident] = {"erreur": f"FMI : pas de données pour {court}"}
            return
        self.natives[ident] = dict(sorted(serie.items()))
        self.etats[ident] = {"source": f"FMI, Perspectives de l'économie mondiale ({self.weo['edition']})", "role": "principale",
                             "date_source": max(serie), "message": ""}

    # ------------------------------------------------------------ séries calculées
    def calculer(self) -> None:
        for ident in self.cfg.ordre_calcul:
            if not self._a_traiter(ident):
                continue
            ind = self.cfg.indicateurs[ident]
            entrees = ind.get("entrees", [])
            manquantes = [e for e in entrees if e not in self.natives]
            if manquantes:
                etats_entrees = [self.etats.get(e, {}) for e in manquantes]
                if all(e.get("inchange") for e in etats_entrees):
                    self.etats[ident] = {"inchange": True}
                else:
                    self.etats[ident] = {"erreur": "entrée indisponible aujourd'hui : " + ", ".join(manquantes), "calcule": True}
                continue
            s = [self.natives[e] for e in entrees]
            t = ind["transformation"]
            if t == "ecart":
                serie = C.ecart(s[0], s[1])
            elif t == "croise":
                serie = C.croise(s[0], s[1])
            elif t == "produit":
                serie = C.produit(s[0], s[1], ind.get("facteur", 1))
            elif t == "pourcentage_pib":
                serie = pourcentage_pib(s[0], s[1], self.cfg.indicateurs[entrees[1]].get("agregat_4t", "somme"))
            elif t == "en_euros":
                serie = en_euros(s[0], s[1], ind["frequence"])
            else:
                raise configuration.ErreurConfig(f"{ident} : transformation {t} non calculable")
            info = {"source": "Calcul (" + ", ".join(self.cfg.indicateurs[e]["nom_court"] for e in entrees) + ")",
                    "role": "principale", "message": "", "calcule": True}
            if ind.get("avant"):
                serie, msg = self._prefixer(ind, serie, self._tele.obtenir(ind["avant"]), ind["avant"])
                info["message"] = msg
            if not serie:
                self.etats[ident] = {"erreur": "calcul vide (aucune date commune)", "calcule": True}
                continue
            info["date_source"] = max(serie)
            if any(self.etats.get(e, {}).get("statut_force") == "secours" for e in entrees):
                info["statut_force"] = "secours"
            self.natives[ident] = serie
            self.etats[ident] = info


def pourcentage_pib(bilan: dict[str, float], pib: dict[str, float], agregat: str) -> dict[str, float]:
    """Bilan (dernière observation du trimestre) ÷ PIB des 4 derniers trimestres × 100.
    agregat = « moyenne » (PIB annualisé) ou « somme » (PIB trimestriel). Aucun report d'un PIB ancien."""
    fin_trimestre: dict[str, float] = {}
    for d, v in bilan.items():
        cle = f"{d[:4]}-{((int(d[5:7]) - 1) // 3) * 3 + 1:02d}-01"
        fin_trimestre[cle] = v
    sortie = {}
    for q in fin_trimestre:
        trimestres = [C.ajouter_mois(q, -3 * k) for k in range(4)]
        if all(t in pib for t in trimestres):
            total = sum(pib[t] for t in trimestres)
            base = total / 4 if agregat == "moyenne" else total
            if base:
                sortie[q] = fin_trimestre[q] / base * 100
    # le dernier trimestre du bilan n'est pas complet : il n'est gardé que si le PIB du trimestre existe
    return sortie


def en_euros(montant: dict[str, float], devise_par_euro: dict[str, float], frequence: str) -> dict[str, float]:
    """Montant en devise ÷ cours (devise pour 1 €) du dernier jour de la période."""
    from datetime import timedelta
    sortie = {}
    mois = 3 if frequence == "T" else 12
    for d, v in montant.items():
        fin = (date.fromisoformat(C.ajouter_mois(d, mois)) - timedelta(days=1)).isoformat()
        point = C.valeur_a_date(devise_par_euro, fin, 10)  # dernier cours de la période (10 jours au plus avant la fin)
        if point and point[1]:
            sortie[d] = v / point[1]
    return sortie


# ====================================================================== point d'entrée
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Collecte du tableau de bord des marchés")
    p.add_argument("--serie", action="append")
    p.add_argument("--verifier", action="store_true")
    p.add_argument("--alerte", action="store_true")
    p.add_argument("--declencheur", default="local")
    p.add_argument("--sortie", default="data")
    p.add_argument("--forcer", action="append", default=[])
    p.add_argument("--couverture", action="store_true")
    args = p.parse_args(argv)

    commun.charger_env()
    cfg = configuration.charger()
    sortie = (RACINE / args.sortie).resolve()
    import verifier
    if args.verifier:
        return verifier.rapport(cfg, sortie)
    if args.alerte:
        return verifier.alerte(cfg, sortie)
    if args.couverture:
        return verifier.couverture(cfg, sortie)

    import ecriture
    aujourd_hui = commun.maintenant_belge().date()
    journal = lambda m: print(m, flush=True)  # noqa: E731
    seules = None
    if args.serie:
        seules = set()
        for ident in args.serie:
            _avec_dependances(cfg, ident, seules)
    existant = lire_existant(sortie)
    if sortie != (RACINE / "data").resolve() and not existant["etat"]:
        existant = lire_existant(RACINE / "data")  # essai : partir des données publiées
    journal(f"Collecte du {aujourd_hui.isoformat()} ({args.declencheur}) → {sortie.relative_to(RACINE)}")
    col = Collecte(cfg, existant, args.declencheur, aujourd_hui, journal, seules)
    tele = Telechargements(journal)
    col._tele = tele
    tele.lancer(col.specs())
    col.charger_weo()
    col.assembler(tele)
    col.calculer()
    import previsions
    jeux = previsions.collecter(cfg, col, existant) if seules is None else None
    resultat = ecriture.ecrire(cfg, col, existant, sortie, args.declencheur, jeux, set(args.forcer))
    journal(resultat)
    return 0


def _avec_dependances(cfg, ident, ensemble):
    if ident not in cfg.indicateurs:
        raise SystemExit(f"Série inconnue : {ident}")
    ensemble.add(ident)
    for e in cfg.indicateurs[ident].get("entrees", []) or []:
        _avec_dependances(cfg, e, ensemble)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:  # message toujours nettoyé (aucune clé dans la sortie du workflow)
        print("Erreur inattendue : " + nettoyer(f"{type(erreur).__name__} : {erreur}"), file=sys.stderr)
        print(nettoyer(traceback.format_exc()), file=sys.stderr)
        sys.exit(2)
