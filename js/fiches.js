/* ==========================================================================
   fiches.js — fiches explicatives (§7 du cahier des charges), chargé au premier
   clic sur ⓘ. Contenu statique ; structure de chaque fiche :
   { titre, phrase, mesure, calcul, interpreter, bouger, liens: [ids], piege }
   Les fiches des indicateurs sont rédigées à l'étape 4.
   ========================================================================== */
window.FICHES = window.FICHES || {};

window.Fiches = {
  rendre: function (f, ind, id) {
    var O = window.Outils, h = O.h, K = window.Composants;
    var bloc = h("div", { class: "fiche" });
    if (f.phrase) bloc.append(h("p", { class: "fiche__phrase" }, h("strong", {}, "En une phrase : "), f.phrase));
    [["Ce que ça mesure", f.mesure], ["Comment c'est calculé", f.calcul], ["Comment l'interpréter", f.interpreter],
      ["Ce qui le fait bouger, ce qu'il influence", f.bouger], ["Piège à éviter", f.piege]].forEach(function (x) {
      if (x[1]) bloc.append(h("h3", {}, x[0]), h("p", {}, x[1]));
    });
    if (f.liens && f.liens.length) {
      var p = h("p", {}, "Voir aussi : ");
      f.liens.forEach(function (l, i) {
        var cible = window.Donnees.ind(l);
        var nom = cible ? cible.nom_court : (window.FICHES[l] ? window.FICHES[l].titre : l);
        if (i) p.append(", ");
        p.append(h("a", { href: "#", onclick: function (ev) { ev.preventDefault(); K.ouvrirFiche(l); } }, nom));
      });
      bloc.append(p);
    }
    return bloc;
  },
};
