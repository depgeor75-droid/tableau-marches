/* ==========================================================================
   composants.js — accès aux données (window.Donnees) et composants communs
   (window.Composants) : carte d'indicateur, graphique de famille, sélecteur de
   période, bandeau d'état, panneau de fiche.
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils, S = window.Stats, G = window.Graphiques;
  var h = O.h;

  // ================================================================== données
  var D = {
    get catalogue() { return (window.DONNEES || {}).catalogue || { indicateurs: {}, familles: [], accueil: [], reglages: {} }; },
    get resume() { return (window.DONNEES || {}).resume || { cartes: {} }; },
    get etat() { return (window.DONNEES || {}).etat || { series: {}, comptes: {} }; },
    ind: function (id) { return D.catalogue.indicateurs[id]; },
    carte: function (id) { return D.resume.cartes[id]; },
    etatSerie: function (id) { return D.etat.series[id] || {}; },
    reglages: function () { return D.catalogue.reglages || {}; },

    /** Promesse : { dates, valeurs } de la vue demandée ; null si indisponible.
     *  vue « native » : J/S → fichier récent (36 mois), M/T/A → historique.
     *  vue « mensuelle » : historique (fin de mois) + point provisoire du mois en cours. */
    serie: function (id, vue) {
      var ind = D.ind(id);
      if (!ind) return Promise.resolve(null);
      var natif = ind.frequence === "J" || ind.frequence === "S";
      var genre = vue === "native" && natif ? "recent" : "historique";
      return O.charger(ind.fichier + "_" + genre).then(function (fichier) {
        var s = fichier && fichier[id];
        if (!s) return null;
        var copie = { dates: s.dates.slice(), valeurs: s.valeurs.slice(), provisoire: null };
        if (vue === "mensuelle" && natif) {
          var c = D.carte(id);
          var dernierMois = copie.dates.length ? copie.dates[copie.dates.length - 1].slice(0, 7) : "";
          if (c && c.date && c.date.slice(0, 7) > dernierMois) {
            copie.dates.push(c.date.slice(0, 7) + "-01");
            copie.valeurs.push(c.valeur);
            copie.provisoire = copie.dates.length - 1;
          }
        }
        return copie;
      });
    },
  };

  // ================================================================== formats
  function fmtValeur(ind, v) {
    return O.valeur({ unite: ind.unite, decimales_affichage: ind.decimales }, v);
  }

  function fmtVariation(ind, v) { return O.variation(ind, v); }

  function nomFrequence(f) { return O.LIBELLES_FREQUENCE[f] || ""; }

  function dateCarte(ind, iso) { return O.dateSelon(iso, ind.frequence); }

  function libellePercentile(p, ind) {
    if (!p) return "";
    if (p.valeur === null || p.valeur === undefined) return "historique trop court pour situer la valeur";
    var texte = (p.base === "variation_12m" ? "variation sur 1 an : " : "") + O.rangOrdinal(p.valeur) + " percentile depuis " + p.depuis + " — " + p.libelle;
    if (p.court) texte += " (historique court)";
    return texte;
  }

  function texteNote(note) {
    if (!note) return "";
    var morceaux = note.split(":");
    if (morceaux[0] === "ga_base_manquante") {
      return "Dernier glissement calculable. Pour " + O.moisLong(morceaux[1] + "-01") +
        ", il n'existe pas de chiffre un an plus tôt (mois non publié aux États-Unis en octobre 2025, fermeture des services fédéraux).";
    }
    if (morceaux[0] === "ga_valeur_manquante") return "Mois de " + O.moisLong(morceaux[1] + "-01") + " non publié.";
    return "";
  }

  // ================================================================== feuille (panneau)
  var feuille = function () { return document.getElementById("feuille"); };

  function ouvrirFeuille(titre, contenu) {
    var f = feuille();
    O.vider(f);
    f.append(
      h("div", { class: "feuille__tete" },
        h("h2", { class: "feuille__titre", id: "feuille-titre" }, titre),
        h("button", { class: "feuille__fermer", type: "button", "aria-label": "Fermer", onclick: fermerFeuille }, "×")),
      h("div", { class: "feuille__corps" }, contenu));
    if (!f.open) { try { f.showModal(); } catch (e) { f.setAttribute("open", ""); } }
    f.onclick = function (ev) { if (ev.target === f) fermerFeuille(); };
  }

  function fermerFeuille() {
    var f = feuille();
    if (f.open) { try { f.close(); } catch (e) { f.removeAttribute("open"); } }
  }

  // ------------------------------------------------------------ fiches (chargées au premier clic)
  var chargementFiches = null;
  function chargerFiches() {
    if (window.FICHES) return Promise.resolve(window.FICHES);
    if (chargementFiches) return chargementFiches;
    chargementFiches = new Promise(function (ok) {
      var s = document.createElement("script");
      s.src = "js/fiches.js";
      s.onload = function () { ok(window.FICHES || {}); };
      s.onerror = function () { chargementFiches = null; ok({}); };
      document.head.append(s);
    });
    return chargementFiches;
  }

  /** Ouvre la fiche d'un indicateur (id du catalogue) ou d'une notion transversale (« t:base100 »). */
  function ouvrirFiche(id) {
    chargerFiches().then(function (fiches) {
      var ind = D.ind(id);
      var cle = ind ? ind.fiche : id;
      var fiche = fiches[cle] || fiches[id];
      var corps = [];
      if (fiche && window.Fiches) {
        corps.push(window.Fiches.rendre(fiche, ind, id));
      } else if (ind) {
        corps.push(h("p", { class: "aide" }, "La fiche explicative de cet indicateur sera ajoutée prochainement."));
      } else {
        corps.push(h("p", { class: "aide" }, "Fiche introuvable."));
      }
      if (ind) corps.push(piedFiche(ind, id));
      else {
        var jeux = D.catalogue.jeux || {};
        Object.keys(jeux).forEach(function (j) {
          if (jeux[j].fiche === cle) {
            var e = (D.etat.jeux || {})[j] || {};
            corps.push(h("p", { class: "fiche__pied" }, jeux[j].nom + " · " + jeux[j].mention + (e.date ? " · Dernière enquête ou édition : " + O.date(e.date) : "") + "."));
          }
        });
      }
      ouvrirFeuille(fiche ? fiche.titre : (ind ? ind.nom : "Fiche"), corps);
    });
  }

  function piedFiche(ind, id) {
    var e = D.etatSerie(id);
    var texte = nomFrequence(ind.frequence).replace(/^./, function (c) { return c.toUpperCase(); }) + " · " + (ind.mention || ind.source) +
      (ind.debut ? " · Depuis " + O.dateSelon(ind.debut, ind.frequence === "J" || ind.frequence === "S" ? "M" : ind.frequence) : "") +
      (e.date ? " · Dernière valeur : " + O.dateSelon(e.date, ind.frequence) : "") + ".";
    var pied = h("p", { class: "fiche__pied" }, texte);
    if (ind.particularite) pied.append(" " + "Particularité : " + ind.particularite + ".");
    return pied;
  }

  function boutonInfo(id, nom) {
    return h("button", { class: "info", type: "button", "aria-label": "Fiche explicative : " + (nom || id),
      title: "Fiche explicative", onclick: function (ev) { ev.stopPropagation(); ouvrirFiche(id); } }, "ⓘ");
  }

  // ================================================================== carte
  function pastilleEtat(id) {
    var e = D.etatSerie(id);
    if (e.statut === "en_retard") return h("span", { class: "pastille", title: e.message || "" }, "en retard");
    if (e.statut === "erreur") return h("span", { class: "pastille pastille--erreur", title: e.message || "" }, "source en panne");
    if (e.statut === "secours") return h("span", { class: "pastille pastille--neutre", title: e.message || "" }, "source de secours");
    return null;
  }

  function carte(id) {
    var ind = D.ind(id);
    if (!ind) return null;
    var c = D.carte(id);
    var e = D.etatSerie(id);
    var noeud = h("article", { class: "carte-ind" + (c ? "" : " carte-ind--nd"), "data-id": id });
    noeud.append(h("div", { class: "carte-ind__tete" },
      h("h3", { class: "carte-ind__nom" }, ind.nom_court, boutonInfo(id, ind.nom_court)),
      pastilleEtat(id)));
    if (!c) {
      noeud.append(h("div", { class: "carte-ind__valeur" }, "non disponible"),
        h("p", { class: "carte-ind__position" }, ind.raison || e.message || "Donnée non disponible pour le moment."));
      return noeud;
    }
    var dateTxt = dateCarte(ind, c.date);
    if (ind.frequence !== "J") dateTxt += " · " + (O.PUBLICATION[ind.frequence] || "");
    if (c.provisoire_depuis) dateTxt += " · provisoire";
    noeud.append(h("div", { class: "carte-ind__ligne" },
      h("span", { class: "carte-ind__valeur chiffres" }, fmtValeur(ind, c.valeur)),
      h("span", { class: "carte-ind__date" }, dateTxt)));
    var variations = h("div", { class: "carte-ind__variations chiffres" });
    if (ind.frequence !== "T" && ind.frequence !== "A") {
      variations.append(h("span", { title: "Variation sur 1 mois" }, h("span", { class: "fleche", "aria-hidden": "true" }, O.fleche(c.var_1m)), " ", fmtVariation(ind, c.var_1m), h("span", {}, " 1 mois")));
    }
    variations.append(h("span", { title: "Variation sur 1 an" }, h("span", { class: "fleche", "aria-hidden": "true" }, O.fleche(c.var_1a)), " ", fmtVariation(ind, c.var_1a), h("span", {}, " 1 an")));
    noeud.append(variations);
    if (c.mini) noeud.append(G.mini(c.mini.valeurs, "Évolution sur " + c.mini.duree + " de " + ind.nom_court));
    var pos = libellePercentile(c.percentile, ind);
    if (pos) noeud.append(h("p", { class: "carte-ind__position" }, "Position : " + pos));
    var note = texteNote(c.note);
    if (note) noeud.append(h("p", { class: "carte-ind__note" }, note));
    noeud.append(h("div", { class: "carte-ind__pied" },
      h("span", { class: "carte-ind__date" }, c.mini ? "Mini-courbe : " + c.mini.duree : ""),
      h("button", { class: "bouton bouton--petit", type: "button", onclick: function () { window.App.comparer([id]); },
        title: "Ajouter au comparateur" }, "＋ Comparer")));
    return noeud;
  }

  function grilleCartes(ids) {
    return h("div", { class: "cartes" }, ids.map(carte));
  }

  // ================================================================== bandeau d'état
  function bandeauEtat() {
    var etat = D.etat;
    var comptes = etat.comptes || {};
    var retard = (comptes.en_retard || 0) + (comptes.erreur || 0);
    return h("div", { class: "bandeau-etat" },
      h("span", {}, "Données mises à jour le " + O.dateHeure(etat.genere_le) + " (heure belge)"),
      retard ? h("a", { href: "#/etat" }, retard + (retard > 1 ? " séries en retard ou en panne" : " série en retard ou en panne")) :
        h("a", { href: "#/etat" }, "Toutes les séries sont à jour"));
  }

  // ================================================================== sélecteur de période
  var PERIODES = ["1M", "1A", "5A", "10A", "30A", "Max"];
  var LIBELLES_PERIODE = { "1M": "1 M", "1A": "1 A", "5A": "5 A", "10A": "10 A", "30A": "30 A", "Max": "Max" };
  var NOMS_PERIODE = { "1M": "1 mois", "1A": "1 an", "5A": "5 ans", "10A": "10 ans", "30A": "30 ans", "Max": "tout l'historique" };

  /** desactivees : { periode: raison } */
  function selecteurPeriode(actuelle, desactivees, choisir) {
    var groupe = h("div", { class: "segments", role: "group", "aria-label": "Période affichée" });
    PERIODES.forEach(function (p) {
      var raison = desactivees && desactivees[p];
      groupe.append(h("button", {
        type: "button", "aria-pressed": String(p === actuelle), disabled: Boolean(raison),
        title: raison || ("Afficher " + NOMS_PERIODE[p]), "aria-label": NOMS_PERIODE[p] + (raison ? " (indisponible : " + raison + ")" : ""),
        onclick: function () { choisir(p); },
      }, LIBELLES_PERIODE[p]));
    });
    return groupe;
  }

  /** Fréquence d'affichage d'une période pour un graphique de famille. */
  function vuePourPeriode(p) { return p === "1M" || p === "1A" ? "native" : "mensuelle"; }

  function debutPeriode(p, finIso) { return S.debutPeriode(finIso, p); }

  // ================================================================== graphique de famille
  /**
   * ids : séries proposées ; coches : séries cochées au départ.
   * options : { titre, id (clé de mémoire), periode }
   */
  function graphiqueFamille(ids, options) {
    options = options || {};
    var cleMemoire = "famille." + (options.id || ids.join("_"));
    var memoire = O.lire(cleMemoire, {});
    var disponibles = ids.filter(function (id) { return D.ind(id) && D.carte(id); });
    var coches = new Set((memoire.coches || options.coches || disponibles.slice(0, 4)).filter(function (id) { return disponibles.indexOf(id) >= 0; }));
    while (coches.size > 1 && nombreAxes(Array.from(coches)) > 3) coches.delete(Array.from(coches).pop());
    var periode = memoire.periode || options.periode || "10A";
    var evenementsVisibles = O.lire("evenements", false);
    var bloc = h("section", { class: "graphique section" });
    var tete = h("div", { class: "graphique__tete" });
    var legende = h("div", { class: "legende-cases" });
    var avis = h("p", { class: "aide", role: "status" });
    var z = G.zone("Graphique : " + (options.titre || "séries de la famille"), "graphique__zone--grand");
    var pied = h("div", { class: "graphique__options" });
    var sources = h("p", { class: "rappel" });
    bloc.append(tete, legende, avis, z.conteneur, pied, sources);
    if (!disponibles.length) {
      tete.append(h("h3", { class: "graphique__titre" }, options.titre || ""));
      G.message(z.conteneur, "Aucune donnée disponible pour ces séries.");
      return bloc;
    }
    var donnees = {};

    function memoriser() { O.ecrire(cleMemoire, { coches: Array.from(coches), periode: periode }); }

    function dessinerLegende() {
      O.vider(legende);
      disponibles.forEach(function (id, rang) {
        var ind = D.ind(id);
        var caseNode = h("input", { type: "checkbox", checked: coches.has(id), onchange: function (ev) {
          if (ev.target.checked) {
            var essai = Array.from(coches).concat([id]);
            if (nombreAxes(essai) > 3) { ev.target.checked = false; avis.textContent = "Trop d'unités différentes (3 axes au plus) : décochez une courbe avant d'en ajouter une autre."; return; }
            coches.add(id);
          } else coches.delete(id);
          avis.textContent = "";
          memoriser(); actualiser();
        } });
        legende.append(h("label", {}, caseNode,
          h("span", { class: "legende__trait", style: "border-color: var(" + couleurRang(rang) + ")" }),
          ind.nom_court, boutonInfo(id, ind.nom_court)));
      });
    }

    function couleurRang(rang) { return "--fam-" + ((rang % 8) + 1); }  // jamais de vert ni de rouge (réservés aux corrélations)

    /** Clé d'axe : même unité → même axe, sauf les indices centrés (N*), qui ont chacun leur axe. */
    function cleAxe(id) { var ind = D.ind(id); return ind.type === "N*" ? (ind.unite || "") + " | " + ind.nom_court : (ind.unite || ""); }
    function nombreAxes(ids) { var s = {}; ids.forEach(function (id) { s[cleAxe(id)] = true; }); return Object.keys(s).length; }

    function actualiser() {
      var choisis = disponibles.filter(function (id) { return coches.has(id); });
      var vueNative = vuePourPeriode(periode) === "native";
      Promise.all(choisis.map(function (id) {
        var cle = id + (vueNative ? "|n" : "|m");
        if (donnees[cle]) return Promise.resolve(donnees[cle]);
        return D.serie(id, vueNative ? "native" : "mensuelle").then(function (s) { donnees[cle] = s; return s; });
      })).then(function (liste) {
        var series = [];
        choisis.forEach(function (id, i) { if (liste[i] && liste[i].dates.length) series.push({ id: id, s: liste[i] }); });
        var fin = series.reduce(function (m, x) { var d = x.s.dates[x.s.dates.length - 1]; return d > m ? d : m; }, "0000");
        // périodes indisponibles : la série cochée la moins fournie aurait moins de 12 points
        var desactivees = {};
        PERIODES.forEach(function (p) {
          if (p === "Max" || !series.length) return;
          var vn = vuePourPeriode(p) === "native";
          var debut = debutPeriode(p, fin);
          series.forEach(function (x) {
            var ind = D.ind(x.id);
            var raison = "Moins de 12 points pour « " + ind.nom_court + " » sur cette période";
            if (ind.frequence === "M" || ind.frequence === "T" || ind.frequence === "A") {
              // même fichier (historique) dans les deux vues : le compte est toujours possible
              if (S.pointsDansPeriode(x.s, ind.frequence, debut, fin) < 12) desactivees[p] = raison;
            } else if (ind.frequence === "S" && p === "1M") {
              desactivees[p] = raison; // une série hebdomadaire n'a que 4 ou 5 points sur un mois
            } else if (vn === vueNative && S.pointsDansPeriode(x.s, vn ? ind.frequence : "M", debut, fin) < 12) {
              desactivees[p] = raison;
            }
          });
        });
        O.vider(tete);
        tete.append(
          h("div", {}, h("h3", { class: "graphique__titre" }, options.titre || ""), h("p", { class: "graphique__sous" }, "Cochez les séries à afficher.")),
          selecteurPeriode(periode, desactivees, function (p) { periode = p; memoriser(); actualiser(); }));
        dessinerGraphique(series, fin);
        O.vider(pied);
        pied.append(
          h("label", { class: "case" }, h("input", { type: "checkbox", checked: evenementsVisibles, onchange: function (ev) {
            evenementsVisibles = ev.target.checked; O.ecrire("evenements", evenementsVisibles); actualiser();
          } }), "Afficher les grands événements"),
          h("button", { class: "bouton bouton--petit", type: "button", disabled: !series.length,
            onclick: function () { window.App.comparer(series.map(function (x) { return x.id; }), { periode: periode }); } }, "Ouvrir dans le comparateur"));
        sources.textContent = series.length ? "Sources : " + Array.from(new Set(series.map(function (x) { return D.ind(x.id).mention.replace(/^Source : /, ""); }))).join(" ") : "";
      });
    }

    function dessinerGraphique(series, fin) {
      if (!series.length) { G.message(z.conteneur, "Cochez au moins une série."); var g = window.Chart && window.Chart.getChart(z.canevas); if (g) g.destroy(); return; }
      G.message(z.conteneur, null);
      var debut = debutPeriode(periode, fin);
      var unites = [];
      var reglages = D.reglages().graphiques || { trou_max_jours: {} };
      var gs = series.map(function (x) {
        var ind = D.ind(x.id);
        var unite = cleAxe(x.id);
        if (unites.indexOf(unite) < 0) unites.push(unite);
        var points = [];
        for (var i = 0; i < x.s.dates.length; i++) {
          var d = x.s.dates[i];
          var cle = ind.frequence === "J" || ind.frequence === "S" ? (vuePourPeriode(periode) === "native" ? d : S.clePeriode(d, "M")) : S.clePeriode(d, ind.frequence === "M" ? "M" : ind.frequence);
          if (debut && cle < debut) continue;
          points.push([S.versTemps(cle), x.s.valeurs[i]]);
        }
        var freqAffichee = vuePourPeriode(periode) === "native" ? ind.frequence : (ind.frequence === "T" || ind.frequence === "A" ? ind.frequence : "M");
        var rang = disponibles.indexOf(x.id);
        return {
          nom: ind.nom_court, points: points, couleur: couleurRang(rang), axe: ["y", "y1", "y2"][Math.min(2, unites.indexOf(unite))],
          spanMs: (reglages.trou_max_jours[freqAffichee] || 45) * G.JOUR,
          format: function (v) { return fmtValeur(ind, v); }, creuxDernier: x.s.provisoire !== null && x.s.provisoire !== undefined,
        };
      });
      var axes = {};
      unites.slice(0, 3).forEach(function (u, i) { axes[["y", "y1", "y2"][i]] = { titre: u.split(" | ").pop() }; });
      var evts = evenementsVisibles ? (D.catalogue.evenements || []).map(function (e) { return { t: S.versTemps(e.date), libelle: e.libelle }; }) : [];
      G.courbes(z.canevas, gs, { axes: axes, evenements: evts, min: debut ? S.versTemps(debut) : undefined });
    }

    dessinerLegende();
    actualiser();
    return bloc;
  }

  window.Donnees = D;
  window.Composants = {
    carte: carte, grilleCartes: grilleCartes, bandeauEtat: bandeauEtat, selecteurPeriode: selecteurPeriode,
    graphiqueFamille: graphiqueFamille, ouvrirFiche: ouvrirFiche, ouvrirFeuille: ouvrirFeuille, fermerFeuille: fermerFeuille,
    boutonInfo: boutonInfo, fmtValeur: fmtValeur, fmtVariation: fmtVariation, libellePercentile: libellePercentile,
    PERIODES: PERIODES, NOMS_PERIODE: NOMS_PERIODE, chargerFiches: chargerFiches, pastilleEtat: pastilleEtat,
  };
})();
