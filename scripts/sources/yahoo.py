"""Yahoo Finance (via yfinance 1.8) — familles G, K, H3-H15, I6, jours récents de H1, H2, J1
et courbe à terme du Brent (jeu `courbe_petrole`, D15).

Principes (PLAN §4, §6.5, §7.1, §12) :
- UN appel groupé `yf.download(...)` pour tous les codes, clôture NON ajustée des dividendes
  (colonne `Close`, `auto_adjust=False`), `threads=False` pour ne pas inonder Yahoo ;
- puis rattrapage code par code des codes vides ou en échec, en 3 tours espacés de 20, 60 et
  180 s (paramètre `attentes`). Un tour est interrompu dès que Yahoo limite le débit (429) :
  insister ne ferait que prolonger le blocage ; les codes restants passent au tour suivant.
  Un code que Yahoo déclare inconnu (« Quote not found », « possibly delisted ») lors d'un
  appel individuel n'est plus retenté ;
- un code en échec n'affecte jamais les autres : il reçoit une ErreurSource (message court en
  français, passé par commun.nettoyer), les autres leur série.

Une série = {date ISO réelle "AAAA-MM-JJ": float}, triée, via commun.serie_propre : aucune
valeur NaN, aucune interpolation, aucun report. Les valeurs négatives sont gardées (CL=F le
20/04/2020). Pièges traités :
- dates : on prend la date LOCALE de la bourse. yfinance la donne déjà pour les données
  quotidiennes (index sans fuseau) ; si l'index porte un fuseau, c'est celui de la bourse et on
  lit la date dans ce fuseau, sans jamais convertir en UTC (minuit à Tokyo = veille en UTC) ;
- doublons de dates : la dernière valeur numérique l'emporte (les NaN ne comptent pas) ;
- séance en cours : la collecte tourne à 5 h 17 UTC, heure à laquelle Tokyo, Shanghai et
  Hong Kong sont OUVERTS et où la séance des contrats à terme de New York a commencé. Règle
  simple : on écarte toute ligne datée d'après « aujourd'hui » (date locale de la bourse), et
  la ligne datée d'aujourd'hui tant que l'heure locale n'a pas dépassé la clôture + 30 min
  (table `_SEANCES`, par suffixe ou par code ; à défaut New York, 17 h 30). Jours fériés et
  clôtures anticipées ne sont pas modélisés : au pire, une séance close est écartée et
  reprise à l'exécution suivante (jamais l'inverse).
"""
from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, time as heure, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from commun import ErreurSource, nettoyer, serie_propre

DEBUT = "1989-01-01"
ATTENTES = (20, 60, 180)  # secondes avant chaque tour de rattrapage

# ------------------------------------------------------------------ séance en cours
_NEW_YORK = ("America/New_York", heure(17, 30))
_SEANCES_SUFFIXES = {
    ".SS": ("Asia/Shanghai", heure(15, 30)),
    ".SZ": ("Asia/Shanghai", heure(15, 30)),
    ".T": ("Asia/Tokyo", heure(16, 0)),
    ".HK": ("Asia/Hong_Kong", heure(16, 40)),
    ".BR": ("Europe/Brussels", heure(18, 10)),
    ".AS": ("Europe/Brussels", heure(18, 10)),
    ".PA": ("Europe/Brussels", heure(18, 10)),
    ".DE": ("Europe/Brussels", heure(18, 10)),
    ".MI": ("Europe/Brussels", heure(18, 10)),
    ".L": ("Europe/London", heure(17, 5)),
}
_SEANCES_CODES = {
    "^N225": ("Asia/Tokyo", heure(16, 0)),
    "^HSI": ("Asia/Hong_Kong", heure(16, 40)),
    "^BFX": ("Europe/Brussels", heure(18, 10)),
    "^FCHI": ("Europe/Brussels", heure(18, 10)),
    "^GDAXI": ("Europe/Brussels", heure(18, 10)),
    "^STOXX50E": ("Europe/Brussels", heure(18, 10)),
    "^FTSE": ("Europe/London", heure(17, 5)),
}


