"""Fusionne les fiches rédigées (docs/fiches/*.json) dans js/fiches.js (contenu statique).

  python scripts/fiches_vers_js.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CHAMPS = ("titre", "phrase", "mesure", "calcul", "interpreter", "bouger", "liens", "piege")


def main() -> int:
    fiches = {}
    for f in sorted((RACINE / "docs" / "fiches").glob("*.json")):
        contenu = json.loads(f.read_text(encoding="utf-8"))
        for cle, fiche in contenu.items():
            if cle in fiches:
                print(f"Attention : fiche {cle} en double ({f.name})")
            manquants = [c for c in CHAMPS if c not in fiche]
            if manquants:
                print(f"Attention : {cle} sans {', '.join(manquants)}")
            fiches[cle] = {c: fiche.get(c) for c in CHAMPS}
    # Liens : alias vers les clés réelles ; liens inconnus retirés (signalés)
    import sys as _s
    _s.path.insert(0, str(RACINE / "scripts"))
    import commun
    catalogue = commun.lire_js(RACINE / "data" / "catalogue.js") or {"indicateurs": {}}
    alias = {"t:prix_hors_dividendes": "t:dividendes", "t:contrat_a_terme": "t:future", "B5": "B5_10A"}
    for cle, fiche in fiches.items():
        liens = []
        for l in fiche.get("liens") or []:
            l = alias.get(l, l)
            if (l in catalogue["indicateurs"] or l in fiches) and l not in liens and l != cle:
                liens.append(l)
            elif l not in liens:
                print(f"Lien retiré dans {cle} : {l}")
        fiche["liens"] = liens
    js = (RACINE / "js" / "fiches.js").read_text(encoding="utf-8")
    debut = js.index("window.FICHES = ")
    fin = js.index("\nwindow.Fiches = ")
    corps = "window.FICHES = {\n" + ",\n".join(
        f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in sorted(fiches.items())) + "\n};\n"
    js = js[:debut] + corps + js[fin:]
    with open(RACINE / "js" / "fiches.js", "w", encoding="utf-8", newline="\n") as sortie:
        sortie.write(js)
    print(f"{len(fiches)} fiches écrites dans js/fiches.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
