"""OCDE — API SDMX (sdmx.oecd.org/public/rest), réponse SDMX-CSV, sans clé.

Interface : telecharger(demandes) -> {cle: série | ErreurSource}.

Une demande : {"cle": "D13_US", "code": "OECD.SDD.STES,DSD_STES@DF_CLI/USA.M.LI...AA...H", …options}
  code   « AGENCE,FLUX[,VERSION]/CLE » ; la clé doit avoir exactement le nombre de dimensions du
         flux (sinon l'OCDE répond 403/404). Un champ vide = toutes les valeurs, mais la clé doit
         désigner UNE série dans la réponse (sinon : erreur « clé ambiguë »).
  debut  « AAAA-MM-JJ » facultatif : startPeriod = année de début, puis coupure exacte.

Regroupement : clés d'un même flux qui ne diffèrent que par une dimension (ex. CLI de tous les
pays : « CHN+DEU+G4E+GBR+JPN+USA.M.LI...AA...H ») ; un échec d'appel met en erreur chacune de
ses séries, jamais les autres. Attente entre essais : 10 s (limite de débit de l'OCDE, C10).
"""
from __future__ import annotations

from commun import ErreurSource, telecharger as http
from sources.sdmx import annee_debut, lire_csv_series, traiter_demandes

URL = "https://sdmx.oecd.org/public/rest/data/{flux}/{cle}"
ENTETES = {"Accept": "application/vnd.sdmx.data+csv"}
ATTENTE = 10.0
NOM = "OCDE"


def _appel(flux: str, cle: str, debut: str | None, options: tuple) -> dict[str, dict[str, float]]:
    params = {"startPeriod": annee_debut(debut)} if debut else None
    reponse = http(URL.format(flux=flux, cle=cle), params=params, entetes=ENTETES, attente=ATTENTE)
    return lire_csv_series(reponse.text)


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    return traiter_demandes(demandes, NOM, _appel)
