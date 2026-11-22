/* ==========================================================================
   stats.js — fonctions de calcul PURES du comparateur (§9 du cahier des charges).
   Aucune dépendance au navigateur : testable avec `node --test tests_js/`.
   Chargé dans la page par une balise <script> classique (window.Stats),
   ou par require() dans node.

   Conventions :
   - une série = { dates: ["AAAA-MM-JJ", …], valeurs: [nombre | null, …] }, dates triées ;
   - un trou reste un trou : aucune interpolation, aucun report de valeur ;
   - types : "T" (taux, %), "N" (niveau/prix), "N*" (indice centré).
   ========================================================================== */
(function (racine, usine) {
  if (typeof module === "object" && module.exports) module.exports = usine();
  else racine.Stats = usine();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var JOUR = 86400000;
  var RANG_FREQUENCE = { J: 0, S: 1, M: 2, T: 3, A: 4 };

  var REGLAGES_DEFAUT = {
    seuils_force: [0.2, 0.4, 0.7], // |r| : < 0,2 aucun · 0,2-0,4 faible · 0,4-0,7 modéré · ≥ 0,7 fort
    fiabilite_plancher: 0.2,       // seuil de fiabilité = max(0,2 ; 2 ÷ √n)
    points_min: 12,
    ecart_meilleur_decalage: 0.10,
    couverture_min: 0.8,
    fenetres: { S: 26, M_5A: 24, M_long: 36, T: 12 },
    decalage_max_mois: 24,
  };

  function estNombre(v) {
    return typeof v === "number" && isFinite(v);
  }

  function reglages(options) {
    var r = {};
    for (var cle in REGLAGES_DEFAUT) r[cle] = REGLAGES_DEFAUT[cle];
    if (options) for (var c in options) if (options[c] !== undefined) r[c] = options[c];
    return r;
  }

  // ------------------------------------------------------------------ dates
  function versTemps(iso) {
    return Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10) || 1);
  }

  function versIso(temps) {
    return new Date(temps).toISOString().slice(0, 10);
  }

  /** Clé de période d'une date : fin de la période, au format AAAA-MM-JJ. */
  function clePeriode(iso, frequence) {
    var a = +iso.slice(0, 4), m = +iso.slice(5, 7) - 1, j = +iso.slice(8, 10) || 1;
    switch (frequence) {
      case "J": return iso.slice(0, 10);
      case "S": { // dimanche de la semaine (semaine du lundi au dimanche)
        var t = Date.UTC(a, m, j);
        var jourSemaine = new Date(t).getUTCDay();
        return versIso(t + ((7 - jourSemaine) % 7) * JOUR);
      }
      case "M": return versIso(Date.UTC(a, m + 1, 0));
      case "T": return versIso(Date.UTC(a, Math.floor(m / 3) * 3 + 3, 0));
      case "A": return versIso(Date.UTC(a, 12, 0));
      default: throw new Error("Fréquence inconnue : " + frequence);
    }
  }

  /** La plus lente de plusieurs fréquences (« J » < « S » < « M » < « T » < « A »). */
  function frequenceLaPlusLente(liste) {
    var lente = "J";
    for (var i = 0; i < liste.length; i++) {
      if (liste[i] && RANG_FREQUENCE[liste[i]] > RANG_FREQUENCE[lente]) lente = liste[i];
    }
    return lente;
  }

  /** Fréquence d'affichage et de calcul selon la période (§9.2). */
  function frequencePourPeriode(periode) {
    if (periode === "1M") return "J";
    if (periode === "1A") return "S";
    return "M";
  }

  /** Nombre de périodes dans un an, pour une fréquence. */
  function periodesParAn(frequence) {
    return { J: 252, S: 52, M: 12, T: 4, A: 1 }[frequence];
  }

  // ------------------------------------------------------------- alignement
  /**
   * Ramène une série à une fréquence : dernière valeur connue de chaque période.
   * Les valeurs nulles sont ignorées (si toute la période est vide, la période est absente).
   */
  function reechantillonner(serie, frequence) {
    var cles = [], valeurs = [], index = {};
    for (var i = 0; i < serie.dates.length; i++) {
      var v = serie.valeurs[i];
      if (!estNombre(v)) continue;
      var cle = clePeriode(serie.dates[i], frequence);
      if (index[cle] === undefined) {
        index[cle] = cles.length;
        cles.push(cle);
        valeurs.push(v);
      } else {
        valeurs[index[cle]] = v; // dates triées : la dernière l'emporte
      }
    }
    return { dates: cles, valeurs: valeurs };
  }

  /** Clé de la période suivante (fin de période) : S +7 jours, M/T/A fin de la période suivante. */
  function periodeSuivante(cle, frequence) {
    var a = +cle.slice(0, 4), m = +cle.slice(5, 7) - 1;
    switch (frequence) {
      case "J": return versIso(versTemps(cle) + JOUR);
      case "S": return versIso(versTemps(cle) + 7 * JOUR);
      case "M": return versIso(Date.UTC(a, m + 2, 0));
      case "T": return versIso(Date.UTC(a, m + 4, 0));
      case "A": return versIso(Date.UTC(a + 1, 12, 0));
      default: throw new Error("Fréquence inconnue : " + frequence);
    }
  }

  /** Prolonge une grille de k périodes futures (pour dessiner une courbe décalée vers l'avant). */
  function prolongerGrille(dates, frequence, k) {
    var sortie = dates.slice();
    for (var i = 0; i < k && sortie.length; i++) {
      var derniere = sortie[sortie.length - 1];
      var suivante = periodeSuivante(derniere, frequence);
      if (frequence === "J") { // jours ouvrables seulement
        while ([0, 6].indexOf(new Date(versTemps(suivante)).getUTCDay()) >= 0) suivante = periodeSuivante(suivante, "J");
      }
      sortie.push(suivante);
    }
    return sortie;
  }

  /**
   * Aligne plusieurs séries sur une grille commune de périodes.
   * J : union des jours présents ; S, M, T, A : grille RÉGULIÈRE de la première à la dernière
   * période (une période absente de toutes les séries reste dans la grille, avec null).
   * Retourne { dates: [clés], valeurs: [[…série 1], [… série 2], …] } ; null là où une série n'a rien.
   */
  function aligner(series, frequence) {
    var reech = series.map(function (s) { return reechantillonner(s, frequence); });
    var ensemble = {};
    reech.forEach(function (s) { s.dates.forEach(function (d) { ensemble[d] = true; }); });
    var dates = Object.keys(ensemble).sort();
    if (frequence !== "J" && dates.length) {
      var reguliere = [dates[0]];
      var fin = dates[dates.length - 1];
      while (reguliere[reguliere.length - 1] < fin) reguliere.push(periodeSuivante(reguliere[reguliere.length - 1], frequence));
      dates = reguliere;
    }
    var position = {};
    dates.forEach(function (d, i) { position[d] = i; });
    var valeurs = reech.map(function (s) {
      var ligne = new Array(dates.length).fill(null);
      for (var i = 0; i < s.dates.length; i++) ligne[position[s.dates[i]]] = s.valeurs[i];
      return ligne;
    });
    return { dates: dates, valeurs: valeurs };
  }

  // ---------------------------------------------------------------- base 100
  /** Base 100 = première valeur valide (strictement positive) ; points ≤ 0 → null. */
  function base100(valeurs) {
    var base = null;
    for (var i = 0; i < valeurs.length; i++) {
      if (estNombre(valeurs[i]) && valeurs[i] > 0) { base = valeurs[i]; break; }
    }
    return valeurs.map(function (v) {
      if (base === null || !estNombre(v) || v <= 0) return null;
      return (v / base) * 100;
    });
  }

  // ------------------------------------------------------- transformations
  /** Variation d'une période à l'autre : en % pour N, en points pour T et N*. */
  function variationsSuccessives(valeurs, type) {
    var sortie = [null];
    for (var i = 1; i < valeurs.length; i++) {
      var a = valeurs[i - 1], b = valeurs[i];
      if (!estNombre(a) || !estNombre(b)) { sortie.push(null); continue; }
      if (type === "N") sortie.push(a > 0 && b > 0 ? (b / a - 1) * 100 : null);
      else sortie.push(b - a);
    }
    return sortie;
  }

  /**
   * Variation sur 12 mois en %, appariée PAR DATE : valeur(t) ÷ valeur(t − 1 an) − 1.
   * La valeur « un an plus tôt » est celle de la période dont la clé tombe un an avant
   * (tolérance de quelques jours pour les fréquences quotidienne et hebdomadaire).
   */
  function variationsAnnuelles(dates, valeurs) {
    var temps = dates.map(versTemps);
    var sortie = new Array(valeurs.length).fill(null);
    var j = 0;
    for (var i = 0; i < valeurs.length; i++) {
      if (!estNombre(valeurs[i]) || valeurs[i] <= 0) continue;
      var d = new Date(temps[i]);
      var cible = Date.UTC(d.getUTCFullYear() - 1, d.getUTCMonth(), d.getUTCDate());
      // fin de mois : 29 févr. → 28 févr., 31 → dernier jour du mois
      if (new Date(cible).getUTCMonth() !== d.getUTCMonth()) {
        cible = Date.UTC(d.getUTCFullYear() - 1, d.getUTCMonth() + 1, 0);
      }
      while (j < i && temps[j] < cible - 3 * JOUR) j++;
      // cherche la date la plus proche de la cible, à ± 3 jours
      var meilleur = -1;
      for (var k = j; k < i && temps[k] <= cible + 3 * JOUR; k++) {
        if (meilleur < 0 || Math.abs(temps[k] - cible) < Math.abs(temps[meilleur] - cible)) meilleur = k;
      }
      if (meilleur < 0) continue;
      var ancien = valeurs[meilleur];
      if (estNombre(ancien) && ancien > 0) sortie[i] = (valeurs[i] / ancien - 1) * 100;
    }
    return sortie;
  }

  /**
   * Transformation selon le mode de corrélation (§9.3) :
   * - « mouvements » : variations successives (N en %, T/N* en points) ;
   * - « rythmes »    : N → variation sur 12 mois en % ; T/N* → niveau ;
   * - « niveaux »    : valeurs brutes.
   */
  function transformer(dates, valeurs, type, mode) {
    if (mode === "mouvements") return variationsSuccessives(valeurs, type);
    if (mode === "rythmes") return type === "N" ? variationsAnnuelles(dates, valeurs) : valeurs.slice();
    if (mode === "niveaux") return valeurs.slice();
    throw new Error("Mode inconnu : " + mode);
  }

  // --------------------------------------------------------------- Pearson
  /** Coefficient de Pearson sur les paires où les deux valeurs existent. */
  function pearson(x, y, options) {
    var o = reglages(options);
    var n = 0, sx = 0, sy = 0;
    var longueur = Math.min(x.length, y.length);
    for (var i = 0; i < longueur; i++) {
      if (estNombre(x[i]) && estNombre(y[i])) { n++; sx += x[i]; sy += y[i]; }
    }
    if (n < o.points_min) return { r: null, n: n };
    var mx = sx / n, my = sy / n, sxy = 0, sxx = 0, syy = 0;
    for (var k = 0; k < longueur; k++) {
      if (estNombre(x[k]) && estNombre(y[k])) {
        var dx = x[k] - mx, dy = y[k] - my;
        sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
      }
    }
    if (sxx === 0 || syy === 0) return { r: null, n: n };
    var r = sxy / Math.sqrt(sxx * syy);
    return { r: Math.max(-1, Math.min(1, r)), n: n };
  }

  /** Seuil de fiabilité : max(0,2 ; 2 ÷ √n). */
  function seuilFiabilite(n, options) {
    var o = reglages(options);
    if (!n) return 1;
    return Math.max(o.fiabilite_plancher, 2 / Math.sqrt(n));
  }

  /**
   * Classe un coefficient : { force: "aucun"|"faible"|"modere"|"fort"|null, sens: 1|-1|0,
   * fiable: bool, libelle: "lien fort", sensLibelle: "bougent ensemble" }.
   * « pas de lien fiable » (gris) si |r| < seuil de fiabilité.
   */
  function classer(r, n, options) {
    var o = reglages(options);
    if (!estNombre(r)) return { force: null, sens: 0, fiable: false, libelle: "trop peu de données", sensLibelle: "" };
    var a = Math.abs(r);
    var fiable = a >= seuilFiabilite(n, o);
    var s = o.seuils_force;
    var force = a < s[0] ? "aucun" : a < s[1] ? "faible" : a < s[2] ? "modere" : "fort";
    if (!fiable) {
      return { force: force, sens: 0, fiable: false, libelle: force === "aucun" ? "aucun lien" : "pas de lien fiable", sensLibelle: "" };
    }
    var libelles = { faible: "lien faible", modere: "lien modéré", fort: "lien fort" };
    return {
      force: force, sens: r > 0 ? 1 : -1, fiable: true, libelle: libelles[force],
      sensLibelle: r > 0 ? "bougent ensemble" : "bougent en sens inverse",
    };
  }

  /**
   * Corrélation glissante sur une fenêtre de w périodes (les w dernières).
   * Fenêtre ignorée (null) si moins de couverture_min (80 %) de paires valides.
   */
  function correlationGlissante(x, y, w, options) {
    var o = reglages(options);
    var sortie = new Array(Math.min(x.length, y.length)).fill(null);
    for (var i = w - 1; i < sortie.length; i++) {
      var res = pearson(x.slice(i - w + 1, i + 1), y.slice(i - w + 1, i + 1), o);
      if (res.r === null || res.n < Math.ceil(o.couverture_min * w)) continue;
      sortie[i] = { r: res.r, n: res.n, classe: classer(res.r, res.n, o) };
    }
    return sortie;
  }

  // -------------------------------------------------------------- décalage
  /**
   * Décale une série de k périodes sur la grille : la valeur de l'indicateur au temps t
   * est placée en t + k (k > 0 : l'indicateur PRÉCÈDE la référence de k périodes).
   * decaler([a,b,c,d], 1) → [null, a, b, c]
   */
  function decaler(valeurs, k) {
    var n = valeurs.length;
    var sortie = new Array(n).fill(null);
    for (var i = 0; i < n; i++) {
      var source = i - k;
      if (source >= 0 && source < n) sortie[i] = valeurs[source];
    }
    return sortie;
  }

  /**
   * Corrélation entre la référence et un indicateur décalé de k, sur la fenêtre [debut, fin]
   * de la grille complète (les valeurs de l'indicateur hors fenêtre servent au décalage).
   */
  function correlationDecalee(ref, ind, k, debut, fin, options) {
    var d = decaler(ind, k);
    return pearson(ref.slice(debut, fin + 1), d.slice(debut, fin + 1), options);
  }

  /**
   * Teste tous les décalages de kMin à kMax. Retourne
   * { courbe: [{k, r, n}], meilleur: {k, r, n} | null, sansDecalage: {r, n}, annonce: bool }.
   * Un décalage n'est annoncé que si son r dépasse le seuil de fiabilité ET dépasse
   * d'au moins 0,10 (en valeur absolue) le r sans décalage.
   */
  function meilleurDecalage(ref, ind, kMin, kMax, debut, fin, options) {
    var o = reglages(options);
    var courbe = [];
    var meilleur = null;
    for (var k = kMin; k <= kMax; k++) {
      var res = correlationDecalee(ref, ind, k, debut, fin, o);
      courbe.push({ k: k, r: res.r, n: res.n });
      if (res.r === null) continue;
      if (!meilleur || Math.abs(res.r) > Math.abs(meilleur.r)) meilleur = { k: k, r: res.r, n: res.n };
    }
    var zero = correlationDecalee(ref, ind, 0, debut, fin, o);
    var annonce = Boolean(meilleur && meilleur.k !== 0 &&
      Math.abs(meilleur.r) >= seuilFiabilite(meilleur.n, o) &&
      Math.abs(meilleur.r) - (zero.r === null ? 0 : Math.abs(zero.r)) >= o.ecart_meilleur_decalage - 1e-12);
    return { courbe: courbe, meilleur: meilleur, sansDecalage: zero, annonce: annonce };
  }

  /** Tableau des corrélations de chaque paire : matrice [i][j] = {r, n, classe}. */
  function matriceCorrelations(listes, options) {
    var m = [];
    for (var i = 0; i < listes.length; i++) {
      m.push([]);
      for (var j = 0; j < listes.length; j++) {
        if (i === j) { m[i].push({ r: 1, n: null, classe: null }); continue; }
        var res = pearson(listes[i], listes[j], options);
        m[i].push({ r: res.r, n: res.n, classe: classer(res.r, res.n, options) });
      }
    }
    return m;
  }

  /**
   * Taille de la fenêtre de corrélation glissante : S → 26 ; M → 24 si la période fait
   * 7 ans au plus (≤ 84 points), 36 au-delà ; T → 12 ; J (vue 1 M) → null (pas de glissante).
   */
  function fenetreGlissante(frequence, nbPoints, options) {
    var f = reglages(options).fenetres;
    if (frequence === "S") return f.S;
    if (frequence === "M") return nbPoints <= 84 ? f.M_5A : f.M_long;
    if (frequence === "T") return f.T;
    return null;
  }

  /** Décalage maximal (en périodes) : 24 mois dans l'unité de la fréquence, et au plus un tiers des points. */
  function decalageMax(frequence, nbPoints, options) {
    var mois = reglages(options).decalage_max_mois;
    var parUnite = { J: Math.round(mois * 21), S: Math.round(mois * 52 / 12), M: mois, T: Math.round(mois / 3), A: Math.round(mois / 12) }[frequence];
    return Math.max(0, Math.min(parUnite, Math.floor(nbPoints / 3)));
  }

  // ------------------------------------------------------------- périodes
  var RECULS = { "1M": [0, 1], "1A": [1, 0], "5A": [5, 0], "10A": [10, 0], "30A": [30, 0] };

  /** Date de début d'une période comptée depuis une date de fin (ISO). « Max » → null. */
  function debutPeriode(finIso, periode) {
    if (!RECULS[periode]) return null;
    var a = +finIso.slice(0, 4) - RECULS[periode][0];
    var m = +finIso.slice(5, 7) - 1 - RECULS[periode][1];
    var j = +finIso.slice(8, 10) || 1;
    var dernierJour = new Date(Date.UTC(a, m + 1, 0)).getUTCDate();
    return versIso(Date.UTC(a, m, Math.min(j, dernierJour)));
  }

  /** Nombre de points valides d'une série dans [debut, fin] après rééchantillonnage. */
  function pointsDansPeriode(serie, frequence, debutIso, finIso) {
    var r = reechantillonner(serie, frequence);
    var n = 0;
    for (var i = 0; i < r.dates.length; i++) {
      if ((!debutIso || r.dates[i] >= debutIso) && (!finIso || r.dates[i] <= clePeriode(finIso, frequence))) n++;
    }
    return n;
  }

  return {
    REGLAGES_DEFAUT: REGLAGES_DEFAUT,
    estNombre: estNombre,
    versTemps: versTemps,
    versIso: versIso,
    clePeriode: clePeriode,
    frequenceLaPlusLente: frequenceLaPlusLente,
    frequencePourPeriode: frequencePourPeriode,
    periodesParAn: periodesParAn,
    reechantillonner: reechantillonner,
    periodeSuivante: periodeSuivante,
    prolongerGrille: prolongerGrille,
    aligner: aligner,
    fenetreGlissante: fenetreGlissante,
    decalageMax: decalageMax,
    base100: base100,
    variationsSuccessives: variationsSuccessives,
    variationsAnnuelles: variationsAnnuelles,
    transformer: transformer,
    pearson: pearson,
    seuilFiabilite: seuilFiabilite,
    classer: classer,
    correlationGlissante: correlationGlissante,
    decaler: decaler,
    correlationDecalee: correlationDecalee,
    meilleurDecalage: meilleurDecalage,
    matriceCorrelations: matriceCorrelations,
    debutPeriode: debutPeriode,
    pointsDansPeriode: pointsDansPeriode,
  };
});
