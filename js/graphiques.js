/* ==========================================================================
   graphiques.js — courbes (Chart.js 4, copié dans lib/) et mini-courbes SVG.
   Style repris d'Aedifica : traits fins, grille discrète, réticule + info-bulle,
   jamais de texte dans la couleur d'une série. Axe du temps linéaire (millisecondes)
   avec graduations maison : pas d'adaptateur de dates.
   Un trou reste un trou : pas de spanGaps global, une durée maximale par série
   (un week-end ne coupe pas la courbe, un mois manquant la coupe).
   ========================================================================== */
(function () {
  "use strict";
  var O = window.Outils;
  var JOUR = 86400000;
  var MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  var actifs = [];

  function disponible() { return typeof window.Chart !== "undefined"; }

  function couleur(nom) {
    return getComputedStyle(document.documentElement).getPropertyValue(nom).trim() || nom;
  }

  function teintes() {
    return { surface: couleur("--surface"), encre: couleur("--encre"), encre2: couleur("--encre-2"), muet: couleur("--muet"),
      filet: couleur("--filet"), axe: couleur("--axe"), accent: couleur("--accent") };
  }

  function lavis(hex, opacite) {
    if (!hex || hex[0] !== "#") return hex;
    var n = parseInt(hex.slice(1), 16);
    return "rgba(" + ((n >> 16) & 255) + ", " + ((n >> 8) & 255) + ", " + (n & 255) + ", " + opacite + ")";
  }

  /** Détruit les graphiques dont le canevas a quitté la page. */
  function nettoyer() {
    actifs = actifs.filter(function (g) {
      if (!g.canvas || !g.canvas.isConnected) { g.destroy(); return false; }
      return true;
    });
  }

  // ----------------------------------------------------------- axe du temps
  function graduations(min, max, largeur) {
    var jours = (max - min) / JOUR;
    var valeurs = [];
    var etroit = largeur < 520;
    if (jours <= 75) {
      var pas = jours <= 40 ? 7 : 14;
      for (var t = max; t >= min; t -= pas * JOUR) valeurs.push(t);
      return { valeurs: valeurs.reverse(), libelle: function (v) { var d = new Date(v); return d.getUTCDate() + " " + MOIS_COURTS[d.getUTCMonth()]; } };
    }
    var debut = new Date(min);
    if (jours <= 800) {
      var pasMois = jours <= 430 ? (etroit ? 3 : 2) : 6;
      var c = new Date(Date.UTC(debut.getUTCFullYear(), debut.getUTCMonth() + 1, 1));
      while (c.getTime() <= max) {
        if (c.getUTCMonth() % pasMois === 0) valeurs.push(c.getTime());
        c.setUTCMonth(c.getUTCMonth() + 1);
      }
      return { valeurs: valeurs, libelle: function (v) { var d = new Date(v); return MOIS_COURTS[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2); } };
    }
    var annees = jours / 365.25;
    var pasA = annees <= 6 ? 1 : annees <= 12 ? (etroit ? 2 : 1) : annees <= 25 ? (etroit ? 5 : 2) : (etroit ? 10 : 5);
    for (var a = debut.getUTCFullYear() + 1; Date.UTC(a, 0, 1) <= max; a++) {
      if (a % pasA === 0) valeurs.push(Date.UTC(a, 0, 1));
    }
    return { valeurs: valeurs, libelle: function (v) { return String(new Date(v).getUTCFullYear()); } };
  }

  // ---------------------------------------------------------------- greffons
  var reticule = {
    id: "reticule",
    afterDatasetsDraw: function (g) {
      var el = g.tooltip && g.tooltip.getActiveElements ? g.tooltip.getActiveElements() : [];
      if (!el.length) return;
      var ctx = g.ctx, zone = g.chartArea;
      ctx.save();
      ctx.strokeStyle = teintes().axe;
      ctx.lineWidth = 1;
      ctx.beginPath();
      var x = Math.round(el[0].element.x) + 0.5;
      ctx.moveTo(x, zone.top); ctx.lineTo(x, zone.bottom); ctx.stroke();
      ctx.restore();
    },
  };

  /** Lignes verticales des grands événements, avec libellé court. */
  var evenements = {
    id: "evenements",
    afterDatasetsDraw: function (g, _a, opts) {
      var liste = (opts && opts.liste) || [];
      if (!liste.length) return;
      var ctx = g.ctx, zone = g.chartArea, x = g.scales.x, t = teintes();
      ctx.save();
      ctx.font = "600 10px system-ui, sans-serif";
      var derniere = -1e9, rang = 0;
      liste.forEach(function (e) {
        if (e.t < x.min || e.t > x.max) return;
        var px = Math.round(x.getPixelForValue(e.t)) + 0.5;
        ctx.strokeStyle = t.muet;
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(px, zone.top); ctx.lineTo(px, zone.bottom); ctx.stroke();
        ctx.setLineDash([]);
        rang = px - derniere < 90 ? rang + 1 : 0;
        derniere = px;
        var texte = e.libelle.length > 22 ? e.libelle.slice(0, 21) + "…" : e.libelle;
        var largeur = ctx.measureText(texte).width + 8;
        var gauche = Math.min(px + 3, zone.right - largeur);
        var haut = zone.top + 2 + (rang % 3) * 15;
        ctx.fillStyle = t.surface; ctx.globalAlpha = 0.9;
        ctx.fillRect(gauche, haut, largeur, 13);
        ctx.globalAlpha = 1; ctx.fillStyle = t.encre2;
        ctx.textBaseline = "top";
        ctx.fillText(texte, gauche + 4, haut + 2);
      });
      ctx.restore();
    },
  };

  /** Nom court en bout de trait (reconnaître les courbes sans dépendre de la couleur). */
  var etiquettesFin = {
    id: "etiquettesFin",
    afterDatasetsDraw: function (g, _a, opts) {
      if (!opts || !opts.actif) return;
      var ctx = g.ctx, t = teintes(), occupes = [];
      ctx.save();
      ctx.font = "600 11px system-ui, sans-serif";
      ctx.textBaseline = "middle";
      g.data.datasets.forEach(function (jeu, i) {
        var meta = g.getDatasetMeta(i);
        if (meta.hidden || !jeu.etiquette) return;
        var pts = meta.data;
        for (var k = pts.length - 1; k >= 0; k--) {
          if (jeu.data[k] && jeu.data[k].y !== null && !isNaN(pts[k].y)) {
            var y = pts[k].y - 12;
            occupes.forEach(function (o) { if (Math.abs(o - y) < 15) y = o - 15; });
            if (y < g.chartArea.top + 8) y = pts[k].y + 14;
            occupes.push(y);
            var largeur = ctx.measureText(jeu.etiquette).width + 8;
            var xx = Math.max(g.chartArea.left, Math.min(pts[k].x - largeur / 2, g.chartArea.right - largeur));
            ctx.fillStyle = t.surface; ctx.globalAlpha = 0.92;
            ctx.fillRect(xx, y - 8, largeur, 16);
            ctx.globalAlpha = 1; ctx.fillStyle = t.encre;
            ctx.fillText(jeu.etiquette, xx + 4, y);
            break;
          }
        }
      });
      ctx.restore();
    },
  };

  function monter(canevas, configuration) {
    var existant = window.Chart.getChart(canevas);
    if (existant) existant.destroy();
    var g = new window.Chart(canevas, configuration);
    actifs.push(g);
    return g;
  }

  function axeValeurs(t, reglage, position, visible) {
    reglage = reglage || {};
    return {
      position: position, display: visible !== false, grace: "6%",
      border: { display: false },
      grid: { color: position === "left" ? t.filet : "transparent", drawTicks: false },
      ticks: { color: t.encre2, font: { size: 11 }, padding: 6, maxTicksLimit: 6,
        callback: function (v) { return reglage.format ? reglage.format(v) : O.nombre(v, Math.abs(v) >= 100 ? 0 : 1); } },
      title: reglage.titre ? { display: true, text: reglage.titre, color: t.encre2, font: { size: 11, weight: "600" } } : { display: false },
    };
  }

  /**
   * Courbes dans le temps.
   * series : [{ nom, etiquette, points: [[t, v|null]], couleur (variable CSS ou #hex), epaisseur, axe,
   *             format(v), spanMs, pointille, segment, creuxDernier (point provisoire), cache }]
   * options : { axes: {y: {titre, format}, y1: …, y2: …}, evenements: [{t, libelle}], etiquettesFin, min, max,
   *             survolLegende }
   */
  function courbes(canevas, series, options) {
    if (!disponible()) return null;
    options = options || {};
    var t = teintes();
    var tous = [];
    series.forEach(function (s) { s.points.forEach(function (p) { if (p[1] !== null) tous.push(p[0]); }); });
    if (!tous.length) return null;
    var min = options.min !== undefined ? options.min : Math.min.apply(null, tous);
    var max = options.max !== undefined ? options.max : Math.max.apply(null, tous);
    if (max === min) max = min + JOUR;
    var largeur = (canevas.parentElement && canevas.parentElement.clientWidth) || 360;
    var echelle = graduations(min, max, largeur);
    var jeux = series.map(function (s, rang) {
      var teinte = couleur(s.couleur || "--fam-" + ((rang % 8) + 1));
      var dernier = -1;
      for (var k = s.points.length - 1; k >= 0; k--) if (s.points[k][1] !== null) { dernier = k; break; }
      var jeu = {
        label: s.nom, etiquette: s.etiquette, format: s.format,
        data: s.points.map(function (p) { return { x: p[0], y: p[1] }; }),
        yAxisID: s.axe || "y", hidden: Boolean(s.cache),
        borderColor: teinte, backgroundColor: teinte, borderWidth: s.epaisseur || 2,
        borderDash: s.pointille ? [5, 4] : undefined,
        borderJoinStyle: "round", borderCapStyle: "round", tension: 0,
        spanGaps: s.spanMs || false,
        pointRadius: function (c) { return c.dataIndex === dernier ? 3.5 : 0; },
        pointBackgroundColor: function (c) { return c.dataIndex === dernier && s.creuxDernier ? t.surface : teinte; },
        pointBorderColor: teinte, pointBorderWidth: 2, pointHoverRadius: 4, pointHitRadius: 10,
        fill: false,
      };
      if (s.segment) jeu.segment = s.segment;
      return jeu;
    });
    var axes = options.axes || { y: {} };
    var echelles = {
      x: {
        type: "linear", min: min, max: max,
        border: { color: t.axe }, grid: { display: false },
        afterBuildTicks: function (axe) { axe.ticks = echelle.valeurs.map(function (v) { return { value: v }; }); },
        ticks: { color: t.encre2, font: { size: 11 }, maxRotation: 0, autoSkip: false, callback: function (v) { return echelle.libelle(v); } },
      },
    };
    var positions = { y: "left", y1: "right", y2: "right" };
    Object.keys(axes).forEach(function (cle) {
      echelles[cle] = axeValeurs(t, axes[cle], positions[cle] || "right", axes[cle].visible);
    });
    return monter(canevas, {
      type: "line",
      data: { datasets: jeux },
      plugins: [reticule, evenements, etiquettesFin],
      options: {
        responsive: true, maintainAspectRatio: false, animation: false, parsing: false, normalized: true,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        layout: { padding: { right: 4 } },
        scales: echelles,
        plugins: {
          legend: { display: false },
          evenements: { liste: options.evenements || [] },
          etiquettesFin: { actif: Boolean(options.etiquettesFin) },
          tooltip: {
            backgroundColor: t.encre, titleColor: t.surface, bodyColor: t.surface,
            titleFont: { weight: "600", size: 12 }, bodyFont: { size: 13 }, padding: 10, cornerRadius: 8,
            usePointStyle: true, boxWidth: 14, boxHeight: 2, boxPadding: 6,
            filter: function (el) { return el.parsed.y !== null; },
            callbacks: {
              title: function (el) { return el.length ? (options.titreInfobulle ? options.titreInfobulle(el[0].parsed.x) : O.date(new Date(el[0].parsed.x).toISOString())) : ""; },
              label: function (el) {
                var f = el.dataset.format || function (v) { return O.nombre(v, 2); };
                return " " + f(el.parsed.y) + "  " + el.dataset.label;
              },
              labelPointStyle: function () { return { pointStyle: "line", rotation: 0 }; },
            },
          },
        },
      },
    });
  }

  /** Barres simples (catégories). */
  function barres(canevas, categories, series, options) {
    if (!disponible()) return null;
    options = options || {};
    var t = teintes();
    var format = options.format || function (v) { return O.nombre(v, 1); };
    return monter(canevas, {
      type: "bar",
      data: { labels: categories, datasets: series.map(function (s, rang) {
        var teinte = couleur(s.couleur || "--fam-" + ((rang % 8) + 1));
        return { label: s.nom, data: s.valeurs, backgroundColor: teinte, maxBarThickness: 26, borderRadius: 4, categoryPercentage: 0.7, barPercentage: 0.9 };
      }) },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false, indexAxis: options.horizontal ? "y" : "x",
        scales: {
          x: options.horizontal ? axeValeurs(t, { format: format }, "bottom") : { border: { color: t.axe }, grid: { display: false }, ticks: { color: t.encre2, font: { size: 11 }, maxRotation: 0, autoSkip: false } },
          y: options.horizontal ? { border: { color: t.axe }, grid: { display: false }, ticks: { color: t.encre2, font: { size: 11 } } } : Object.assign(axeValeurs(t, { format: format }, "left"), { beginAtZero: true }),
        },
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: t.encre, titleColor: t.surface, bodyColor: t.surface, padding: 10, cornerRadius: 8,
            callbacks: { label: function (el) { return " " + format(options.horizontal ? el.parsed.x : el.parsed.y) + "  " + el.dataset.label; } } },
        },
      },
    });
  }

  /** Mini-courbe SVG (sans Chart.js) : les trous coupent le tracé. */
  function mini(valeurs, etiquette) {
    var vals = valeurs || [];
    var nombres = vals.filter(O.estNombre);
    var s = O.svg("svg", { class: "carte-ind__mini", viewBox: "0 0 100 30", preserveAspectRatio: "none", role: "img", "aria-label": etiquette || "Mini-courbe" });
    if (nombres.length < 2) return s;
    var mn = Math.min.apply(null, nombres), mx = Math.max.apply(null, nombres);
    var ecart = mx - mn || 1;
    var d = "", leve = true;
    vals.forEach(function (v, i) {
      if (!O.estNombre(v)) { leve = true; return; }
      var x = (i / (vals.length - 1)) * 100, y = 28 - ((v - mn) / ecart) * 26;
      d += (leve ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2) + " ";
      leve = false;
    });
    s.append(O.svg("path", { d: d.trim() }));
    return s;
  }

  /** Zone d'un graphique : canevas + message de remplacement si Chart.js manque. */
  function zone(etiquette, classe) {
    var canevas = O.h("canvas", { role: "img", "aria-label": etiquette });
    var conteneur = O.h("div", { class: "graphique__zone" + (classe ? " " + classe : "") }, canevas);
    if (!disponible()) conteneur.append(O.h("p", { class: "graphique__message" }, "Graphique indisponible : la bibliothèque de graphiques n'a pas pu être chargée."));
    return { conteneur: conteneur, canevas: canevas };
  }

  function message(conteneur, texte) {
    var ancien = conteneur.querySelector(".graphique__message");
    if (ancien) ancien.remove();
    if (texte) conteneur.append(O.h("p", { class: "graphique__message" }, texte));
  }

  window.Graphiques = {
    disponible: disponible, couleur: couleur, lavis: lavis, nettoyer: nettoyer, courbes: courbes, barres: barres,
    mini: mini, zone: zone, message: message, graduations: graduations, JOUR: JOUR,
  };
})();
