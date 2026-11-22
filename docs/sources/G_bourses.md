# Sources — familles G (indices boursiers) et K (valeurs suivies)

Test réalisé le 22 novembre 2026 (dimanche) ; dernier jour de bourse disponible partout : vendredi 20 novembre 2026.
Outils : Python 3.12, yfinance 1.8.0, pandas. Aucune clé nécessaire. Tous de type N, clôture non ajustée des dividendes.

## Appel exact qui a fonctionné (un seul appel groupé, sans erreur 429 ni échec)

```python
import yfinance as yf
codes = ["^BFX","^GSPC","^DJI","^IXIC","^STOXX50E","^GDAXI","^FCHI","^FTSE","^N225",
         "000001.SS","000300.SS","^HSI","IWDA.AS","URTH","AED.BR"]
d = yf.download(codes, start="1990-01-01", auto_adjust=False,
                group_by="ticker", threads=False)
serie = d["^GSPC"]["Close"].dropna()   # un DataFrame par code, colonne Close
```
Particularités : les jours fériés propres à chaque place sont des lignes vides (NaN) dans le tableau groupé, à supprimer par `dropna()` code par code. Index = dates locales de séance. Aucune valeur nulle ou négative. Aucun trou anormal (> 10 jours) sauf mention ci-dessous.

## Tableau

