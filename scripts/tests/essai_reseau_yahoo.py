"""Essai EN RÉSEAU du module Yahoo (hors pytest : nom sans préfixe test_).

Télécharge tous les codes Yahoo du PLAN §4 (G, K, H, I6, J1) en un appel groupé + rattrapage,
puis la courbe à terme du Brent, et imprime pour chaque code : nombre de points, première date,
dernière date, dernière valeur, nombre de trous de plus de 10 jours. Mesure la durée totale.

    python scripts/tests/essai_reseau_yahoo.py
"""
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commun import ErreurSource  # noqa: E402
from sources import yahoo  # noqa: E402

CODES = {
    "G1": "^BFX", "G2": "^GSPC", "G3": "^DJI", "G4": "^IXIC", "G5": "^STOXX50E", "G6": "^GDAXI",
    "G7": "^FCHI", "G8": "^FTSE", "G9": "^N225", "G10": "000001.SS", "G11": "510300.SS",
    "G12": "^HSI", "G13": "IWDA.AS", "K1": "AED.BR",
    "H1": "BZ=F", "H2": "CL=F", "H3": "GC=F", "H4": "TTF=F", "H5": "NG=F", "H6": "HG=F",
    "H7": "DBC", "H8_USO": "USO", "H8_BNO": "BNO", "H9": "GLD", "H10": "VNQ", "H11": "IPRP.AS",
    "H12": "TLT", "H13": "IEF", "H14": "IEGA.AS", "H15": "TIP",
    "I6": "DX-Y.NYB", "J1": "^VIX",
}


def trous(dates: list[str], jours: int = 10) -> int:
    ds = [date.fromisoformat(d) for d in dates]
    return sum(1 for a, b in zip(ds, ds[1:]) if (b - a).days > jours)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    resultats = yahoo.telecharger([{"cle": k, "code": c} for k, c in CODES.items()])
    t1 = time.perf_counter()
    courbe = yahoo.telecharger_courbe_petrole(date.today())
    t2 = time.perf_counter()

    echecs = 0
    print(f"{'id':7} {'code':11} {'points':>6}  {'début':10}  {'fin':10}  {'dernière':>12}  trous>10j")
    for cle, code in CODES.items():
        r = resultats[cle]
        if isinstance(r, ErreurSource):
            echecs += 1
            print(f"{cle:7} {code:11} ERREUR : {r}")
            continue
        dates = list(r)
        print(f"{cle:7} {code:11} {len(r):6d}  {dates[0]}  {dates[-1]}  {r[dates[-1]]:12.4f}  {trous(dates)}")
        if cle == "H2":
            mini = min(r, key=r.get)
            print(f"        minimum CL=F : {r[mini]} le {mini}")

    print()
    if isinstance(courbe, ErreurSource):
        echecs += 1
        print(f"Courbe du Brent : ERREUR : {courbe}")
    else:
        print(f"Courbe du Brent au {courbe['date']} ; comptant {courbe['comptant']}")
        for p in courbe["points"]:
            print(f"  {p['echeance']}  {p['contrat']:11}  {p['prix']:.2f}")
        print(f"  dans 6 mois : {courbe['dans_6_mois']} ; dans 12 mois : {courbe['dans_12_mois']}")

    print(f"\nDurée : séries {t1 - t0:.1f} s ; courbe {t2 - t1:.1f} s ; total {t2 - t0:.1f} s ; échecs : {echecs}")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
