/* ==========================================================================
   blocs.js — blocs particuliers des pages : courbe des taux US, jauges QE,
   probabilités (SPF), récession, anticipations de taux, prévisions du FMI,
   signaux d'inflation, tableau des pays, QE/QT, schéma des liens, courbe du pétrole.
   Les chiffres viennent de data/resume.js et data/previsions.js (calculés en Python) ;
   ici on ne fait que composer les phrases et dessiner.
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, S = window.Stats, G = window.Graphiques, D = window.Donnees, K = window.Composants;
  var h = O.h;
  var PAYS = { US: "États-Unis", ZE: "Zone euro", DE: "Allemagne", FR: "France", IT: "Italie", BE: "Belgique", JP: "Japon", CN: "Chine", UK: "Royaume-Uni" };

  function section(titre, contenu, intro, id) {
    return h("section", { class: "section", id: id || null }, h("h2", { class: "section__titre" }, titre), intro ? h("p", { class: "section__intro" }, intro) : null, contenu);
  }
  function carte() { return h("div", { class: "carte" }, Array.prototype.slice.call(arguments)); }
  function pct(v, d) { return O.estNombre(v) ? O.nombre(v, d === undefined ? 1 : d) + O.INSECABLE + "%" : "n.d."; }
  function attendre(fn) { requestAnimationFrame(function () { requestAnimationFrame(fn); }); }

  /** Conteneur rempli quand data/previsions.js est chargé. */
  function avecPrevisions(remplir) {
    var zone = h("div", {}, h("p", { class: "aide" }, "Chargement…"));
    O.charger("previsions").then(function (p) {
      O.vider(zone);
      var contenu = p ? remplir(p) : null;
      zone.append(contenu || h("p", { class: "aide" }, "Données non disponibles pour le moment."));
    });
    return zone;
  }

  // ------------------------------------------------------------ courbe des taux US
  function courbeUS() {
    var c = D.resume.courbe_us;
    if (!c) return null;
    var z = G.zone("Courbe des taux américains aujourd'hui et il y a un an", "graphique__zone--petit");
    var legende = h("div", { class: "legende" },
      h("span", { class: "legende__item" }, h("span", { class: "legende__carre", style: "background: var(--serie-1)" }), "Le " + O.date(c.date)),
      c.il_y_a_1_an ? h("span", { class: "legende__item" }, h("span", { class: "legende__carre", style: "background: var(--serie-neutre)" }), "Le " + O.date(c.il_y_a_1_an.date)) : null);
    attendre(function () {
      var cles = ["3M", "2A", "10A"];
      var series = [{ nom: "Le " + O.date(c.date), valeurs: cles.map(function (k) { return c.points[k]; }), couleur: "--serie-1" }];
      if (c.il_y_a_1_an) series.push({ nom: "Le " + O.date(c.il_y_a_1_an.date), valeurs: cles.map(function (k) { return c.il_y_a_1_an.points[k]; }), couleur: "--serie-neutre" });
      G.barres(z.canevas, ["3 mois", "2 ans", "10 ans"], series, { format: function (v) { return O.nombre(v, 2) + " %"; } });
    });
    return section("Courbe des taux américains", h("div", { class: "graphique" }, legende, z.conteneur,
      h("p", { class: "rappel" }, "Taux des emprunts d'État américains à 3 mois, 2 ans et 10 ans. Source : Trésor américain, via FRED®.")),
      "Normalement, emprunter longtemps coûte plus cher. Quand les taux courts dépassent les taux longs (courbe « inversée »), le marché anticipe souvent un ralentissement.", "courbe-us");
  }

  // ------------------------------------------------------------ jauges QE
  function libellesConditions(zone) {
    var r = D.reglages().jauges || {};
    var cible = O.nombre(r.inflation_cible || 2, 0), recul = O.nombre(Math.abs(r.recul_3m || 0.5), 1);
    if (zone === "ZE") return {
      1: "Inflation (IPCH, indice des prix à la consommation harmonisé) sous " + cible + " % ou en net recul (−" + recul + " point sur 3 mois)",
      2: "Peur sur les marchés : VSTOXX au-dessus du " + r.percentile_stress + "ᵉ percentile",
      3: "Stress financier : indicateur CISS de la BCE au-dessus du " + r.percentile_stress + "ᵉ percentile",
      4: "Tensions sur la dette : écart Italie − Allemagne au-dessus du " + r.percentile_ecart + "ᵉ percentile et en hausse de plus de " + O.nombre(r.hausse_ecart_1m, 1) + " point sur 1 mois",
      5: "Crédit sous tension : tensions obligataires (composante du CISS) au-dessus du " + r.percentile_stress + "ᵉ percentile",
      6: "Taux de dépôt de la BCE déjà bas (≤ " + O.nombre(r.taux_bas, 0) + " %)",
    };
    return {
      1: "Inflation (PCE, indice des prix des dépenses de consommation) sous " + cible + " % ou en net recul (−" + recul + " point sur 3 mois)",
      2: "Peur sur les marchés : VIX au-dessus du " + r.percentile_stress + "ᵉ percentile",
      3: "Stress financier : indice de la Fed de Saint-Louis au-dessus du " + r.percentile_stress + "ᵉ percentile",
      4: "Tensions sur la dette : taux américain à 10 ans en hausse de plus de " + O.nombre(r.hausse_us10_1m, 2) + " point sur 1 mois",
      5: "Crédit sous tension : écart de crédit des entreprises au-dessus du " + r.percentile_stress + "ᵉ percentile",
      6: "Taux de la Fed déjà bas (≤ " + O.nombre(r.taux_bas, 0) + " %)",
    };
  }

  var LECTURES = { faible: "faible", possible: "possible", eleve: "élevée" };

  function jauge(zone, j) {
    var libelles = libellesConditions(zone);
    var piste = h("div", { class: "jauge-qe__piste", "aria-hidden": "true" });
    j.conditions.forEach(function (c) { piste.append(h("span", { class: c.ok === null ? "vide" : (c.ok ? "plein" : "") })); });
    var liste = h("ul", { class: "conditions" });
    j.conditions.forEach(function (c) {
      var ind = D.ind(c.id);
      var detail = [];
      if (O.estNombre(c.valeur) && ind) detail.push(K.fmtValeur(ind, c.valeur));
      if (O.estNombre(c.percentile)) detail.push(O.rangOrdinal(c.percentile) + " percentile depuis " + c.depuis);
      if (O.estNombre(c.variation_3m)) detail.push(O.signe(c.variation_3m, 2) + " pt sur 3 mois");
      if (O.estNombre(c.variation_1m)) detail.push(O.signe(c.variation_1m, 2) + " pt sur 1 mois");
      liste.append(h("li", {},
        h("span", { class: "conditions__etat", "aria-label": c.ok === null ? "non évaluée" : (c.ok ? "remplie" : "non remplie") }, c.ok === null ? "?" : (c.ok ? "✓" : "✗")),
        h("span", {}, libelles[c.n], c.ok === null ? h("span", { class: "muet" }, " — non évaluée (série absente ou historique de moins de 10 ans)") : null,
          detail.length ? h("span", { class: "muet" }, " — " + detail.join(", ") + (c.date ? " (" + O.dateSelon(c.date, ind ? ind.frequence : "J") + ")" : "")) : null)));
    });
    var phrase = j.evaluees ?
      "Score " + j.score + " sur " + j.evaluees + (j.evaluees < 6 ? " conditions évaluées" : "") + " : conditions favorables à un nouveau QE — lecture « " + LECTURES[j.lecture] + " »." :
      "Aucune condition évaluable.";
    var b = carte(
      h("h3", { class: "graphique__titre" }, zone === "ZE" ? "Zone euro (BCE)" : "États-Unis (Fed)"),
      h("div", { class: "jauge-qe" },
        h("div", { class: "jauge-qe__score" }, h("span", { class: "jauge-qe__chiffre chiffres" }, j.score + "/" + j.evaluees), h("span", {}, "conditions favorables à un QE — lecture : " + (LECTURES[j.lecture] || "n.d."))),
        piste, h("p", {}, phrase), liste,
        h("p", { class: "aide" }, "Un QE est surtout décidé quand l'inflation est basse et les marchés sous stress. Avec une inflation élevée, la banque centrale a peu de marge, sauf intervention d'urgence ciblée (ex. : Banque d'Angleterre, sept. 2022)."),
        h("p", { class: "rappel" }, "Indicateur maison, aide à la lecture — pas un modèle validé.")));
    if (j.historique) b.append(historiqueJauge(zone, j.historique));
    return b;
  }

  function historiqueJauge(zone, hist) {
    var z = G.zone("Historique du score de la jauge", "graphique__zone--petit");
    var bloc = h("details", { class: "repli" }, h("summary", {}, "Historique du score depuis " + O.dateSelon(hist.debut, "M") + " et lancements réels des QE"), z.conteneur);
    bloc.addEventListener("toggle", function () {
      if (!bloc.open) return;
      var points = hist.scores.map(function (s, i) {
        var d = S.periodeSuivante(S.clePeriode(hist.debut, "M"), "M");
        var cle = S.clePeriode(new Date(Date.UTC(+hist.debut.slice(0, 4), +hist.debut.slice(5, 7) - 1 + i, 1)).toISOString().slice(0, 10), "M");
        return [S.versTemps(cle), O.estNombre(s) && hist.evaluees[i] ? s / hist.evaluees[i] * 6 : null];
      });
      var banque = zone === "ZE" ? /BCE|PEPP/ : /Fed/;
      var evts = (D.catalogue.evenements || []).filter(function (e) { return e.categorie === "banques_centrales" && banque.test(e.libelle); })
        .map(function (e) { return { t: S.versTemps(e.date), libelle: e.libelle }; });
      G.courbes(z.canevas, [{ nom: "Score (ramené sur 6)", points: points, couleur: "--serie-1", spanMs: 45 * G.JOUR, format: function (v) { return O.nombre(v, 1) + " / 6"; } }],
        { axes: { y: { titre: "score sur 6", format: function (v) { return O.nombre(v, 0); } } }, evenements: evts, titreInfobulle: function (t) { return O.dateSelon(S.versIso(t), "M"); } });
    });
    return bloc;
  }

  function jauges() {
    var j = D.resume.jauges;
    if (!j) return null;
    return section("Conditions favorables à un QE", h("div", { class: "grille-2" }, j.ZE ? jauge("ZE", j.ZE) : null, j.US ? jauge("US", j.US) : null),
      "Le QE (assouplissement quantitatif) est l'achat massif d'obligations par une banque centrale. Ces jauges comptent les conditions qui ont souvent précédé un tel programme.", "jauges");
  }

  // ------------------------------------------------------------ probabilités SPF
  function histogramme(classes, probabilites) {
    var max = Math.max.apply(null, probabilites.filter(O.estNombre).concat([1]));
    return h("div", { class: "histogramme" }, classes.map(function (c, i) {
      var p = probabilites[i];
      var libelle = c.libelle || (c.min === null ? "moins de " + O.nombre(c.max, 1) + " %" : c.max === null ? O.nombre(c.min, 1) + " % et plus" : O.nombre(c.min, 1) + " à " + O.nombre(c.max, 1) + " %");
      var cible = c.min !== null && c.max !== null && c.min <= 2 && c.max >= 2;
      return h("div", { class: "barre-h" + (cible ? " barre-h--cible" : "") }, h("span", {}, libelle),
        h("span", { class: "barre-h__piste" }, h("span", { class: "barre-h__rempli", style: "width: " + (O.estNombre(p) ? (p / max) * 100 : 0) + "%" })),
        h("span", { class: "chiffres" }, O.estNombre(p) ? O.nombre(p, 1) + " %" : "n.d."));
    }));
  }

  function probabilites() {
    return section("Probabilités d'inflation selon les prévisionnistes", avecPrevisions(function (p) {
      var blocs = [];
      var bce = p.spf_bce;
      var annee = bce && bce.enquete ? +bce.enquete.slice(0, 4) : new Date().getUTCFullYear();
      if (bce && bce.horizons) {
        var cartes = h("div", { class: "grille-2" });
        bce.horizons.filter(function (x) { return x.annee === annee + 1 || x.annee === annee + 2; }).forEach(function (x) {
          cartes.append(carte(h("h3", { class: "graphique__titre" }, "Zone euro — inflation en " + x.annee),
            h("p", {}, "Les prévisionnistes donnent " + pct(x.sous_1_8) + " de chances que l'inflation de la zone euro soit sous 1,8 % en " + x.annee +
              ", " + pct(x.proche_de_2) + " qu'elle soit proche de 2 % (1,8 à 2,2 %) et " + pct(x.au_dessus_de_2_2) + " qu'elle dépasse 2,2 %."),
            histogramme(bce.classes, x.probabilites),
            h("p", { class: "rappel" }, "Moyenne des probabilités données par les prévisionnistes (enquête " + bce.enquete.replace("-Q", ", T") + (x.reponses_probabilites || x.reponses ? ", " + (x.reponses_probabilites || x.reponses) + " réponses" : "") + "). La classe orangée contient 2 %, l'objectif de la BCE.")));
        });
        blocs.push(cartes, h("p", { class: "aide" }, "Les classes de l'enquête ne permettent pas de dire exactement « sous 2 % » : la classe 1,8-2,2 % chevauche ce seuil. ", K.boutonInfo("D5_LT", "enquête SPF"), " Source : BCE, enquête auprès des prévisionnistes professionnels (SPF)."));
      }
      var us = p.spf_us;
      if (us && us.horizons) {
        var cu = h("div", { class: "grille-2 section" });
        us.horizons.forEach(function (x) {
          cu.append(carte(h("h3", { class: "graphique__titre" }, "États-Unis — inflation sous-jacente en " + x.annee),
            h("p", {}, "Les prévisionnistes américains donnent " + pct(x.sous_2) + " de chances que l'inflation sous-jacente (IPC hors énergie et alimentation, du 4ᵉ trimestre au 4ᵉ trimestre) soit sous 2 % en " + x.annee + "."),
            histogramme(us.classes, x.probabilites),
            h("p", { class: "rappel" }, "Enquête " + us.enquete.replace("-Q", ", T") + " de la Banque fédérale de réserve de Philadelphie (SPF). Le fichier ne publie que l'inflation sous-jacente. ", K.boutonInfo("D6", "enquête SPF américaine"))));
        });
        blocs.push(cu);
      }
      return blocs.length ? h("div", {}, blocs) : null;
    }), "Chaque trimestre, des économistes professionnels donnent la probabilité que l'inflation tombe dans chaque intervalle.", "probabilites");
  }

  // ------------------------------------------------------------ récession
  function recession() {
    var r = D.resume.recession;
    if (!r) return null;
    var v = r.probabilite;
    var metre = h("div", { class: "metre", role: "meter", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(v), "aria-label": "Probabilité de récession" },
      h("div", { class: "metre__rempli", style: "width: " + Math.max(1, Math.min(100, v)) + "%" }));
    var graphique = K.graphiqueFamille(["D14"], { titre: "Probabilité de récession dans 12 mois (historique)", id: "recession", coches: ["D14"], periode: "30A" });
    return section("Probabilité de récession aux États-Unis", h("div", {}, carte(
      h("div", { class: "jauge-qe__score" }, h("span", { class: "jauge-qe__chiffre chiffres" }, pct(v)), h("span", {}, "de probabilité de récession d'ici " + O.moisLong(r.mois_vise + "-01"), " ", K.boutonInfo("D14", "probabilité de récession"))),
      metre,
      h("p", { class: "aide" }, "Modèle de la Banque fédérale de réserve de New York, fondé sur l'écart entre les taux à 10 ans et à 3 mois observé en " + O.moisLong(r.mois_ecart + "-01") + ". Indication statistique, pas une certitude.")), graphique),
      null, "recession");
  }

  // ------------------------------------------------------------ anticipations de taux
  function anticipations() {
    var a = D.resume.anticipations;
    if (!a) return null;
    function phrase(x, banque, court, directeur) {
      if (!x) return h("p", { class: "aide" }, "Données indisponibles pour la " + banque + ".");
      var e = Math.abs(x.ecart);
      var txt = x.lecture === "baisses" ? "Le marché anticipe des baisses de taux de la " + banque + " : le " + court + " est " + O.nombre(e, 2) + " point sous le " + directeur + "." :
        x.lecture === "hausses" ? "Le marché anticipe des hausses de taux de la " + banque + " : le " + court + " est " + O.nombre(e, 2) + " point au-dessus du " + directeur + "." :
          "Le marché anticipe une stabilité des taux de la " + banque + " : le " + court + " est proche du " + directeur + " (écart de " + O.signe(x.ecart, 2) + " point).";
      return h("p", {}, txt, h("span", { class: "muet" }, " (" + O.date(x.date) + ")"));
    }
    return section("Ce que le marché anticipe pour les taux", carte(
      phrase(a.fed, "Fed", "taux américain à 2 ans", "taux directeur"),
      phrase(a.bce, "BCE", "taux à 2 ans des États notés AAA de la zone euro", "taux de dépôt"),
      h("p", { class: "aide" }, "Règle : écart sous −0,25 point → baisses anticipées ; au-dessus de +0,25 → hausses ; entre les deux → stabilité. ", K.boutonInfo("DC_FED", "anticipation des taux")),
      h("p", {}, O.lienExterne("https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html", "Probabilités des prochaines décisions de la Fed (outil CME FedWatch)"))), null, "anticipations");
  }

  // ------------------------------------------------------------ prévisions du FMI
  function previsionsFmi() {
    return section("Prévisions du FMI", avecPrevisions(function (p) {
      var f = p.fmi;
      if (!f || !f.annees) return null;
      var annees = f.annees.slice(1, 4);
      var table = h("table", { class: "tableau" });
      var tete1 = h("tr", {}, h("th", { rowspan: "2" }, "Pays"), h("th", { colspan: "3", class: "num" }, "Inflation (%)"), h("th", { colspan: "3", class: "num" }, "Croissance du PIB réel (%)"));
      var tete2 = h("tr", {});
      [0, 1].forEach(function () { annees.forEach(function (a) { tete2.append(h("th", { class: "num" }, String(a))); }); });
      table.append(h("thead", {}, tete1, tete2));
      var corps = h("tbody", {});
      f.pays.forEach(function (code) {
        var tr = h("tr", {}, h("td", {}, PAYS[code] || code));
        ["inflation", "croissance"].forEach(function (cle) {
          (f[cle][code] || []).slice(1, 4).forEach(function (v) { tr.append(h("td", { class: "num chiffres" }, O.estNombre(v) ? O.nombre(v, 1) : "n.d.")); });
        });
        corps.append(tr);
      });
      table.append(corps);
      return h("div", {}, h("div", { class: "tableau-zone carte" }, table),
        h("p", { class: "rappel" }, "Fonds monétaire international (FMI), Perspectives de l'économie mondiale, édition " + O.moisLong(f.edition + "-01") + ". " + annees[0] + " : année en cours (estimation) ; " + annees[1] + " et " + annees[2] + " : prévisions. Source : FMI. Inflation ", K.boutonInfo("D7", "prévisions d'inflation du FMI"), " · Croissance ", K.boutonInfo("E2", "prévisions de croissance du FMI")));
    }), "Le FMI publie ses prévisions deux fois par an (avril et octobre).", "fmi");
  }

  // ------------------------------------------------------------ signaux d'inflation
  var NOMS_SIGNAUX = { brent_1a: "Pétrole sur 1 an", gaz: "Gaz", prix_production: "Prix à la production", gscpi: "Tensions d'approvisionnement (GSCPI)",
    inflation_anticipee: "Inflation anticipée", salaires: "Salaires", menages: "Anticipations des ménages" };

  function signaux() {
    var s = D.resume.signaux;
    if (!s) return null;
    function zone(code, titre) {
      var z = s[code];
      if (!z) return null;
      var evalues = z.hausse + z.baisse + z.stable;
      var synthese = !evalues ? "Aucun signal évaluable." :
        z.synthese === "baisse" ? z.baisse + " signaux sur " + evalues + " orientés à la baisse → pression à la baisse sur l'inflation dans les prochains mois." :
          z.synthese === "hausse" ? z.hausse + " signaux sur " + evalues + " orientés à la hausse → pression à la hausse sur l'inflation dans les prochains mois." :
            "Signaux partagés (" + z.hausse + " à la hausse, " + z.baisse + " à la baisse, " + z.stable + " stables) : pas de direction nette.";
      return carte(h("h3", { class: "graphique__titre" }, titre),
        h("ul", { class: "signaux" }, z.liste.map(function (x) {
          var ind = x.id ? D.ind(x.id) : null;
          return h("li", {}, h("span", {}, NOMS_SIGNAUX[x.cle] + (ind ? " — " + ind.nom_court : ""), ind ? K.boutonInfo(x.id, ind.nom_court) : null),
            h("span", { class: "chiffres", title: x.fleche ? "Variation sur 3 mois : " + O.signe(x.variation, 2) + " (seuil ± " + O.nombre(x.seuil, 2) + ")" : "non évalué" },
              x.fleche ? x.fleche + " " + ({ "▲": "en hausse", "▼": "en baisse", "▶": "stable" })[x.fleche] : "non évalué"));
        })),
        h("p", {}, h("strong", {}, synthese)));
    }
    return section("Lecture des signaux d'inflation", h("div", {}, h("div", { class: "grille-2" }, zone("ZE", "Zone euro"), zone("US", "États-Unis")),
      h("p", { class: "rappel" }, "Indication, pas une prévision. Direction sur les 3 derniers mois, comparée à la variabilité habituelle de chaque série (▶ = mouvement trop faible pour compter).")),
      "Sept signaux qui précèdent souvent l'inflation de quelques mois.", "signaux");
  }

  // ------------------------------------------------------------ croissance et dette
  function tableauPays() {
    var p = D.resume.pays;
    if (!p) return null;
    var zone = h("div", {});
    O.charger("previsions").then(function (prev) {
      var f = prev && prev.fmi;
      var table = h("table", { class: "tableau" });
      var an = f ? f.annees[1] : null;
      table.append(h("thead", {}, h("tr", {}, h("th", {}, "Pays"), h("th", { class: "num" }, "Croissance (dernier trimestre, sur 1 an)"),
        h("th", { class: "num" }, "Dette publique (% du PIB, FMI)"), h("th", { class: "num" }, "Solde budgétaire (% du PIB)"),
        h("th", { class: "num" }, "Dette en montant"), f ? h("th", { class: "num" }, "Croissance prévue " + an + " / " + (an + 1) + " (FMI)") : null)));
      var corps = h("tbody", {});
      Object.keys(PAYS).forEach(function (code) {
        var l = p[code] || {};
        function cell(x, freq, d) { return h("td", { class: "num chiffres" }, x ? O.nombre(x.valeur, d === undefined ? 1 : d) + " %" + " (" + O.dateSelon(x.date, freq) + ")" : "—"); }
        var m = l.dette_montant;
        corps.append(h("tr", {}, h("td", {}, PAYS[code]),
          cell(l.croissance, "T"), cell(l.dette, "A"), cell(l.deficit, "A"),
          h("td", { class: "num chiffres" }, m ? O.nombre(m.valeur, 0) + " " + (m.unite || "") + (O.estNombre(m.en_euros) && m.unite !== "Md €" ? " (" + O.nombre(m.en_euros, 0) + " Md €)" : "") : "—"),
          f ? h("td", { class: "num chiffres" }, (f.croissance[code] || []).slice(1, 3).map(function (v) { return O.estNombre(v) ? O.nombre(v, 1) : "n.d."; }).join(" / ")) : null));
      });
      table.append(corps);
      zone.append(h("div", { class: "tableau-zone carte" }, table),
        h("p", { class: "rappel" }, "Dette et solde : FMI (toutes administrations publiques, même définition pour tous les pays). Dette en montant : Eurostat (zone euro, Belgique, Allemagne, France, Italie), FRED (dette fédérale américaine), calcul à partir du FMI (Japon, Chine, Royaume-Uni). Croissance : FRED, Eurostat, OCDE, ONS."));
    });
    return section("Comparaison des pays", zone, null, "pays");
  }

  function detteBarres() {
    var p = D.resume.pays;
    if (!p) return null;
    var codes = Object.keys(PAYS).filter(function (c) { return p[c] && p[c].dette; }).sort(function (a, b) { return p[b].dette.valeur - p[a].dette.valeur; });
    if (!codes.length) return null;
    var z = G.zone("Dette publique en % du PIB par pays", "graphique__zone--grand");
    attendre(function () {
      G.barres(z.canevas, codes.map(function (c) { return PAYS[c]; }), [{ nom: "Dette publique (% du PIB)", valeurs: codes.map(function (c) { return p[c].dette.valeur; }), couleur: "--serie-1" }],
        { horizontal: true, format: function (v) { return O.nombre(v, 0) + " %"; } });
    });
    return section("Dette publique en % du PIB", h("div", { class: "graphique" }, z.conteneur,
      h("p", { class: "rappel" }, "Dernière année observée par le FMI pour chaque pays : " + codes.map(function (c) { return PAYS[c] + " " + p[c].dette.date.slice(0, 4); }).join(", ") + ". Source : FMI, Perspectives de l'économie mondiale.")));
  }

  // ------------------------------------------------------------ QE / QT
  function qeqt() {
    var q = D.resume.qe_qt;
    if (!q) return null;
    var noms = { F1: "Fed", F2: "BCE", F3: "Banque du Japon", F4: "Banque d'Angleterre" };
    var libelles = { QE: "QE en cours", QT: "QT en cours", stable: "stable" };
    return section("QE ou QT : où en sont les banques centrales ?", h("div", { class: "cartes" }, Object.keys(noms).map(function (id) {
      var x = q[id];
      return carte(h("h3", { class: "graphique__titre" }, noms[id], K.boutonInfo("t:qeqt", "QE et QT")),
        x && x.statut ? [h("p", {}, h("span", { class: "marque marque--neutre" }, libelles[x.statut])),
          h("p", { class: "aide" }, "Bilan " + (x.variation_3m > 0 ? "en hausse" : "en baisse") + " de " + O.nombre(Math.abs(x.variation_3m), 1) + " % entre " + O.dateSelon(x.date_reference, D.ind(id).frequence) + " et " + O.dateSelon(x.date, D.ind(id).frequence) + ".")] :
          h("p", { class: "aide" }, "Données insuffisantes."));
    })), "Statut d'après la variation du bilan sur 3 mois : hausse de plus de 1 % → QE ; baisse de plus de 1 % → QT ; sinon stable.", "qeqt");
  }

  // ------------------------------------------------------------ schéma des liens
  function schema() {
    var NOEUDS = [
      { id: "energie", texte: "Énergie, pétrole", x: 90, y: 50, page: "energie" },
      { id: "geo", texte: "Géopolitique", x: 90, y: 170, page: "risques" },
      { id: "inflation", texte: "Inflation", x: 300, y: 50, page: "inflation" },
      { id: "directeurs", texte: "Taux directeurs", x: 510, y: 50, page: "taux" },
      { id: "qe", texte: "QE / QT", x: 510, y: 170, page: "banques" },
      { id: "dette", texte: "Dette publique", x: 510, y: 290, page: "croissance" },
      { id: "longs", texte: "Taux longs", x: 720, y: 170, page: "taux" },
      { id: "credit", texte: "Crédit, immobilier", x: 900, y: 80, page: "energie" },
      { id: "bourse", texte: "Bourse", x: 900, y: 200, page: "bourses" },
      { id: "vix", texte: "Peur (VIX)", x: 300, y: 290, page: "risques" },
      { id: "dollar", texte: "Dollar, or", x: 300, y: 380, page: "devises" },
    ];
    var LIENS = [["energie", "inflation"], ["inflation", "directeurs"], ["directeurs", "longs"], ["longs", "credit"], ["longs", "bourse"],
      ["dette", "longs"], ["qe", "longs"], ["geo", "energie"], ["geo", "vix"], ["geo", "dollar"]];
    var pos = {};
    NOEUDS.forEach(function (n) { pos[n.id] = n; });
    var L = 150, H = 44;
    var svg = O.svg("svg", { class: "schema", viewBox: "0 0 1000 420", role: "group", "aria-label": "Schéma des liens entre les grands indicateurs" });
    var defs = O.svg("defs", {}, O.svg("marker", { id: "pointe", viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" },
      O.svg("path", { d: "M0 0 L10 5 L0 10 z", class: "pointe" })));
    svg.append(defs);
    LIENS.forEach(function (l) {
      var a = pos[l[0]], b = pos[l[1]];
      var dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy);
      var ux = dx / d, uy = dy / d;
      var bordA = Math.min(Math.abs((L / 2) / (ux || 1e-9)), Math.abs((H / 2) / (uy || 1e-9)));
      var bordB = bordA;
      svg.append(O.svg("line", { class: "lien-fleche", x1: a.x + ux * bordA, y1: a.y + uy * bordA, x2: b.x - ux * (bordB + 4), y2: b.y - uy * (bordB + 4), "marker-end": "url(#pointe)" }));
    });
    NOEUDS.forEach(function (n) {
      var g = O.svg("a", { class: "bloc", href: "#/" + n.page, tabindex: "0", "aria-label": n.texte + " : ouvrir la page" },
        O.svg("rect", { x: n.x - L / 2, y: n.y - H / 2, width: L, height: H, rx: "10" }),
        O.svg("text", { x: n.x, y: n.y }, document.createTextNode(n.texte)));
      svg.append(g);
    });
    return section("Comment les indicateurs s'influencent", h("div", { class: "carte", style: "overflow-x: auto" }, svg,
      h("p", { class: "aide" }, "Lecture : le pétrole et l'énergie poussent l'inflation ; l'inflation guide les taux directeurs ; ceux-ci influencent les taux longs, qui pèsent sur le crédit, l'immobilier et la bourse. La dette publique et les achats d'obligations des banques centrales (QE/QT) agissent aussi sur les taux longs. La géopolitique fait bouger le pétrole, la peur sur les marchés, le dollar et l'or. Touchez un bloc pour ouvrir sa page.")),
      null, "schema");
  }

  // ------------------------------------------------------------ courbe à terme du pétrole
  function courbePetrole() {
    return section("Ce que le marché anticipe pour le pétrole", avecPrevisions(function (p) {
      var c = p.courbe_petrole;
      if (!c || !c.points || !c.points.length) return h("p", { class: "aide" }, "Courbe à terme non disponible pour le moment.");
      var z = G.zone("Prix du Brent selon l'échéance de livraison", "graphique__zone--petit");
      attendre(function () {
        var cats = (c.comptant ? ["Contrat le plus proche"] : []).concat(c.points.map(function (x) { return O.dateSelon(x.echeance + "-01", "M"); }));
        var vals = (c.comptant ? [c.comptant.valeur] : []).concat(c.points.map(function (x) { return x.prix; }));
        G.barres(z.canevas, cats, [{ nom: "Brent (USD/baril)", valeurs: vals, couleur: "--fam-3" }], { format: function (v) { return O.nombre(v, 2) + " $"; } });
      });
      var phrases = [];
      if (c.dans_6_mois) phrases.push("dans 6 mois (" + O.moisLong(c.dans_6_mois.echeance + "-01") + ") : " + O.nombre(c.dans_6_mois.prix, 2) + " $");
      if (c.dans_12_mois) phrases.push("dans 12 mois (" + O.moisLong(c.dans_12_mois.echeance + "-01") + ") : " + O.nombre(c.dans_12_mois.prix, 2) + " $");
      return carte(h("p", {}, "Prix du baril de Brent fixé aujourd'hui pour une livraison future" + (c.comptant ? " (contrat le plus proche : " + O.nombre(c.comptant.valeur, 2) + " $)" : "") + " — " + phrases.join(" ; ") + ". ", K.boutonInfo("D15", "courbe à terme du pétrole")),
        z.conteneur,
        h("p", { class: "rappel" }, "Cours des contrats à terme du " + O.date(c.date) + ". Des échéances lointaines moins chères signalent surtout un marché tendu aujourd'hui (offre rare, stocks bas) ; ce n'est pas une prévision du prix futur. Source : Yahoo Finance (contrats Brent, NYMEX). ", K.boutonInfo("t:future", "contrat à terme")));
    }), null, "petrole");
  }

  window.Blocs = { courbeUS: courbeUS, jauges: jauges, probabilites: probabilites, recession: recession, anticipations: anticipations,
    previsionsFmi: previsionsFmi, signaux: signaux, tableauPays: tableauPays, detteBarres: detteBarres, qeqt: qeqt, schema: schema, courbePetrole: courbePetrole };
})();
