"""Lecture et validation de la configuration (config/*.yaml)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from commun import DOSSIER_CONFIG

CHAMPS_OBLIGATOIRES = ("id", "nom", "nom_court", "famille", "type", "frequence", "source")
TYPES = {"T", "N", "N*"}
FREQUENCES = {"J", "S", "M", "T", "A"}
TRANSFORMATIONS = {"aucune", "glissement_annuel", "ecart", "croise", "pourcentage_pib", "produit", "en_euros"}


class ErreurConfig(Exception):
    pass


@dataclass
class Config:
    indicateurs: dict[str, dict]
    familles: dict[str, dict]
    accueil: list[str]
    jeux: dict[str, dict]
    reglages: dict
    sources: dict[str, dict]
    comparaisons: list[dict]
    evenements: list[dict]
    ordre_calcul: list[str] = field(default_factory=list)

    def publies(self) -> list[str]:
        """Séries visibles (ni auxiliaires), dans l'ordre du fichier."""
        return [i for i, ind in self.indicateurs.items() if not ind.get("auxiliaire")]

    def fichier(self, ident: str) -> str:
        return self.familles[self.indicateurs[ident]["famille"]]["fichier"]


def _lire(nom: str):
    with open(DOSSIER_CONFIG / nom, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def charger() -> Config:
    brut = _lire("indicateurs.yaml")
    defauts = brut.get("defauts", {})
    familles = brut["familles"]
    indicateurs: dict[str, dict] = {}
    for entree in brut["indicateurs"]:
        famille = familles.get(entree.get("famille"))
        if famille is None:
            raise ErreurConfig(f"famille inconnue pour {entree.get('id')}")
        ind = {**defauts, **famille.get("defauts", {}), **entree}
        ind.setdefault("fiche", ind["id"])
        ind.setdefault("options", {})
        ind["mouvement"] = ind.get("mouvement") in (True, "oui")
        for champ in CHAMPS_OBLIGATOIRES:
            if champ not in ind:
                raise ErreurConfig(f"{ind.get('id')} : champ « {champ} » manquant")
        if not re.fullmatch(r"[A-Za-z0-9_]+", ind["id"]):
            raise ErreurConfig(f"identifiant invalide : {ind['id']}")
        if ind["id"] in indicateurs:
            raise ErreurConfig(f"identifiant en double : {ind['id']}")
        if ind["type"] not in TYPES or ind["frequence"] not in FREQUENCES:
            raise ErreurConfig(f"{ind['id']} : type ou fréquence invalide")
        if ind["transformation"] not in TRANSFORMATIONS:
            raise ErreurConfig(f"{ind['id']} : transformation inconnue « {ind['transformation']} »")
        indicateurs[ind["id"]] = ind
    for ind in indicateurs.values():
        for entree in ind.get("entrees", []) or []:
            if entree not in indicateurs:
                raise ErreurConfig(f"{ind['id']} : entrée inconnue « {entree} »")
    accueil = brut.get("accueil", [])
    for ident in accueil:
        if ident not in indicateurs:
            raise ErreurConfig(f"carte d'accueil inconnue : {ident}")
    cfg = Config(
        indicateurs=indicateurs,
        familles=familles,
        accueil=accueil,
        jeux=brut.get("jeux", {}),
        reglages=_lire("reglages.yaml"),
        sources=_lire("sources.yaml"),
        comparaisons=_lire("comparaisons.yaml").get("comparaisons", []),
        evenements=_lire("evenements.yaml").get("evenements", []),
    )
    for comp in cfg.comparaisons:
        for ident in [comp["reference"], *comp.get("autres", [])]:
            if ident not in indicateurs:
                raise ErreurConfig(f"comparaison « {comp['libelle']} » : indicateur inconnu {ident}")
    cfg.ordre_calcul = _ordre(indicateurs)
    return cfg


def _ordre(indicateurs: dict[str, dict]) -> list[str]:
    """Séries calculées dans l'ordre des dépendances (détecte les cycles)."""
    ordre, en_cours, fait = [], set(), set()

    def visiter(ident):
        if ident in fait:
            return
        if ident in en_cours:
            raise ErreurConfig(f"dépendance circulaire autour de {ident}")
        en_cours.add(ident)
        for entree in indicateurs[ident].get("entrees", []) or []:
            visiter(entree)
        en_cours.discard(ident)
        fait.add(ident)
        if indicateurs[ident]["source"] == "calcul":
            ordre.append(ident)

    for ident in indicateurs:
        visiter(ident)
    return ordre
