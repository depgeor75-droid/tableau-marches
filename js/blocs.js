/* ==========================================================================
   blocs.js — blocs particuliers des pages : courbe des taux US, jauges QE,
   probabilités (SPF), récession, anticipations de taux, prévisions du FMI,
   signaux d'inflation, tableau des pays, QE/QT, schéma des liens, courbe du pétrole.
   Les chiffres viennent de data/resume.js et data/previsions.js (calculés en Python).
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, S = window.Stats, G = window.Graphiques, D = window.Donnees, K = window.Composants;
  var h = O.h;

  function section(titre, contenu, intro, id) {
    return h("section", { class: "section", id: id || null }, h("h2", { class: "section__titre" }, titre), intro ? h("p", { class: "section__intro" }, intro) : null, contenu);
  }

  // ------------------------------------------------------------ courbe des taux US
  function courbeUS() {
    var c = D.resume.courbe_us;
    if (!c) return null;
    var z = G.zone("Courbe des taux américains aujourd'hui et il y a un an", "graphique__zone--petit");
    var bloc = h("div", { class: "graphique" }, z.conteneur,
      h("p", { class: "rappel" }, "Taux des emprunts d'État américains à 3 mois, 2 ans et 10 ans, le " + O.date(c.date) + (c.il_y_a_1_an ? " et le " + O.date(c.il_y_a_1_an.date) : "") + ". Source : Trésor américain via FRED®."));
    requestAnimationFrame(function () {
      var cats = ["3 mois", "2 ans", "10 ans"], cles = ["3M", "2A", "10A"];
      var series = [{ nom: "Aujourd'hui", valeurs: cles.map(function (k) { return c.points[k]; }), couleur: "--serie-1" }];
      if (c.il_y_a_1_an) series.push({ nom: "Il y a 1 an", valeurs: cles.map(function (k) { return c.il_y_a_1_an.points[k]; }), couleur: "--serie-neutre" });
      G.barres(z.canevas, cats, series, { format: function (v) { return O.nombre(v, 2) + " %"; } });
    });
    var legende = h("div", { class: "legende" },
      h("span", { class: "legende__item" }, h("span", { class: "legende__carre", style: "background: var(--serie-1)" }), "Aujourd'hui"),
      c.il_y_a_1_an ? h("span", { class: "legende__item" }, h("span", { class: "legende__carre", style: "background: var(--serie-neutre)" }), "Il y a 1 an") : null);
    return section("Courbe des taux américains", [legende, bloc], "Quand les taux courts dépassent les taux longs (courbe « inversée »), le marché anticipe souvent un ralentissement.", "courbe-us");
  }

  window.Blocs = { courbeUS: courbeUS };
})();