def fuseau_et_fin_de_seance(code: str) -> tuple[ZoneInfo, heure]:
    """Fuseau de la bourse et heure locale à partir de laquelle la séance du jour est close."""
    code = code.upper()
    fuseau, fin = _SEANCES_CODES.get(code, (None, None))
    if fuseau is None:
        for suffixe, valeur in _SEANCES_SUFFIXES.items():
            if code.endswith(suffixe):
                fuseau, fin = valeur
                break
        else:
            fuseau, fin = _NEW_YORK  # indices et ETF américains, contrats à terme, DX-Y.NYB, ^VIX
    return ZoneInfo(fuseau), fin


def ecarter_seance_en_cours(serie: dict[str, float], code: str, maintenant: datetime) -> dict[str, float]:
    """Retire les lignes datées d'après aujourd'hui, et celle d'aujourd'hui si la séance n'est pas close."""
    fuseau, fin = fuseau_et_fin_de_seance(code)
    local = maintenant.astimezone(fuseau)
    aujourd = local.date().isoformat()
    close = local.time() >= fin
    return {d: v for d, v in serie.items() if d < aujourd or (d == aujourd and close)}


# ------------------------------------------------------------------ appel yfinance
class _Capteur(logging.Handler):
    """Récupère les messages d'erreur que yfinance écrit dans son journal (« ['X']: motif »)."""

    def __init__(self):
        super().__init__(logging.ERROR)
        self.lignes: list[str] = []

    def emit(self, record):  # pragma: no cover - trivial
        try:
            self.lignes.append(record.getMessage())
        except Exception:
            pass


def _erreurs_du_journal(lignes: list[str]) -> dict[str, str]:
    erreurs = {}
    for ligne in lignes:
        for morceau in ligne.splitlines():
            m = re.match(r"\s*\[([^\]]*)\]:\s*(.*)", morceau)
            if not m:
                continue
            for code in re.findall(r"'([^']+)'", m.group(1)):
                erreurs[code.upper()] = m.group(2).strip()
    return erreurs


def _appel(codes: list[str], debut: str) -> tuple[pd.DataFrame | None, dict[str, str]]:
    """Un appel yf.download. Retourne (tableau ou None, {CODE: motif d'erreur brut})."""
    journal = logging.getLogger("yfinance")
    capteur = _Capteur()
    anciens = (journal.handlers[:], journal.propagate, journal.level)
    journal.handlers = [capteur]
    journal.propagate = False  # pas de pavé d'erreurs anglaises dans la sortie de la collecte
    if journal.level == logging.NOTSET or journal.level > logging.ERROR:
        journal.setLevel(logging.ERROR)
    try:
        tableau = yf.download(codes, start=debut, auto_adjust=False, group_by="ticker",
                              threads=False, progress=False)
        erreurs = _erreurs_du_journal(capteur.lignes)
    except Exception as erreur:  # panne de l'appel entier : chaque code est en échec
        tableau = None
        erreurs = {c.upper(): f"{type(erreur).__name__}: {erreur}" for c in codes}
    finally:
        journal.handlers, journal.propagate = anciens[0], anciens[1]
        journal.setLevel(anciens[2])
    return tableau, erreurs


def _dormir(secondes: float) -> None:
    if secondes > 0:
        time.sleep(secondes)


# ------------------------------------------------------------------ lecture du tableau
def _colonne_close(tableau: pd.DataFrame | None, code: str, seul: bool) -> pd.Series | None:
    if tableau is None or not isinstance(tableau, pd.DataFrame) or tableau.empty:
        return None
    colonnes = tableau.columns
    if isinstance(colonnes, pd.MultiIndex):
        for niveau in range(colonnes.nlevels):
            valeurs = [str(v).upper() for v in colonnes.get_level_values(niveau)]
            if code in valeurs:
                masque = [v == code for v in valeurs]
                sous = tableau.loc[:, masque]
                sous.columns = sous.columns.droplevel(niveau)
                if "Close" not in sous.columns:
                    return None
                close = sous["Close"]
                return close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
        return None
    if seul and "Close" in colonnes:  # appel d'un seul code sans niveau « Ticker »
        close = tableau["Close"]
        return close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
    return None


