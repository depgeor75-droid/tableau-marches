"""BIS / BRI — API SDMX v2 (stats.bis.org), réponse SDMX-CSV 2.0, sans clé.

Interface : telecharger(demandes) -> {cle: série | ErreurSource}.

Une demande : {"cle": "A6", "code": "WS_CBPOL/M.CN", …options}
  code   « FLUX/CLE » ; clé SDMX complète du jeu (WS_CBPOL : FREQ.REF_AREA ;
         WS_CBTA : FREQ.REF_AREA.COMP_METHOD.UNIT_MEASURE.CURRENCY.TRANSFORMATION,
         ex. « WS_CBTA/M.GB.B.XDC.GBP.B » = bilan de la Banque d'Angleterre, monnaie nationale,
         milliards, corrigé des ruptures). Version du jeu : 1.0, ou « FLUX@VERSION/CLE ».
  debut  « AAAA-MM-JJ » facultatif : startPeriod = année de début, puis coupure exacte.

Le filtre de la BIS n'étant pas toujours strict, chaque série est re-choisie dans la réponse
d'après sa clé. Regroupement : clés d'un même jeu qui ne diffèrent que par une dimension
(ex. « M.CH+CN ») ; un échec d'appel met en erreur chacune de ses séries, jamais les autres.
"""
from __future__ import annotations

from commun import ErreurSource, telecharger as http
from sources.sdmx import annee_debut, lire_csv_series, traiter_demandes

URL = "https://stats.bis.org/api/v2/data/dataflow/BIS/{flux}/{version}/{cle}"
ENTETES = {"Accept": "application/vnd.sdmx.data+csv;version=2.0.0"}
ATTENTE = 4.0
NOM = "BIS"


def _appel(flux: str, cle: str, debut: str | None, options: tuple) -> dict[str, dict[str, float]]:
    nom, _, version = flux.partition("@")
    params = {"startPeriod": annee_debut(debut)} if debut else None
    reponse = http(URL.format(flux=nom, version=version or "1.0", cle=cle), params=params,
                   entetes=ENTETES, attente=ATTENTE)
    return lire_csv_series(reponse.text)


def telecharger(demandes: list[dict]) -> dict[str, dict[str, float] | ErreurSource]:
    return traiter_demandes(demandes, NOM, _appel)
