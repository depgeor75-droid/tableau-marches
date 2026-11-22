/* ==========================================================================
   comparateur.js — page Comparateur (§9 du cahier des charges, PLAN §9.4).
   Tous les calculs passent par js/stats.js (fonctions pures testées).
   Couleurs : vert bleuté = bougent ensemble ; rouge orangé = sens inverse ;
   gris = pas de lien fiable. Épaisseur = force du lien.
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, S = window.Stats, G = window.Graphiques, D = window.Donnees, K = window.Composants;
  var h = O.h;

  var MODES = {
    mouvements: { nom: "Mouvements", aide: "Compare les variations d'une période à l'autre (en % pour un prix ou un niveau, en points pour un taux). Évite les fausses corrélations dues à deux tendances de fond." },
    rythmes: { nom: "Rythmes annuels", aide: "Compare la variation sur 12 mois des prix et niveaux avec le niveau des taux (ex. : Brent sur 1 an et inflation). Les variations sur 12 mois se recouvrent d'un mois à l'autre, ce qui gonfle r." },
    niveaux: { nom: "Niveaux bruts", aide: "Compare les valeurs telles quelles. Attention : deux séries qui montent toutes les deux depuis 30 ans paraissent liées sans l'être forcément." },
  };
  var AFFICHAGES = { valeurs: "Valeurs réelles", base100: "Base 100", calcul: "Séries du calcul" };
  var UNITE_DECALAGE = { J: ["jour de bourse", "jours de bourse"], S: ["semaine", "semaines"], M: ["mois", "mois"], T: ["trimestre", "trimestres"], A: ["an", "ans"] };

  var etat = null;   // { ids, ref, periode, du, au, mode, affichage, decalages }
  var racine = null;
  var cache = {};    // id|vue → série

  function reglages() { return Object.assign({}, S.REGLAGES_DEFAUT, (D.reglages().comparateur || {})); }

  function etatParDefaut() {
    return { ids: ["C5", "H1"], ref: "C5", periode: "10A", du: null, au: null, mode: "rythmes", affichage: "calcul", decalages: {} };
  }

  function sauver() { O.ecrire("comparateur", etat); }

  /** Ajoute des indicateurs depuis une autre page. */
  function ajouter(ids, options) {
    etat = etat || O.lire("comparateur", null) || etatParDefaut();
    ids.forEach(function (id) { if (etat.ids.indexOf(id) < 0 && etat.ids.length < reglages().max_courbes) etat.ids.push(id); });
    if (!etat.ref || etat.ids.indexOf(etat.ref) < 0) etat.ref = etat.ids[0];
    if (options && options.periode) { etat.periode = options.periode; etat.du = etat.au = null; }
    sauver();
  }

  function appliquerPreparee(p) {
    etat = { ids: [p.reference].concat(p.autres), ref: p.reference, periode: p.periode, du: null, au: null,
      mode: p.mode, affichage: p.affichage || "valeurs", decalages: Object.assign({}, p.decalages || {}) };
    sauver();
    dessiner();
  }

  // ------------------------------------------------------------------ données
  function charger(id, vue) {
    var cle = id + "|" + vue;
    if (cache[cle] !== undefined) return Promise.resolve(cache[cle]);
    return D.serie(id, vue).then(function (s) { cache[cle] = s; return s; });
  }

  function frequenceNative(id) { return D.ind(id).frequence; }

  /** Fréquence de calcul : la plus lente entre celle de la période et celles des séries. */
  function frequenceCalcul(periode, ids, du, au) {
    var f;
    if (du && au) {
      var jours = (S.versTemps(au) - S.versTemps(du)) / G.JOUR;
      var limite = S.versIso(Date.now() - (reglages().recent_mois || 36) * 30.4 * G.JOUR);
      f = du >= limite && jours <= 92 ? "J" : du >= limite && jours <= 731 ? "S" : "M";
    } else {
      f = S.frequencePourPeriode(periode);
    }
    return S.frequenceLaPlusLente([f].concat(ids.map(frequenceNative)));
  }

  function vuePour(f) { return f === "J" || f === "S" ? "native" : "mensuelle"; }

  // ------------------------------------------------------------------ calcul complet
  function calculer(series, f) {
    var r = reglages();
    var ids = etat.ids.filter(function (id) { return series[id]; });
    var grille = S.aligner(ids.map(function (id) { return series[id]; }), f);
    var idxRef = ids.indexOf(etat.ref);
    if (idxRef < 0) idxRef = 0;
    var valsRef = grille.valeurs[idxRef];
    var i1 = -1;
    for (var i = valsRef.length - 1; i >= 0; i--) if (valsRef[i] !== null) { i1 = i; break; }
    if (etat.du && etat.au) {
      var cleAu = S.clePeriode(etat.au, f);
      while (i1 > 0 && grille.dates[i1] > cleAu) i1--;
    }
    if (i1 < 0) return null;
    var debut = etat.du && etat.au ? S.clePeriode(etat.du, f) : S.debutPeriode(grille.dates[i1], etat.periode);
    var i0 = 0;
    if (debut) while (i0 < i1 && grille.dates[i0] < debut) i0++;
    var n = i1 - i0 + 1;
    var transformees = ids.map(function (id, k) { return S.transformer(grille.dates, grille.valeurs[k], D.ind(id).type, etat.mode); });
    var xRef = transformees[idxRef];
    var w = S.fenetreGlissante(f, n, r);
    var kMax = S.decalageMax(f, n, r);
    var resultats = ids.map(function (id, k) {
      if (k === idxRef) return { id: id, ref: true };
      var dec = Math.max(-kMax, Math.min(kMax, etat.decalages[id] || 0));
      var xd = S.decaler(transformees[k], dec);
      var global = S.pearson(xRef.slice(i0, i1 + 1), xd.slice(i0, i1 + 1), r);
      var glissante = w ? S.correlationGlissante(xRef, xd, w, r).slice(i0, i1 + 1) : null;
      return { id: id, decalage: dec, r: global.r, n: global.n, classe: S.classer(global.r, global.n, r), glissante: glissante, indice: k };
    });
    return { ids: ids, grille: grille, transformees: transformees, i0: i0, i1: i1, n: n, f: f, w: w, kMax: kMax, idxRef: idxRef, resultats: resultats };
  }

  // ------------------------------------------------------------------ couleurs
  function couleurClasse(classe) {
    if (!classe || !classe.fiable) return G.couleur("--lien-gris");
    var pale = classe.force === "faible";
    if (classe.sens > 0) return G.couleur(pale ? "--lien-plus-pale" : "--lien-plus");
    return G.couleur(pale ? "--lien-moins-pale" : "--lien-moins");
  }
  function epaisseurClasse(classe) {
    var e = reglages().epaisseurs || { gris: 1.5, faible: 2, modere: 3, fort: 4.5 };
    if (!classe || !classe.fiable) return e.gris;
    return e[classe.force] || e.gris;
  }
  function texteR(res) {
    if (res.r === null || res.r === undefined) return "trop peu de données (" + (res.n || 0) + " points communs, 12 au moins)";
    var c = res.classe;
    var txt = "r = " + O.signe(res.r, 2) + " — " + c.libelle;
    if (c.fiable) txt += ", " + c.sensLibelle;
    return txt + " (" + res.n + " points)";
  }

  // ------------------------------------------------------------------ unités et axes
  function cleUnite(id) {
    var ind = D.ind(id);
    if (etat.affichage === "base100" && ind.type === "N") return "base 100";
    if (etat.affichage === "calcul") {
      if (etat.mode === "mouvements") return ind.type === "N" ? "variation en %" : "variation en points";
      if (etat.mode === "rythmes" && ind.type === "N") return "% sur 12 mois";
    }
    return ind.unite || "";
  }

  function unitesSelection(ids) {
    var u = [];
    ids.forEach(function (id) { var c = cleUnite(id); if (u.indexOf(c) < 0) u.push(c); });
    return u;
  }

  // ------------------------------------------------------------------ page
  function page(conteneur) {
    racine = conteneur;
    etat = etat || O.lire("comparateur", null) || etatParDefaut();
    etat.ids = etat.ids.filter(function (id) { return D.ind(id) && D.carte(id); });
    if (!etat.ids.length) etat = etatParDefaut();
    dessiner();
  }

  function dessiner() {
    if (!racine) return;
    O.vider(racine);
    var r = reglages();
    racine.append(h("h1", { class: "page__titre" }, "Comparateur"),
      h("p", { class: "page__intro" }, "Choisissez jusqu'à " + r.max_courbes + " indicateurs. Les couleurs indiquent s'ils bougent ensemble (vert bleuté), en sens inverse (rouge orangé) ou sans lien fiable (gris), par rapport à l'indicateur de référence ☆. L'épaisseur du trait montre la force du lien."));
    var pretes = h("div", { class: "pretes section", role: "group", "aria-label": "Comparaisons prêtes à l'emploi" });
    (D.catalogue.comparaisons || []).forEach(function (p) {
      pretes.append(h("button", { class: "puce", type: "button", onclick: function () { appliquerPreparee(p); } }, p.libelle));
    });
    racine.append(pretes);
    var grille = h("div", { class: "comparateur section" });
    grille.append(panneauSelection(), h("div", { class: "pile", id: "comparateur-principal" }, h("p", { class: "chargement" }, "Calcul…")));
    racine.append(grille);
    actualiser();
  }

  function panneauSelection() {
    var r = reglages();
    var panneau = h("aside", { class: "selection", "aria-label": "Sélection des indicateurs" });
    var recherche = h("input", { class: "recherche", type: "search", placeholder: "Rechercher un indicateur…", "aria-label": "Rechercher un indicateur" });
    var liste = h("div", { class: "selection__liste" });
    var message = h("p", { class: "aide", role: "status" });
    function remplir() {
      O.vider(liste);
      var q = recherche.value.trim().toLowerCase();
      D.catalogue.familles.forEach(function (fam) {
        var ids = (D.catalogue.ordre || Object.keys(D.catalogue.indicateurs)).filter(function (id) {
          var ind = D.ind(id);
          return ind.famille === fam.id && (!q || (ind.nom + " " + ind.nom_court + " " + id).toLowerCase().indexOf(q) >= 0);
        });
        if (!ids.length) return;
        liste.append(h("div", { class: "selection__famille" }, fam.nom));
        ids.forEach(function (id) {
          var ind = D.ind(id);
          var dispo = Boolean(D.carte(id));
          var coche = etat.ids.indexOf(id) >= 0;
          var idCase = "sel-" + id;
          liste.append(h("div", { class: "selection__item" + (dispo ? "" : " selection__item--nd") },
            h("input", { type: "checkbox", id: idCase, checked: coche, disabled: !dispo, onchange: function (ev) {
              if (ev.target.checked) {
                if (etat.ids.length >= r.max_courbes) { ev.target.checked = false; message.textContent = "Maximum " + r.max_courbes + " courbes : retirez-en une pour en ajouter une autre."; return; }
                var essai = etat.ids.concat([id]);
                if (unitesSelection(essai).length > 3) { ev.target.checked = false; message.textContent = "Trop d'unités différentes : passez en base 100 ou retirez une courbe."; return; }
                etat.ids = essai;
              } else {
                etat.ids = etat.ids.filter(function (x) { return x !== id; });
                delete etat.decalages[id];
              }
              if (etat.ids.indexOf(etat.ref) < 0) etat.ref = etat.ids[0] || null;
              message.textContent = "";
              sauver(); dessiner();
            } }),
            h("label", { for: idCase, title: dispo ? ind.nom : (ind.raison || "non disponible") }, ind.nom_court, dispo ? "" : " (non disponible)"),
            coche ? h("button", { class: "etoile", type: "button", "aria-pressed": String(etat.ref === id), title: "Choisir comme référence",
              "aria-label": "Choisir " + ind.nom_court + " comme référence", onclick: function () { etat.ref = id; sauver(); dessiner(); } }, etat.ref === id ? "★" : "☆") : null));
        });
      });
    }
    recherche.addEventListener("input", remplir);
    remplir();
    panneau.append(h("div", { class: "graphique__titre" }, "Indicateurs (" + etat.ids.length + "/" + r.max_courbes + ")"), recherche, message, liste);
    return panneau;
  }

  function actualiser() {
    var principal = document.getElementById("comparateur-principal");
    if (!principal) return;
    if (!etat.ids.length) { O.vider(principal); principal.append(h("p", { class: "aide" }, "Cochez au moins deux indicateurs dans la liste.")); return; }
    var f = frequenceCalcul(etat.periode, etat.ids, etat.du, etat.au);
    var vues = { native: true, mensuelle: true };
    var promesses = [];
    etat.ids.forEach(function (id) { Object.keys(vues).forEach(function (v) { promesses.push(charger(id, v)); }); });
    Promise.all(promesses).then(function () {
      var series = {};
      etat.ids.forEach(function (id) { var s = cache[id + "|" + vuePour(f)]; if (s && s.dates.length) series[id] = s; });
      var calcul = calculer(series, f);
      O.vider(principal);
      principal.append(blocReglages(f));
      if (!calcul || Object.keys(series).length < 1) { principal.append(h("p", { class: "aide" }, "Données indisponibles pour cette sélection.")); return; }
      principal.append(blocGraphique(calcul, series));
    });
  }

  // ------------------------------------------------------------------ réglages
  function periodesDesactivees() {
    var des = {};
    K.PERIODES.forEach(function (p) {
      if (p === "Max") return;
      var f = frequenceCalcul(p, etat.ids);
      etat.ids.forEach(function (id) {
        var s = cache[id + "|" + vuePour(f)];
        if (!s || !s.dates.length) return;
        var fin = s.dates[s.dates.length - 1];
        var fe = S.frequenceLaPlusLente([f, frequenceNative(id)]);
        if (S.pointsDansPeriode(s, fe, S.debutPeriode(fin, p), fin) < 12) des[p] = "Moins de 12 points pour « " + D.ind(id).nom_court + " » sur cette période";
      });
    });
    return des;
  }

  function segments(options, actuelle, choisir, etiquette, desactives) {
    var g = h("div", { class: "segments", role: "group", "aria-label": etiquette });
    Object.keys(options).forEach(function (cle) {
      var raison = desactives && desactives[cle];
      g.append(h("button", { type: "button", "aria-pressed": String(cle === actuelle), disabled: Boolean(raison), title: raison || "",
        onclick: function () { choisir(cle); } }, options[cle]));
    });
    return g;
  }

  function blocReglages(f) {
    var bloc = h("div", { class: "graphique" });
    var du = h("input", { type: "date", class: "champ", value: etat.du || "", "aria-label": "Date de début" });
    var au = h("input", { type: "date", class: "champ", value: etat.au || "", "aria-label": "Date de fin" });
    var appliquer = h("button", { class: "bouton bouton--petit", type: "button", onclick: function () {
      if (du.value && au.value && du.value < au.value) { etat.du = du.value; etat.au = au.value; sauver(); actualiser(); }
    } }, "Appliquer");
    var periodeActive = etat.du && etat.au ? null : etat.periode;
    bloc.append(h("div", { class: "reglages" },
      h("div", { class: "reglages__groupe" }, h("span", { class: "reglages__etiquette" }, "Période"),
        K.selecteurPeriode(periodeActive, periodesDesactivees(), function (p) { etat.periode = p; etat.du = etat.au = null; sauver(); actualiser(); })),
      h("div", { class: "reglages__groupe" }, h("span", { class: "reglages__etiquette" }, "Ou dates libres"),
        h("div", { class: "actions" }, du, au, appliquer)),
      h("div", { class: "reglages__groupe" }, h("span", { class: "reglages__etiquette" }, "Mode de calcul"),
        segments({ mouvements: "Mouvements", rythmes: "Rythmes annuels", niveaux: "Niveaux bruts" }, etat.mode, function (m) { etat.mode = m; sauver(); actualiser(); }, "Mode de calcul")),
      h("div", { class: "reglages__groupe" }, h("span", { class: "reglages__etiquette" }, "Affichage"),
        segments(AFFICHAGES, etat.affichage, function (a) {
          if (unitesSelection(etat.ids).length > 3 && a !== "base100") return;
          etat.affichage = a; sauver(); actualiser();
        }, "Affichage"))),
      h("label", { class: "case" }, h("input", { type: "checkbox", checked: O.lire("evenements", false), onchange: function (ev) { O.ecrire("evenements", ev.target.checked); actualiser(); } }), "Afficher les grands événements"),
      h("p", { class: "mode-aide" }, h("strong", {}, MODES[etat.mode].nom + " : "), MODES[etat.mode].aide, " ", K.boutonInfo("t:correlation", "corrélation")),
      h("p", { class: "mode-aide" }, "Calcul en données " + ({ J: "quotidiennes", S: "hebdomadaires", M: "mensuelles", T: "trimestrielles", A: "annuelles" })[f] +
        (etat.du && etat.au ? " du " + O.date(etat.du) + " au " + O.date(etat.au) : "") + "."));
    return bloc;
  }

  // ------------------------------------------------------------------ graphique principal
  function blocGraphique(c, series) {
    var r = reglages();
    var bloc = h("div", { class: "graphique" });
    var z = G.zone("Comparaison des indicateurs choisis", "graphique__zone--grand");
    var notes = h("div", {});
    var unites = unitesSelection(c.ids);
    var axesCles = {};
    unites.forEach(function (u, i) { axesCles[u] = ["y", "y1", "y2"][Math.min(2, i)]; });
    var kMaxGrille = Math.max(0, Math.max.apply(null, c.resultats.map(function (x) { return x.decalage || 0; })));
    var dates = S.prolongerGrille(c.grille.dates.slice(0, c.i1 + 1), c.f, kMaxGrille).slice(c.i0);
    var temps = dates.map(S.versTemps);
    var gseries = [];
    var etroit = window.matchMedia && window.matchMedia("(max-width: 619px)").matches;
    c.ids.forEach(function (id, k) {
      var ind = D.ind(id);
      var res = c.resultats[k];
      var dec = res.ref ? 0 : res.decalage;
      var brutes = etat.affichage === "calcul" ? c.transformees[k] : c.grille.valeurs[k];
      var prolongees = brutes.slice(0, c.i1 + 1).concat(new Array(kMaxGrille).fill(null));
      var decalees = S.decaler(prolongees, dec).slice(c.i0);
      if (etat.affichage === "base100" && ind.type === "N") decalees = S.base100(decalees);
      var points = temps.map(function (t, i) { return [t, decalees[i] === undefined ? null : decalees[i]]; });
      var numero = etroit ? String(k + 1) : ind.nom_court + (dec ? " (" + (dec > 0 ? "+" : "−") + Math.abs(dec) + ")" : "");
      var formatV = etat.affichage === "valeurs" ? function (v) { return K.fmtValeur(ind, v); } : function (v) { return O.nombre(v, 2) + (cleUnite(id).indexOf("%") >= 0 ? " %" : ""); };
      if (res.ref) {
        gseries.push({ nom: ind.nom_court + " (référence)", etiquette: (etroit ? numero : "Référence : " + ind.nom_court), points: points, couleur: "--reference", epaisseur: 3.5,
          axe: axesCles[cleUnite(id)], format: formatV, spanMs: false });
        return;
      }
      var couleurGlobale = couleurClasse(res.classe);
      var largeur = epaisseurClasse(res.classe);
      var segment = null;
      if (res.glissante) {
        var gl = res.glissante;
        segment = {
          borderColor: function (ctx) { var x = gl[ctx.p1DataIndex]; return x ? couleurClasse(x.classe) : G.couleur("--lien-gris"); },
          borderWidth: function (ctx) { var x = gl[ctx.p1DataIndex]; return x ? epaisseurClasse(x.classe) : 1.5; },
          borderDash: function (ctx) { var x = gl[ctx.p1DataIndex]; return x ? undefined : [4, 4]; },
        };
      }
      gseries.push({ nom: ind.nom_court, etiquette: numero, points: points, couleur: couleurGlobale, epaisseur: largeur,
        axe: axesCles[cleUnite(id)], format: formatV, segment: segment, spanMs: false });
    });
    var axes = {};
    unites.forEach(function (u, i) { axes[["y", "y1", "y2"][Math.min(2, i)]] = { titre: u, visible: i < 2 }; });
    var evts = O.lire("evenements", false) ? (D.catalogue.evenements || []).map(function (e) { return { t: S.versTemps(e.date), libelle: e.libelle }; }) : [];
    bloc.append(z.conteneur);
    var graphique = null;
    requestAnimationFrame(function () {
      graphique = G.courbes(z.canevas, gseries, { axes: axes, evenements: evts, etiquettesFin: true,
        titreInfobulle: function (t) { return O.dateSelon(S.versIso(t), c.f === "S" ? "J" : c.f); } });
      dessinerBande(bande, c, graphique);
    });
    // Légende avec r, décalage, meilleur décalage
    var legende = h("div", { class: "legende-r" });
    c.ids.forEach(function (id, k) {
      var ind = D.ind(id);
      var res = c.resultats[k];
      var ligne = h("div", { class: "legende-r__ligne", tabindex: "0",
        onmouseenter: function () { surligner(graphique, k); }, onfocus: function () { surligner(graphique, k); },
        onmouseleave: function () { surligner(graphique, null); }, onblur: function () { surligner(graphique, null); } });
      if (res.ref) {
        ligne.append(h("span", { class: "legende-r__trait", style: "border-color: var(--reference); border-top-width: 4px" }),
          h("div", {}, h("div", { class: "legende-r__nom" }, (etroit ? (k + 1) + ". " : "") + ind.nom_court, h("span", { class: "etiquette-ref" }, "☆ Référence"), K.boutonInfo(id, ind.nom_court)),
            h("div", { class: "legende-r__r" }, "Les couleurs des autres courbes se calculent par rapport à elle.")));
      } else {
        var unite = UNITE_DECALAGE[c.f];
        var valeurDec = h("output", {}, texteDecalage(res.decalage, unite));
        var curseur = h("input", { type: "range", min: String(-c.kMax), max: String(c.kMax), step: "1", value: String(res.decalage),
          "aria-label": "Décalage de " + ind.nom_court + " en " + unite[1],
          oninput: function (ev) { valeurDec.textContent = texteDecalage(+ev.target.value, unite); },
          onchange: function (ev) { etat.decalages[id] = +ev.target.value; sauver(); actualiser(); } });
        var resultatDecalage = h("div", {});
        ligne.append(h("span", { class: "legende-r__trait", style: "border-color: " + couleurClasse(res.classe) + "; border-top-width: " + epaisseurClasse(res.classe) + "px" }),
          h("div", {},
            h("div", { class: "legende-r__nom" }, (etroit ? (k + 1) + ". " : "") + ind.nom_court, K.boutonInfo(id, ind.nom_court)),
            h("div", { class: "legende-r__r" }, texteR(res))),
          c.kMax > 0 ? h("div", { class: "legende-r__decalage" }, h("span", {}, "Décalage"), curseur, valeurDec,
            h("button", { class: "bouton bouton--petit", type: "button", disabled: etat.mode === "niveaux",
              title: etat.mode === "niveaux" ? "Indisponible en mode « Niveaux bruts » (résultat trompeur avec des séries à tendance)" : "Tester tous les décalages",
              onclick: function () { meilleurDecalage(c, k, resultatDecalage); } }, "Trouver le meilleur décalage"),
            K.boutonInfo("t:decalage", "décalage")) : null,
          resultatDecalage);
      }
      legende.append(ligne);
    });
    // Bande de corrélation
    var bande = h("div", { class: "bande", "aria-label": "Bande de corrélation dans le temps" });
    bloc.append(legende, bande);
    // Notes
    var zones = new Set(c.ids.map(function (id) { return D.ind(id).zone_horaire; }).filter(Boolean));
    if (c.f === "J" && zones.size > 1) notes.append(h("p", { class: "mode-aide" }, "Ces marchés ne clôturent pas à la même heure (Asie, Europe, Amérique), ce qui affaiblit les corrélations quotidiennes : préférez la vue 1 A (hebdomadaire)."));
    if (!c.w) notes.append(h("p", { class: "mode-aide" }, "Vue quotidienne : pas de corrélation glissante (trop peu de points) ; seul le r global de la période est calculé."));
    if (c.ids.length >= 3) notes.append(matrice(c));
    notes.append(h("p", { class: "rappel" }, "Corrélation ne veut pas dire causalité. ", K.boutonInfo("t:causalite", "corrélation et causalité")),
      h("p", { class: "rappel" }, "Sources : " + Array.from(new Set(c.ids.map(function (id) { return D.ind(id).mention.replace(/^Source : /, ""); }))).join(" ")));
    notes.append(h("div", { class: "actions section" }, h("button", { class: "bouton", type: "button", onclick: function () { exporter(c); } }, "Exporter cette comparaison")));
    bloc.append(notes);
    return bloc;
  }

  function texteDecalage(k, unite) {
    if (!k) return "aucun";
    return (k > 0 ? "+" : "−") + Math.abs(k) + " " + (Math.abs(k) > 1 ? unite[1] : unite[0]) + (k > 0 ? " (précède)" : " (suit)");
  }

  function surligner(graphique, k) {
    if (!graphique) return;
    graphique.data.datasets.forEach(function (jeu, i) {
      if (jeu._largeurInitiale === undefined) jeu._largeurInitiale = jeu.borderWidth;
      jeu.borderWidth = k === null ? jeu._largeurInitiale : (i === k ? jeu._largeurInitiale + 2.5 : Math.max(1, jeu._largeurInitiale * 0.6));
    });
    graphique.update("none");
  }

  // ------------------------------------------------------------------ bande de corrélation
  function dessinerBande(conteneur, c, graphique) {
    O.vider(conteneur);
    var lignes = c.resultats.filter(function (x) { return !x.ref; });
    if (!lignes.length) return;
    conteneur.append(h("div", { class: "graphique__sous" }, c.w ? "Corrélation dans le temps (fenêtre glissante de " + c.w + " points) : vert bleuté = ensemble, rouge orangé = sens inverse, gris = pas de lien fiable." : "Corrélation sur toute la période."));
    lignes.forEach(function (res) {
      var canevas = h("canvas", { height: "14", "aria-hidden": "true" });
      conteneur.append(h("div", { class: "bande__ligne" }, h("span", {}, D.ind(res.id).nom_court), canevas));
      requestAnimationFrame(function () {
        var largeur = canevas.clientWidth || 300;
        canevas.width = largeur;
        var ctx = canevas.getContext("2d");
        var n = c.i1 - c.i0 + 1;
        var gauche = 0, droite = largeur;
        for (var i = 0; i < n; i++) {
          var x0 = gauche + (i / n) * (droite - gauche), x1 = gauche + ((i + 1) / n) * (droite - gauche);
          var cl = res.glissante ? (res.glissante[i] ? res.glissante[i].classe : null) : res.classe;
          ctx.fillStyle = cl ? couleurClasse(cl) : G.couleur("--surface-2");
          ctx.fillRect(Math.floor(x0), 0, Math.ceil(x1 - x0) + 1, 14);
        }
      });
    });
    var d0 = c.grille.dates[c.i0], d1 = c.grille.dates[c.i1];
    conteneur.append(h("div", { class: "bande__echelle" }, h("span", {}, O.date(d0)), h("span", {}, O.date(d1))));
  }

  // ------------------------------------------------------------------ meilleur décalage
  function meilleurDecalage(c, k, zoneResultat) {
    var r = reglages();
    var ref = c.transformees[c.idxRef];
    var res = S.meilleurDecalage(ref, c.transformees[k], -c.kMax, c.kMax, c.i0, c.i1, r);
    var nomInd = D.ind(c.ids[k]).nom_court, nomRef = D.ind(c.ids[c.idxRef]).nom_court;
    var unite = UNITE_DECALAGE[c.f];
    var phrase;
    if (res.annonce) {
      var kk = res.meilleur.k;
      phrase = nomInd + " semble " + (kk > 0 ? "précéder " : "suivre ") + nomRef + " d'environ " + Math.abs(kk) + " " + (Math.abs(kk) > 1 ? unite[1] : unite[0]) +
        " (r = " + O.signe(res.meilleur.r, 2) + ", contre " + (res.sansDecalage.r === null ? "n.d." : O.signe(res.sansDecalage.r, 2)) + " sans décalage). Ce lien statistique ne prouve pas une cause.";
    } else {
      phrase = "Aucun décalage ne ressort nettement" + (res.meilleur ? " (meilleur r = " + O.signe(res.meilleur.r, 2) + " à " + texteDecalage(res.meilleur.k, unite) + ")" : "") + ".";
    }
    O.vider(zoneResultat);
    var z = G.zone("Coefficient r selon le décalage", "graphique__zone--petit");
    zoneResultat.append(h("div", { class: "decalage-resultat" }, h("p", {}, phrase),
      h("p", { class: "aide" }, "En essayant de nombreux décalages, on finit toujours par trouver un chiffre flatteur : regardez si le pic est net ou s'il s'agit d'un plateau."), z.conteneur,
      res.annonce ? h("button", { class: "bouton bouton--petit", type: "button", onclick: function () { etat.decalages[c.ids[k]] = res.meilleur.k; sauver(); actualiser(); } }, "Appliquer ce décalage") : null));
    requestAnimationFrame(function () {
      G.barres(z.canevas, res.courbe.map(function (x) { return String(x.k); }), [{ nom: "r", valeurs: res.courbe.map(function (x) { return x.r; }), couleur: "--serie-1" }],
        { format: function (v) { return O.signe(v, 2); } });
    });
  }

  // ------------------------------------------------------------------ tableau des corrélations
  function matrice(c) {
    var r = reglages();
    var listes = c.transformees.map(function (x) { return x.slice(c.i0, c.i1 + 1); });
    var m = S.matriceCorrelations(listes, r);
    var table = h("table", { class: "matrice" });
    var tete = h("tr", {}, h("th", {}, ""));
    c.ids.forEach(function (id) { tete.append(h("th", { scope: "col" }, D.ind(id).nom_court)); });
    table.append(h("thead", {}, tete));
    var corps = h("tbody", {});
    c.ids.forEach(function (id, i) {
      var tr = h("tr", {}, h("th", { scope: "row" }, D.ind(id).nom_court));
      c.ids.forEach(function (_, j) {
        var x = m[i][j];
        if (i === j) { tr.append(h("td", { class: "case-diag" }, "—")); return; }
        var cl = x.classe;
        var classe = !cl || !cl.fiable ? "case-gris" : (cl.sens > 0 ? (cl.force === "faible" ? "case-plus-pale" : "case-plus") : (cl.force === "faible" ? "case-moins-pale" : "case-moins"));
        tr.append(h("td", { class: classe, title: x.r === null ? "trop peu de données" : (cl.libelle + (cl.fiable ? ", " + cl.sensLibelle : "") + " — " + x.n + " points") },
          x.r === null ? "n.d." : O.signe(x.r, 2)));
      });
      corps.append(tr);
    });
    table.append(corps);
    return h("div", { class: "section" }, h("h3", { class: "graphique__titre" }, "Tableau des corrélations (sans décalage, mode « " + MODES[etat.mode].nom + " »)"),
      h("div", { class: "tableau-zone" }, table));
  }

  // ------------------------------------------------------------------ export
  function exporter(c) {
    var lignes = [];
    var entete = ["Date"];
    c.ids.forEach(function (id, k) {
      var ind = D.ind(id);
      entete.push(ind.nom_court + " (" + (ind.unite || "") + ")");
      entete.push(ind.nom_court + " — " + MODES[etat.mode].nom + (c.resultats[k].decalage ? " (décalé de " + c.resultats[k].decalage + ")" : ""));
    });
    lignes.push(entete.join(";"));
    for (var i = c.i0; i <= c.i1; i++) {
      var ligne = [c.grille.dates[i]];
      c.ids.forEach(function (id, k) {
        ligne.push(O.nombreCsv(c.grille.valeurs[k][i]));
        var dec = c.resultats[k].decalage || 0;
        var src = i - dec;
        ligne.push(O.nombreCsv(src >= 0 && src < c.transformees[k].length ? c.transformees[k][src] : null));
      });
      lignes.push(ligne.join(";"));
    }
    O.telechargerFichier("comparaison_" + c.ids.join("_") + ".csv", "﻿" + lignes.join("\n") + "\n");
    var resume = [
      "Comparaison exportée du tableau de bord des marchés",
      "Période : " + O.date(c.grille.dates[c.i0]) + " → " + O.date(c.grille.dates[c.i1]) + " (données " + ({ J: "quotidiennes", S: "hebdomadaires", M: "mensuelles", T: "trimestrielles", A: "annuelles" })[c.f] + ")",
      "Mode : " + MODES[etat.mode].nom,
      "Référence : " + D.ind(c.ids[c.idxRef]).nom,
    ];
    c.resultats.forEach(function (res) {
      if (res.ref) return;
      resume.push("- " + D.ind(res.id).nom + " : " + texteR(res) + (res.decalage ? ", décalage " + texteDecalage(res.decalage, UNITE_DECALAGE[c.f]) : ""));
      var best = S.meilleurDecalage(c.transformees[c.idxRef], c.transformees[res.indice], -c.kMax, c.kMax, c.i0, c.i1, reglages());
      if (best.meilleur && etat.mode !== "niveaux") resume.push("  meilleur décalage : " + texteDecalage(best.meilleur.k, UNITE_DECALAGE[c.f]) + " (r = " + O.signe(best.meilleur.r, 2) + ")" + (best.annonce ? "" : " — ne ressort pas nettement"));
    });
    resume.push("Rappel : corrélation ne veut pas dire causalité.");
    var texte = resume.join("\n");
    var copie = navigator.clipboard && navigator.clipboard.writeText ? navigator.clipboard.writeText(texte) : Promise.reject();
    copie.then(function () {
      K.ouvrirFeuille("Comparaison exportée", [h("p", {}, "Le fichier CSV est téléchargé et le résumé ci-dessous est copié dans le presse-papiers : collez-le dans une conversation avec Claude."), h("textarea", { class: "zone-texte", readonly: true }, texte)]);
    }, function () {
      K.ouvrirFeuille("Comparaison exportée", [h("p", {}, "Le fichier CSV est téléchargé. Le navigateur a refusé la copie automatique : sélectionnez le texte ci-dessous et copiez-le à la main."), h("textarea", { class: "zone-texte", readonly: true }, texte)]);
    });
  }

  window.Comparateur = { page: page, ajouter: ajouter };
})();