| id | indicateur | source retenue | code testé | début | dernière date | fréquence | secours | rediffusion publique | remarque |
|---|---|---|---|---|---|---|---|---|---|
| G1 | BEL 20 | Yahoo (yfinance) | `^BFX` | 1991-04-09 | 2026-11-20 | quotidienne | aucun testable (Stooq bloqué) | restreinte | 9 047 points, 1 201,7 -> 5 797,75. Ne remonte pas à 1990 (manque 1990-01 à 1991-04). Sans trou. |
| G2 | S&P 500 | Yahoo | `^GSPC` | 1990-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 9 291 points. Historique complet depuis 1990. |
| G3 | Dow Jones | Yahoo | `^DJI` | 1992-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | Début 1992 seulement (manque 1990-1991). |
| G4 | Nasdaq Composite | Yahoo | `^IXIC` | 1990-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 9 291 points. |
| G5 | Euro Stoxx 50 | Yahoo | `^STOXX50E` | 2007-03-30 | 2026-11-20 | quotidienne | aucun testable (Stooq bloqué) | restreinte | **Historique court** : 4 926 points depuis mars 2007. Rien avant 2007 via Yahoo ; la profondeur 1990 n'est pas atteignable gratuitement par cette voie. À signaler à Georgy. |
| G6 | DAX | Yahoo | `^GDAXI` | 1990-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 9 335 points. Le DAX est un indice de performance (dividendes réinvestis) par construction, pas un indice de prix : à noter dans la fiche. |
| G7 | CAC 40 | Yahoo | `^FCHI` | 1990-03-01 | 2026-11-20 | quotidienne | aucun testable | restreinte | Début au 1er mars 1990 (manque janvier-février 1990). |
| G8 | FTSE 100 | Yahoo | `^FTSE` | 1990-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 9 319 points. |
| G9 | Nikkei 225 | Yahoo | `^N225` | 1990-01-04 | 2026-11-20 | quotidienne | aucun testable | restreinte | Trou de 11 jours en mai 2019 (jours fériés exceptionnels de l'avènement de l'empereur, réel). |
| G10 | Shanghai Composite | Yahoo | `000001.SS` | 1997-07-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 7 119 points. **Début juillet 1997** (pas 1990). Trous de 11 à 20 jours (février, mai, octobre) = fêtes chinoises, réels. |
| G11 | CSI 300 | **aucune source Yahoo exploitable pour l'indice** | `000300.SS` | 2026-11-20 (1 seul point) | 2026-11-20 | quotidienne | voir remarque | restreinte | **Échec** : `000300.SS`, `399300.SZ` et `000905.SS` ne renvoient qu'UN point ; `^CSI300` n'existe pas. Substituts testés (ETF, pas l'indice) : `510300.SS` (ETF CSI 300, CNY) depuis 2012-05-04, 3 521 points ; `159919.SZ` depuis 2012-05-07 ; `ASHR` (ETF, USD) depuis 2013-11-06, 3 280 points. Recommandation : `510300.SS` en remplacement, début 2012, présenté comme « ETF répliquant le CSI 300 » et non comme l'indice. Indice lui-même : non disponible gratuitement de façon fiable. Priorité S : pas d'alerte. |
| G12 | Hang Seng | Yahoo | `^HSI` | 1990-01-02 | 2026-11-20 | quotidienne | aucun testable | restreinte | 9 104 points. |
| G13 | MSCI World (ETF iShares Core MSCI World, EUR) | Yahoo | `IWDA.AS` | 2009-09-25 | 2026-11-20 | quotidienne | `URTH` (USD) | restreinte | 4 391 points, **en euros**, hors dividendes (ETF de capitalisation : le cours reste un cours d'ETF, pas un indice de prix). `URTH` : début 2012-01-12, 3 737 points, **en dollars**. **Ne jamais raccorder les deux** : si IWDA.AS tombe, URTH remplace la série entière (début 2012, USD) sans la prolonger. |
| K1 | Aedifica | Yahoo | `AED.BR` | 2006-10-23 | 2026-11-20 | quotidienne | aucun | restreinte | 5 136 points, 31,59 -> 63,60 EUR, sans trou. Clôture non ajustée (hors dividendes). |

## Stooq (secours) : inutilisable sans contournement

Appel testé : `GET https://stooq.com/q/d/l/?s=^dax&i=d`, puis `^spx ^ndq ^dji ^cac ^ftm ^nkx ^hsi ^shc ^bel20 ^sx5e ^cs3`.
Résultat pour les 12 codes : HTTP 200 mais le contenu est une page HTML de 796 octets (« This site requires JavaScript to verify your browser », script de vérification anti-robot), jamais le CSV. Pas de clé API demandée, mais une épreuve JavaScript qu'un `requests` ou `curl` ne passe pas. La contourner reviendrait à contourner une détection de robot : non fait. **Conclusion : Stooq n'est plus utilisable en collecte automatique (local comme GitHub Actions), sauf navigateur réel.** Les cases « secours » G1-G12 restent donc sans solution ; le plan doit accepter « source unique Yahoo » pour la famille G, à retester depuis GitHub Actions à l'étape 3. Pour G5, le complément 1990-2007 prévu par la spec n'est pas possible via Stooq.

## Conditions d'utilisation de Yahoo : rediffusion **restreinte**

Source consultée : https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html (lue le 22/11/2026). Extraits (traduits) : il est interdit « d'accéder aux données des Services ou de les collecter par tout moyen automatisé (robots, spiders, scrapers, outils d'extraction...) sans notre permission expresse préalable » ; il est interdit d'exploiter à des fins commerciales tout ou partie des Services (contenu, API, logiciels) ; « sauf mention contraire, vous ne pouvez pas accéder aux Services ni les réutiliser à des fins commerciales ». Les cours d'indices relèvent aussi de licences des fournisseurs d'indices. `yfinance` est un outil tiers non affilié à Yahoo, prévu pour un usage personnel/recherche. **Verdict : restreinte** pour toutes les lignes G et K, y compris la collecte automatisée elle-même. Un site public non commercial qui republie des séries complètes est en zone grise ; Georgy doit trancher (§3 règle 10). Mitigations possibles : afficher graphiques et variations calculées sans téléchargement des cours bruts, citer Yahoo Finance, noindex (déjà prévu).

## Réponses synthétiques

- Euro Stoxx 50 : Yahoo court (depuis 2007-03-30), pas de complément gratuit testable.
- BEL 20 (`^BFX`) : depuis le 9 avril 1991.
- Shanghai Composite : depuis juillet 1997. CSI 300 : indice indisponible (1 point), ETF `510300.SS` depuis mai 2012 en remplacement.
- IWDA.AS : 25/09/2009 (EUR). URTH : 12/01/2012 (USD). Jamais raccordés.
