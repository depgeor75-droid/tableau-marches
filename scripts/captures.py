"""Captures d'écran de chaque page (PC 1440 × 900 et GSM 390 × 844) et contrôle de la console.

  python scripts/captures.py                    site local en file:// (index.html)
  python scripts/captures.py --url https://depgeor75-droid.github.io/tableau-marches/
  python scripts/captures.py --pages accueil comparateur --sans-images   (contrôle de la console seulement)

Écrit docs/captures/<page>_pc.png et <page>_gsm.png ; sort avec le code 1 si une erreur
apparaît dans la console du navigateur.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
PAGES = ["accueil", "comparateur", "taux", "inflation", "croissance", "banques", "bourses", "energie", "devises", "risques", "comprendre", "etat"]
FORMATS = {"pc": {"width": 1440, "height": 900}, "gsm": {"width": 390, "height": 844}}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=(RACINE / "index.html").as_uri())
    p.add_argument("--pages", nargs="*", default=PAGES)
    p.add_argument("--formats", nargs="*", default=list(FORMATS))
    p.add_argument("--sans-images", action="store_true")
    p.add_argument("--pleine-page", action="store_true")
    args = p.parse_args()
    dossier = RACINE / "docs" / "captures"
    dossier.mkdir(parents=True, exist_ok=True)
    erreurs = []
    with sync_playwright() as pw:
        navigateur = pw.chromium.launch()
        for nom_format in args.formats:
            options = {"viewport": FORMATS[nom_format], "locale": "fr-BE", "timezone_id": "Europe/Brussels"}
            if nom_format == "gsm":
                options.update({"device_scale_factor": 2, "is_mobile": True, "has_touch": True})
            contexte = navigateur.new_context(**options)
            page = contexte.new_page()
            page.on("console", lambda m, f=nom_format: erreurs.append(f"[{f}] {page.url.split('#')[-1]} : {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e, f=nom_format: erreurs.append(f"[{f}] {page.url.split('#')[-1]} : {e}"))
            for nom in args.pages:
                page.goto(f"{args.url.split('#')[0]}#/{nom}")
                page.wait_for_timeout(2500)
                if not args.sans_images:
                    page.screenshot(path=str(dossier / f"{nom}_{nom_format}.png"), full_page=args.pleine_page)
            contexte.close()
        navigateur.close()
    if erreurs:
        print("Erreurs dans la console :")
        for e in erreurs:
            print(" - " + e[:200])
        return 1
    print(f"Aucune erreur dans la console ({len(args.pages)} pages × {len(args.formats)} formats).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
