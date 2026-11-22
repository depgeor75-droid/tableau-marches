/* ==========================================================================
   pages.js — Accueil, pages thématiques (générées depuis le catalogue),
   État des données, Comprendre. Les blocs du lot 3 (jauges, probabilités,
   signaux…) viennent de js/blocs.js quand il est présent.
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, S = window.Stats, G = window.Graphiques, D = window.Donnees, K = window.Composants;
  var h = O.h;
  var DEPOT = "https://github.com/depgeor75-droid/tableau-marches";
  var LIEN_WORKFLOW = DEPOT + "/actions/workflows/mise-a-jour.yml";

  function ids(famille, filtre) {
    return (D.catalogue.ordre || Object.keys(D.catalogue.indicateurs)).filter(function (id) {
      var ind = D.ind(id);
      return ind.famille === famille && (!filtre || filtre(id, ind));
    });
  }

  function titre(texte, intro) {
    return [h("h1", { class: "page__titre" }, texte), intro ? h("p", { class: "page__intro" }, intro) : null];
  }

  function section(texte, contenu, intro) {
    return h("section", { class: "section" }, h("h2", { class: "section__titre" }, texte), intro ? h("p", { class: "section__intro" }, intro) : null, contenu);
  }

  function bloc(nom) {
    var B = window.Blocs;
    if (B && B[nom]) {
      try { return B[nom](); } catch (e) { return h("p", { class: "aide" }, "Bloc indisponible (" + nom + ")."); }
    }
    return null;
  }

  // ================================================================== Accueil
  function accueil(c) {
    c.append.apply(c, titre("Vue d'ensemble", "Les grands indicateurs des marchés en un coup d'œil. Touchez ⓘ pour comprendre chaque indicateur, ＋ Comparer pour l'étudier dans le comparateur."));
    c.append(K.bandeauEtat());
    c.append(section("Indicateurs clés", K.grilleCartes(D.catalogue.accueil || [])));
    c.append(section("Ce qui a bougé cette semaine", ceQuiABouge(),
      "Les mouvements les plus inhabituels des 7 derniers jours, mesurés par rapport à la volatilité habituelle de chaque série (5 dernières années)."));
    var jauges = bloc("jauges");
    if (jauges) c.append(jauges);
  }

  function ceQuiABouge() {
    var b = D.resume.bouge;
    if (!b || !b.au) return h("p", { class: "aide" }, "Données insuffisantes pour cette semaine.");
    if (b.calme || !b.liste.length) return h("p", { class: "aide" }, "Semaine calme : aucun mouvement inhabituel du " + O.date(b.du) + " au " + O.date(b.au) + ".");
    return h("div", { class: "mouvements" }, b.liste.map(function (m) {
      var ind = D.ind(m.id);
      if (!ind) return null;
      var fois = Math.abs(m.rapport);
      return h("div", { class: "mouvement" },
        h("strong", {}, ind.nom_court, " ", K.boutonInfo(m.id, ind.nom_court)),
        h("span", { class: "chiffres" }, h("span", { class: "fleche" }, O.fleche(m.variation)), " ", K.fmtVariation(ind, m.variation)),
        h("span", { class: "mouvement__detail" }, "Du " + O.date(m.depuis) + " au " + O.date(m.jusqua) + " — mouvement " + O.nombre(fois, 1) + " fois plus ample que d'habitude" +
          " (" + (m.rapport > 0 ? "hausse" : "baisse") + ")."));
    }));
  }

  // ================================================================== pages thématiques
  var PAGES = {
    taux: {
      titre: "Taux d'intérêt", intro: "Taux directeurs des banques centrales, taux des emprunts d'État à long terme et écarts entre eux.",
      sections: [
        { titre: "Taux directeurs", familles: ["A"], coches: ["A1", "A2", "A4", "A5"] },
        { titre: "Taux longs (emprunts d'État)", familles: ["B"], filtre: function (id) { return id.indexOf("BC_") !== 0; }, coches: ["B1", "B4", "B8", "B6"] },
        { titre: "Écarts de taux", familles: ["B"], filtre: function (id) { return id.indexOf("BC_") === 0; }, coches: ["BC_10A2A", "BC_IT_DE"],
          intro: "Un écart (« spread ») est la différence entre deux taux, en points de pourcentage." },
      ],
      blocs: ["courbeUS"],
    },
    inflation: {
      titre: "Inflation et anticipations", intro: "Inflation par pays, anticipations des marchés et des ménages, signaux avancés.",
      sections: [
        { titre: "Inflation par pays", familles: ["C"], coches: ["C1", "C5", "C7", "C11"] },
        { titre: "Anticipations et signaux avancés", familles: ["D"], coches: ["D1", "D10", "D14"] },
      ],
      blocs: ["probabilites", "recession", "anticipations", "previsionsFmi", "signaux", "courbePetrole"],
    },
    croissance: {
      titre: "Croissance et dette", intro: "Croissance du PIB (produit intérieur brut), dette publique et déficits des grandes économies.",
      sections: [
        { titre: "Croissance", familles: ["E"], filtre: function (id) { return id.indexOf("E1_") === 0; }, coches: ["E1_US", "E1_ZE", "E1_CN"] },
        { titre: "Dette publique et solde budgétaire", familles: ["E"], filtre: function (id) { return id.indexOf("E1_") !== 0; }, coches: ["E3T_BE", "E3T_IT", "E3T_DE"] },
      ],
      blocs: ["tableauPays", "detteBarres"],
      encadre: "Une dette élevée oblige l'État à emprunter beaucoup, ce qui tend à maintenir des taux longs élevés.",
    },
    banques: {
      titre: "Banques centrales", intro: "Taille des bilans (QE, QT) et masse monétaire.",
      sections: [{ titre: "Bilans et masse monétaire", familles: ["F"], coches: ["F5_FED", "F5_BCE", "F5_BOJ"] }],
      blocs: ["qeqt"],
      encadre: "QE et QT en 4 lignes : pour soutenir l'économie, une banque centrale peut acheter massivement des obligations (QE, assouplissement quantitatif). Son bilan grossit et les taux longs baissent. Quand elle laisse ces obligations arriver à échéance sans les remplacer, ou les revend (QT, resserrement quantitatif), son bilan diminue. Le QT pousse plutôt les taux longs vers le haut.",
    },
    bourses: {
      titre: "Bourses", intro: "Indices boursiers et valeurs suivies (cours hors dividendes).",
      sections: [{ titre: "Indices boursiers", familles: ["G"], coches: ["G1", "G2", "G5", "G9"] }, { titre: "Valeurs suivies", familles: ["K"], coches: ["K1"] }],
    },
    energie: {
      titre: "Énergie, matières premières et ETF", intro: "Pétrole, gaz, or, cuivre et fonds cotés (ETF).",
      sections: [{ titre: "Énergie et matières premières", familles: ["H"], filtre: function (id) { return ["H1", "H2", "H3", "H4", "H5", "H6"].indexOf(id) >= 0; }, coches: ["H1", "H4", "H3"] },
        { titre: "ETF (fonds cotés)", familles: ["H"], filtre: function (id) { return ["H1", "H2", "H3", "H4", "H5", "H6"].indexOf(id) < 0; }, coches: ["H10", "H11", "H12", "H14"] }],
    },
    devises: {
      titre: "Devises", intro: "Cours des grandes monnaies, dans le sens « 1 € = … » quand c'est pertinent.",
      sections: [{ titre: "Taux de change", familles: ["I"], coches: ["I1", "IC_EURGBP", "IC_EURCHF"] }],
    },
    risques: {
      titre: "Risques et géopolitique", intro: "Peur sur les marchés, stress financier, tensions sur le crédit, risque géopolitique.",
      sections: [{ titre: "Peur et stress", familles: ["J"], coches: ["J1", "J2", "J5"] }],
      blocs: ["jauges"],
    },
  };

  function thematique(nom, c) {
    var p = PAGES[nom];
    c.append.apply(c, titre(p.titre, p.intro));
    p.sections.forEach(function (s) {
      var liste = [];
      s.familles.forEach(function (f) { liste = liste.concat(ids(f, s.filtre)); });
      c.append(section(s.titre, K.grilleCartes(liste), s.intro));
      c.append(K.graphiqueFamille(liste, { titre: s.titre, id: nom + "_" + s.titre, coches: s.coches }));
    });
    if (p.encadre) c.append(h("p", { class: "explication section" }, p.encadre));
    (p.blocs || []).forEach(function (b) { var n = bloc(b); if (n) c.append(n); });
  }

  // ================================================================== État des données
  var LIBELLES_STATUT = { ok: "à jour", en_retard: "en retard", erreur: "source en panne", secours: "source de secours", non_disponible: "non disponible" };

  function etatDonnees(c) {
    var etat = D.etat;
    c.append.apply(c, titre("État des données", "Statut, dernière date et source de chaque série."));
    c.append(K.bandeauEtat());
    c.append(h("div", { class: "actions section" },
      h("a", { class: "bouton bouton--primaire", href: "data/donnees_mensuelles.csv", download: "donnees_mensuelles.csv" }, "Télécharger toutes les données (CSV)"),
      h("a", { class: "bouton", href: LIEN_WORKFLOW, target: "_blank", rel: "noopener noreferrer" }, "Mettre à jour maintenant ↗")));
    c.append(h("p", { class: "aide" }, "« Mettre à jour maintenant » ouvre la page GitHub du robot de collecte : bouton « Run workflow », puis le bouton vert « Run workflow ». Les nouvelles données sont en ligne quelques minutes plus tard. Le fichier CSV contient toutes les séries en mensuel (séparateur « ; », virgule décimale) : il s'ouvre dans Excel et peut être donné à Claude pour une analyse."));
    var comptes = etat.comptes || {};
    c.append(h("p", { class: "section" }, Object.keys(comptes).map(function (k) { return comptes[k] + " " + (LIBELLES_STATUT[k] || k); }).join(" · ")));
    var table = h("table", { class: "tableau" });
    table.append(h("thead", {}, h("tr", {}, h("th", {}, "Indicateur"), h("th", {}, "Statut"), h("th", {}, "Dernière valeur"), h("th", {}, "Source"), h("th", {}, "Remarque"))));
    var corps = h("tbody", {});
    D.catalogue.familles.forEach(function (fam) {
      corps.append(h("tr", {}, h("th", { colspan: "5", class: "selection__famille", scope: "colgroup" }, fam.nom)));
      ids(fam.id).forEach(function (id) {
        var ind = D.ind(id), e = D.etatSerie(id);
        corps.append(h("tr", {},
          h("td", {}, ind.nom_court, " ", K.boutonInfo(id, ind.nom_court)),
          h("td", {}, LIBELLES_STATUT[e.statut] || e.statut || "?"),
          h("td", { class: "num" }, e.date ? O.dateSelon(e.date, ind.frequence) : "—"),
          h("td", {}, e.source || ind.source || ""),
          h("td", {}, ind.raison || e.message || "")));
      });
    });
    table.append(corps);
    c.append(h("div", { class: "tableau-zone section" }, table));
    var jeux = etat.jeux || {};
    if (Object.keys(jeux).length) {
      c.append(section("Jeux particuliers", h("ul", { class: "points" }, Object.keys(jeux).map(function (k) {
        var j = jeux[k], nom = (D.catalogue.jeux[k] || {}).nom || k;
        return h("li", { class: "point point--info" }, h("span", { class: "point__icone" }, j.statut === "ok" ? "✓" : "!"),
          h("div", {}, h("div", { class: "point__titre" }, nom), h("div", { class: "point__detail" }, (LIBELLES_STATUT[j.statut] || j.statut) + (j.date ? " — " + O.date(j.date) : "") + (j.message ? " — " + j.message : ""))));
      }))));
    }
  }

  // ================================================================== Comprendre
  var LEXIQUE = [
    ["t:base100", "Base 100"], ["t:points", "Points de % et %"], ["t:glissement", "Glissement annuel"], ["t:correlation", "Corrélation"],
    ["t:causalite", "Corrélation et causalité"], ["t:glissante", "Corrélation glissante"], ["t:decalage", "Décalage dans le temps"],
    ["t:percentile", "Percentile"], ["t:qeqt", "QE et QT"], ["t:point_mort", "Point mort d'inflation"], ["t:courbe", "Courbe des taux"],
    ["t:spread", "Écart de taux (spread)"], ["t:etf", "ETF"], ["t:future", "Contrat à terme (« future »)"], ["t:dividendes", "Prix hors dividendes"],
    ["t:fiabilite", "Seuil de fiabilité d'une corrélation"],
  ];

  function comprendre(c) {
    c.append.apply(c, titre("Comprendre", "Les liens entre les indicateurs, le lexique, le mode d'emploi et les sources."));
    var schema = bloc("schema");
    if (schema) c.append(schema);
    c.append(section("Mode d'emploi", h("ol", { class: "aide", style: "list-style: decimal; padding-left: 20px; display: grid; gap: 4px" }, [
      "L'Accueil montre 12 indicateurs clés, les mouvements inhabituels de la semaine et les jauges.",
      "Chaque carte donne la dernière valeur, sa date, les variations sur 1 mois et 1 an (▲▼ en couleur neutre : une hausse n'est pas toujours une bonne nouvelle) et la position dans l'historique.",
      "Le bouton ⓘ ouvre une fiche qui explique l'indicateur simplement.",
      "Les pages thématiques (Taux, Inflation, Bourses…) regroupent les cartes et un graphique par famille : cochez les séries, choisissez la période (1 M à Max).",
      "＋ Comparer envoie un indicateur dans le comparateur.",
      "Dans le comparateur, l'étoile ☆ désigne la référence. Vert bleuté : les courbes bougent ensemble ; rouge orangé : en sens inverse ; gris : pas de lien fiable.",
      "Le mode « Mouvements » (par défaut) évite les fausses corrélations dues aux tendances de fond ; « Rythmes annuels » compare des variations sur 12 mois.",
      "Le curseur de décalage teste si un indicateur en annonce un autre ; « Trouver le meilleur décalage » essaie tous les décalages.",
      "« Exporter cette comparaison » télécharge un fichier CSV et copie un résumé à coller dans une conversation avec Claude.",
      "Les données sont mises à jour chaque matin automatiquement ; « État des données » montre les éventuels retards et permet une mise à jour manuelle.",
    ].map(function (t) { return h("li", {}, t); }))));
    var lexique = h("dl", { class: "lexique" });
    LEXIQUE.forEach(function (x) {
      lexique.append(h("dt", {}, x[1], " ", K.boutonInfo(x[0], x[1])));
      lexique.append(h("dd", { "data-fiche": x[0] }, ""));
    });
    c.append(section("Lexique", lexique));
    K.chargerFiches().then(function (fiches) {
      lexique.querySelectorAll("dd[data-fiche]").forEach(function (dd) {
        var f = fiches[dd.getAttribute("data-fiche")];
        dd.textContent = f ? f.phrase : "Fiche à venir.";
      });
    });
    c.append(section("État des données", h("p", {}, h("a", { href: "#/etat" }, "Voir l'état de toutes les séries, télécharger les données (CSV), lancer une mise à jour manuelle →"))));
    c.append(section("Sources et mentions légales", h("div", { class: "aide", style: "display: grid; gap: 6px" },
      h("p", {}, "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis. ",
        h("em", {}, "(Ce produit utilise l'interface de programmation FRED® mais n'est ni approuvé ni certifié par la Banque fédérale de réserve de Saint-Louis.)"), " ",
        O.lienExterne("https://fred.stlouisfed.org/docs/api/terms_of_use.html", "Conditions d'utilisation de l'API FRED"), ". Les utilisateurs de cette application sont tenus par ces conditions pour les données issues de FRED."),
      h("p", {}, "Indice de risque géopolitique : Caldara, Dario et Matteo Iacoviello (2022), « Measuring Geopolitical Risk », American Economic Review, vol. 112, n° 4, p. 1194-1225 ; données téléchargées sur matteoiacoviello.com."),
      h("p", {}, "Chaque série cite sa source dans sa fiche, sous les graphiques et dans « État des données ». Les séries transformées (glissements annuels, écarts, taux croisés, % du PIB) sont des calculs de l'auteur à partir de ces sources."),
      h("p", {}, "Cours de bourse, ETF, matières premières et indice du dollar : Yahoo Finance ; VSTOXX : STOXX Ltd. Usage personnel, non commercial."),
      h("p", {}, "Outil personnel d'information — pas un conseil en investissement. Site non indexé par les moteurs de recherche."))));
  }

  window.Pages = { accueil: accueil, thematique: thematique, etat: etatDonnees, comprendre: comprendre, PAGES: PAGES, LIEN_WORKFLOW: LIEN_WORKFLOW };
})();