def _date_locale(horodatage) -> str | None:
    """Date de séance « AAAA-MM-JJ » lue dans le fuseau de l'index (celui de la bourse)."""
    try:
        ts = pd.Timestamp(horodatage)
    except (TypeError, ValueError):
        return None
    if pd.isna(ts):
        return None
    return ts.date().isoformat()  # avec fuseau : date dans CE fuseau, pas en UTC


def serie_depuis_tableau(tableau, code: str, maintenant: datetime, seul: bool = False) -> dict[str, float]:
    """Série propre d'un code dans la réponse de yf.download ({} si absente ou vide)."""
    close = _colonne_close(tableau, code.upper(), seul)
    if close is None:
        return {}
    paires = []
    for horodatage, valeur in close.items():
        jour = _date_locale(horodatage)
        if jour is not None and not pd.isna(valeur):  # NaN écartés AVANT le dédoublonnage
            paires.append((jour, valeur))
    return ecarter_seance_en_cours(serie_propre(paires), code, maintenant)


# ------------------------------------------------------------------ messages
def _motif(brut: str | None) -> str:
    if not brut:
        return "aucune donnée renvoyée par Yahoo"
    b = brut.lower()
    if "rate limit" in b or "too many requests" in b or "429" in b:
        return "Yahoo limite le débit (429)"
    if "delisted" in b or "not found" in b or "no data found" in b or "no timezone" in b or "404" in b:
        return "code inconnu ou retiré chez Yahoo"
    if "timeout" in b or "timed out" in b:
        return "délai de réponse dépassé"
    if "connection" in b or "resolve" in b or "ssl" in b:
        return "Yahoo injoignable (réseau)"
    return f"échec Yahoo ({brut})"


def _est_limite(motif: str) -> bool:
    return "429" in motif


def _est_definitif(motif: str) -> bool:
    return motif.startswith("code inconnu")


# ------------------------------------------------------------------ interface commune
def telecharger(demandes: list[dict], *, attentes=ATTENTES, maintenant: datetime | None = None,
                debut: str = DEBUT) -> dict[str, dict[str, float] | ErreurSource]:
    """Chaque demande : {"cle": str unique, "code": str (code Yahoo)}. Retourne {cle: série | ErreurSource}."""
    maintenant = maintenant or datetime.now(timezone.utc)
    resultats: dict[str, dict[str, float] | ErreurSource] = {}
    par_code: dict[str, list[str]] = {}
    for demande in demandes:
        cle, code = demande.get("cle"), str(demande.get("code") or "").strip()
        if not code:
            resultats[cle] = ErreurSource(nettoyer(f"demande Yahoo sans code ({cle})"))
            continue
        par_code.setdefault(code.upper(), []).append(cle)
    codes = list(par_code)
    if not codes:
        return resultats

    series: dict[str, dict[str, float]] = {}
    motifs: dict[str, str] = {}
    essais = {c: 1 for c in codes}

    tableau, erreurs = _appel(codes, debut)
    for code in codes:
        serie = serie_depuis_tableau(tableau, code, maintenant, seul=len(codes) == 1)
        if serie:
            series[code] = serie
        else:
            motifs[code] = _motif(erreurs.get(code))

    definitifs: set[str] = set()
    for attente in attentes:
        a_tenter = [c for c in codes if c not in series and c not in definitifs]
        if not a_tenter:
            break
        _dormir(attente)
        for code in a_tenter:
            tableau, erreurs = _appel([code], debut)
            essais[code] += 1
            serie = serie_depuis_tableau(tableau, code, maintenant, seul=True)
            if serie:
                series[code] = serie
                motifs.pop(code, None)
                continue
            motifs[code] = _motif(erreurs.get(code))
            if _est_definitif(motifs[code]):
                definitifs.add(code)
            elif _est_limite(motifs[code]):
                break  # Yahoo bloque : les codes restants attendent le tour suivant

    for code, cles in par_code.items():
        for cle in cles:
            if code in series:
                resultats[cle] = dict(series[code])
            else:
                n = essais[code]
                resultats[cle] = ErreurSource(nettoyer(
                    f"Yahoo {code} : {motifs.get(code, 'échec')} ({n} essai{'s' if n > 1 else ''})"))
    return resultats


