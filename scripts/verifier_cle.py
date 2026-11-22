"""Vérifie que la clé FRED n'apparaît nulle part : fichiers suivis par git, data/, docs/,
historique git. N'affiche jamais la clé, seulement des noms de fichiers ou de commits.

  python scripts/verifier_cle.py                 avant chaque git push (aussi crochet pre-push)
  python scripts/verifier_cle.py --dossiers data docs    dans le workflow (sans historique)

Code de sortie : 0 aucune clé trouvée ; 1 clé trouvée ; 2 aucune clé disponible pour chercher.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import commun  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dossiers", nargs="*", help="ne chercher que dans ces dossiers (pas dans git)")
    args = p.parse_args()
    commun.charger_env()
    cles = [c for c in (os.environ.get("FRED_API_KEY"), os.environ.get("EIA_API_KEY")) if c and len(c) >= 8]
    if not cles:
        print("Aucune clé disponible : vérification impossible.")
        return 2
    trouve = []
    if args.dossiers:
        fichiers = [f for d in args.dossiers for f in (RACINE / d).rglob("*") if f.is_file()]
    else:
        suivis = subprocess.run(["git", "ls-files"], cwd=RACINE, capture_output=True, text=True, encoding="utf-8").stdout.split("\n")
        fichiers = [RACINE / f for f in suivis if f] + [f for d in ("data", "docs") for f in (RACINE / d).rglob("*") if f.is_file()]
    for f in fichiers:
        if f.name == ".env" or not f.exists():
            continue
        try:
            contenu = f.read_bytes()
        except OSError:
            continue
        if any(c.encode() in contenu for c in cles):
            trouve.append(str(f.relative_to(RACINE)))
    if not args.dossiers:
        for c in cles:
            log = subprocess.run(["git", "log", "--all", "--oneline", f"-S{c}"], cwd=RACINE, capture_output=True, text=True, encoding="utf-8")
            trouve += [f"commit {ligne.split()[0]}" for ligne in log.stdout.splitlines() if ligne.strip()]
    if trouve:
        print("ARRÊT : clé trouvée dans : " + ", ".join(sorted(set(trouve))))
        return 1
    print("Aucune clé dans les fichiers vérifiés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
