/* ==========================================================================
   app.js — démarrage, navigation par #/page, en-tête (pastille d'état).
   Les données de démarrage (catalogue, état, résumé) sont chargées par des
   balises <script> dans index.html ; le reste à la demande.
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, D = window.Donnees, K = window.Composants, P = window.Pages, G = window.Graphiques;
  var h = O.h;

  var ECRANS = [
    { id: "accueil", libelle: "Accueil", icone: "M4 11l8-7 8 7v9h-5v-6H9v6H4z" },
    { id: "comparateur", libelle: "Comparateur", icone: "M4 19V5m0 14h16M7 15l4-5 3 3 5-7" },
    { id: "taux", libelle: "Taux", icone: "M6 18L18 6M8 8.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zm8 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" },
    { id: "inflation", libelle: "Inflation", icone: "M12 3v18M8 7l4-4 4 4M6 21h12" },
    { id: "croissance", libelle: "Croissance et dette", icone: "M4 20V10m5 10V6m5 14v-8m5 8V4" },
    { id: "banques", libelle: "Banques centrales", icone: "M4 10h16L12 4zM6 10v8m4-8v8m4-8v8m4-8v8M4 20h16" },
    { id: "bourses", libelle: "Bourses", icone: "M4 17l5-5 4 3 7-8M15 7h5v5" },
    { id: "energie", libelle: "Énergie et ETF", icone: "M13 3L5 14h6l-1 7 8-11h-6z" },
    { id: "devises", libelle: "Devises", icone: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm3 6.5c-.5-1-1.6-1.5-3-1.5-1.8 0-3 .9-3 2s1 1.6 3 2 3 1 3 2.1-1.2 1.9-3 1.9c-1.4 0-2.6-.6-3-1.6M12 6v12" },
    { id: "risques", libelle: "Risques", icone: "M12 4l9 16H3zM12 10v4m0 3h.01" },
    { id: "comprendre", libelle: "Comprendre", icone: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm0-5v.01M12 13c0-2 2.5-2 2.5-4a2.5 2.5 0 0 0-5 0" },
  ];
  var BAS = ["accueil", "comparateur", "themes", "comprendre"];
  var racine = document.getElementById("contenu");

  function icone(d) {
    return O.svg("svg", { class: "icone", viewBox: "0 0 24 24", "aria-hidden": "true" },
      O.svg("path", { d: d, fill: "none", stroke: "currentColor", "stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round" }));
  }

  function route() {
    var m = location.hash.replace(/^#\/?/, "").split("/")[0];
    if (m === "etat") return "etat";
    return ECRANS.some(function (e) { return e.id === m; }) ? m : (O.lire("page", "accueil") || "accueil");
  }

  function dessinerOnglets(actif) {
    var haut = O.vider(document.getElementById("onglets-haut"));
    ECRANS.forEach(function (e) {
      haut.append(h("a", { class: "onglet", href: "#/" + e.id, "aria-current": e.id === actif || (actif === "etat" && e.id === "comprendre") ? "page" : null }, icone(e.icone), h("span", {}, e.libelle)));
    });
    var bas = O.vider(document.getElementById("onglets-bas"));
    bas.style.gridTemplateColumns = "repeat(4, 1fr)";
    var themes = ["taux", "inflation", "croissance", "banques", "bourses", "energie", "devises", "risques"];
    BAS.forEach(function (id) {
      if (id === "themes") {
        bas.append(h("button", { class: "onglet", type: "button", "aria-current": themes.indexOf(actif) >= 0 ? "page" : null, style: "border:0;background:none",
          onclick: ouvrirThemes }, icone("M4 6h16M4 12h16M4 18h16"), h("span", {}, "Thèmes")));
        return;
      }
      var e = ECRANS.find(function (x) { return x.id === id; });
      bas.append(h("a", { class: "onglet", href: "#/" + e.id, "aria-current": e.id === actif || (actif === "etat" && id === "comprendre") ? "page" : null }, icone(e.icone), h("span", {}, e.libelle)));
    });
  }

  function ouvrirThemes() {
    var actif = route();
    K.ouvrirFeuille("Thèmes", h("nav", { class: "menu-pages", "aria-label": "Pages thématiques" },
      ECRANS.filter(function (e) { return ["accueil", "comparateur", "comprendre"].indexOf(e.id) < 0; }).map(function (e) {
        return h("a", { href: "#/" + e.id, "aria-current": e.id === actif ? "page" : null, onclick: K.fermerFeuille }, icone(e.icone), e.libelle);
      })));
  }

  function dessinerEntete() {
    var etat = D.etat;
    document.getElementById("sous-titre").textContent = etat.genere_le ? "Données du " + O.dateHeure(etat.genere_le) : "Données non disponibles";
    var comptes = etat.comptes || {};
    var pannes = comptes.erreur || 0, retards = comptes.en_retard || 0;
    var niveau = (etat.alerte && etat.alerte.declenchee) || pannes > 3 ? "rouge" : (pannes || retards ? "orange" : "vert");
    var textes = { vert: "À jour", orange: (pannes + retards) + " en retard", rouge: "Alerte" };
    var pastille = document.getElementById("pastille");
    pastille.className = "etat etat--" + niveau;
    document.getElementById("pastille-texte").textContent = textes[niveau];
    pastille.setAttribute("aria-label", "État des données : " + textes[niveau] + ". Ouvrir la page État des données.");
    pastille.onclick = function () { location.hash = "#/etat"; };
    document.getElementById("pied-detail").textContent = "Sources : FRED®, BCE (Banque centrale européenne), Eurostat, BRI (Banque des règlements internationaux), OCDE (Organisation de coopération et de développement économiques), FMI (Fonds monétaire international), Banque d'Angleterre, Bundesbank, ONS (statistiques britanniques), Fed de New York, Yahoo Finance, STOXX… (détail dans « Comprendre »). This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.";
  }

  var tour = 0;
  function afficher() {
    var page = route();
    tour++;
    O.ecrire("page", page === "etat" ? "comprendre" : page);
    dessinerOnglets(page);
    K.fermerFeuille();
    G.nettoyer();
    O.vider(racine);
    try {
      if (page === "accueil") P.accueil(racine);
      else if (page === "comparateur") window.Comparateur.page(racine);
      else if (page === "etat") P.etat(racine);
      else if (page === "comprendre") P.comprendre(racine);
      else P.thematique(page, racine);
    } catch (e) {
      racine.append(h("p", { class: "chargement" }, "Erreur d'affichage de la page."));
      if (window.console) console.error(e);
    }
    var titrePage = ECRANS.find(function (e) { return e.id === page; });
    document.title = (titrePage ? titrePage.libelle : "État des données") + " — Tableau de bord des marchés";
    window.scrollTo(0, 0);
  }

  window.App = {
    comparer: function (ids, options) {
      window.Comparateur.ajouter(ids, options);
      if (location.hash === "#/comparateur") afficher(); else location.hash = "#/comparateur";
    },
  };

  function demarrer() {
    if (!window.DONNEES || !window.DONNEES.catalogue) {
      O.vider(racine).append(h("p", { class: "chargement" }, "Les données n'ont pas pu être chargées."));
      return;
    }
    dessinerEntete();
    window.addEventListener("hashchange", afficher);
    afficher();
  }

  demarrer();
})();