# ------------------------------------------------------------------ courbe à terme du Brent
LETTRES_MOIS = "FGHJKMNQUVXZ"


def ajouter_mois(annee: int, mois: int, n: int) -> tuple[int, int]:
    total = annee * 12 + (mois - 1) + n
    return total // 12, total % 12 + 1


def contrats_brent(aujourd_hui: date) -> list[tuple[str, str]]:
    """[(échéance "AAAA-MM", code Yahoo)] pour les mois de livraison courant + 1 à + 13."""
    liste = []
    for n in range(1, 14):
        a, m = ajouter_mois(aujourd_hui.year, aujourd_hui.month, n)
        liste.append((f"{a:04d}-{m:02d}", f"BZ{LETTRES_MOIS[m - 1]}{a % 100:02d}.NYM"))
    return liste


def jours_ouvrables_avant(jour: date, n: int) -> date:
    """Date située n jours ouvrables (lundi-vendredi) avant `jour`."""
    d = jour
    while n > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def choisir_echeance(points: list[dict], aujourd_hui: date, decalage: int) -> dict | None:
    """Contrat du mois courant + décalage ; sinon le plus proche à ± 1 mois (le plus tôt
    d'abord en cas d'égalité, plus liquide) ; sinon None (PLAN §6.5)."""
    par_echeance = {p["echeance"]: p for p in points}
    for n in (decalage, decalage - 1, decalage + 1):
        a, m = ajouter_mois(aujourd_hui.year, aujourd_hui.month, n)
        p = par_echeance.get(f"{a:04d}-{m:02d}")
        if p is not None:
            return {"echeance": p["echeance"], "prix": p["prix"]}
    return None


def telecharger_courbe_petrole(aujourd_hui: date, *, maintenant: datetime | None = None) -> dict | ErreurSource:
    """Structure `courbe_petrole` du PLAN §6.5, ou ErreurSource (retournée, pas levée) si moins
    de 6 contrats ont un cours de clôture datant de moins de 5 jours ouvrables. Un seul appel
    groupé (comptant BZ=F + 13 contrats), sans rattrapage : un contrat absent (échu, ou mois
    lointain que Yahoo ne publie pas) est simplement omis."""
    maintenant = maintenant or datetime.now(timezone.utc)
    contrats = contrats_brent(aujourd_hui)
    codes = ["BZ=F"] + [code for _, code in contrats]
    debut = (aujourd_hui - timedelta(days=21)).isoformat()
    tableau, erreurs = _appel(codes, debut)
    if tableau is None:
        brut = next(iter(erreurs.values()), None)
        return ErreurSource(nettoyer(f"courbe du Brent : {_motif(brut)}"))
    limite = jours_ouvrables_avant(aujourd_hui, 5).isoformat()

    def dernier(code):
        serie = serie_depuis_tableau(tableau, code, maintenant)
        if not serie:
            return None
        jour = max(serie)
        return (jour, serie[jour]) if jour >= limite else None

    points, dates = [], []
    for echeance, code in contrats:
        cours = dernier(code)
        if cours is not None:
            points.append({"echeance": echeance, "contrat": code, "prix": round(cours[1], 4)})
            dates.append(cours[0])
    if len(points) < 6:
        return ErreurSource(nettoyer(
            f"courbe du Brent : {len(points)} contrat(s) à jour sur {len(contrats)}, 6 au minimum"))
    points.sort(key=lambda p: p["echeance"])
    comptant = dernier("BZ=F")
    return {
        "statut": "ok",
        "produit": "Brent",
        "date": max(dates),
        "unite": "USD/baril",
        "comptant": {"valeur": round(comptant[1], 4), "contrat": "BZ=F"} if comptant else None,
        "points": points,
        "dans_6_mois": choisir_echeance(points, aujourd_hui, 6),
        "dans_12_mois": choisir_echeance(points, aujourd_hui, 12),
    }
