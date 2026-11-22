/* ==========================================================================
   outils.js — mise en forme « à la belge » et petits outils d'affichage.
   Script classique (fonctionne en file://) : expose window.Outils.
   Nombres et dates via Intl (fr-BE) ; heures en heure belge (Europe/Brussels).
   Tout texte venant des données est inséré avec textContent (jamais innerHTML).
   ========================================================================== */
(function () {
  "use strict";

  var MOINS = "−";
  var INSECABLE = " ";
  var formats = {};

  function estNombre(v) { return typeof v === "number" && isFinite(v); }

  function formateur(decimales) {
    if (!formats[decimales]) {
      formats[decimales] = new Intl.NumberFormat("fr-BE", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
    }
    return formats[decimales];
  }

  /** 1234.5 → « 1 234,50 » (espace insécable, virgule décimale, vrai signe moins). */
  function nombre(v, decimales) {
    if (!estNombre(v)) return "n.d.";
    var d = decimales === undefined ? 2 : decimales;
    return formateur(d).format(v).replace("-", MOINS).replace(/ /g, INSECABLE);
  }

  /** Toujours signé : « +1,2 » ou « −3,4 ». */
  function signe(v, decimales) {
    if (!estNombre(v)) return "n.d.";
    var d = decimales === undefined ? 1 : decimales;
    var arrondi = Number(v.toFixed(d));
    var texte = nombre(Math.abs(arrondi), d);
    if (arrondi > 0) return "+" + texte;
    if (arrondi < 0) return MOINS + texte;
    return texte;
  }

  var fDate = new Intl.DateTimeFormat("fr-BE", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  var fMois = new Intl.DateTimeFormat("fr-BE", { month: "short", year: "numeric", timeZone: "UTC" });
  var fMoisLong = new Intl.DateTimeFormat("fr-BE", { month: "long", year: "numeric", timeZone: "UTC" });
  var fHeureBelge = new Intl.DateTimeFormat("fr-BE", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Brussels" });

  function versDateUTC(iso) {
    return new Date(Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10) || 1));
  }

  /** « 2026-11-22 » → « 22 nov. 2026 ». */
  function date(iso) {
    if (!iso) return "n.d.";
    return fDate.format(versDateUTC(iso));
  }

  /** Date selon la fréquence : mensuel → « oct. 2026 », trimestriel → « T3 2026 », annuel → « 2026 ». */
  function dateSelon(iso, frequence) {
    if (!iso) return "n.d.";
    if (frequence === "M") return fMois.format(versDateUTC(iso));
    if (frequence === "T") return "T" + (Math.floor((+iso.slice(5, 7) - 1) / 3) + 1) + " " + iso.slice(0, 4);
    if (frequence === "A") return iso.slice(0, 4);
    return date(iso);
  }

  function moisLong(iso) { return fMoisLong.format(versDateUTC(iso)); }

  /** Horodatage ISO (UTC ou avec décalage) → « 22 nov. 2026 à 06:21 » en heure belge. */
  function dateHeure(isoComplet) {
    if (!isoComplet) return "n.d.";
    var d = new Date(isoComplet);
    if (isNaN(d)) return "n.d.";
    var parties = fHeureBelge.formatToParts(d);
    var get = function (type) { var p = parties.find(function (x) { return x.type === type; }); return p ? p.value : ""; };
    return get("day") + " " + get("month") + " " + get("year") + " à " + get("hour") + ":" + get("minute");
  }

  var LIBELLES_FREQUENCE = { J: "quotidien", S: "hebdomadaire", M: "mensuel", T: "trimestriel", A: "annuel" };
  var PUBLICATION = { S: "publié chaque semaine", M: "publié chaque mois", T: "publié chaque trimestre", A: "publié chaque année" };

  /** Valeur avec unité selon l'indicateur du catalogue. */
  function valeur(ind, v, decimalesForcees) {
    if (!estNombre(v)) return "n.d.";
    var d = decimalesForcees !== undefined ? decimalesForcees : (ind.decimales_affichage !== undefined ? ind.decimales_affichage : 2);
    var unite = ind.unite || "";
    if (unite === "%") return nombre(v, d) + INSECABLE + "%";
    if (unite === "pt") return signe(v, d) + INSECABLE + "pt";
    if (!unite || unite === "indice" || unite === "points") return nombre(v, d);
    return nombre(v, d) + INSECABLE + unite;
  }

  /** Variation : en points pour T et N*, en % pour N. */
  function variation(ind, v) {
    if (!estNombre(v)) return "n.d.";
    if (ind.type === "N") return signe(v, 1) + INSECABLE + "%";
    var d = Math.abs(v) < 10 ? 2 : 1;
    return signe(v, d) + INSECABLE + "pt";
  }

  /** Flèche neutre ▲ ▼ ▶ (jamais de couleur : une hausse n'est pas toujours une bonne nouvelle). */
  function fleche(v, seuil) {
    if (!estNombre(v)) return "";
    var s = seuil || 0;
    var r = Math.round(v * 100) / 100; // une variation affichée « 0,00 » est stable
    return r > s ? "▲" : r < -s ? "▼" : "▶";
  }

  function rangOrdinal(p) { return p + (p === 1 ? "ᵉʳ" : "ᵉ"); }

  // ------------------------------------------------------------------ DOM
  var SVG_NS = "http://www.w3.org/2000/svg";

  function h(balise, attributs) {
    var element = document.createElement(balise);
    var attrs = attributs || {};
    Object.keys(attrs).forEach(function (cle) {
      var v = attrs[cle];
      if (v === null || v === undefined || v === false) return;
      if (cle === "class") element.className = v;
      else if (cle === "dataset") Object.assign(element.dataset, v);
      else if (cle.slice(0, 2) === "on" && typeof v === "function") element.addEventListener(cle.slice(2), v);
      else if (v === true) element.setAttribute(cle, "");
      else element.setAttribute(cle, v);
    });
    ajouter(element, Array.prototype.slice.call(arguments, 2));
    return element;
  }

  function ajouter(parent, enfants) {
    [enfants].flat(Infinity).forEach(function (enfant) {
      if (enfant === null || enfant === undefined || enfant === false) return;
      parent.append(enfant instanceof Node ? enfant : document.createTextNode(String(enfant)));
    });
    return parent;
  }

  function svg(balise, attributs) {
    var element = document.createElementNS(SVG_NS, balise);
    Object.keys(attributs || {}).forEach(function (cle) { element.setAttribute(cle, attributs[cle]); });
    for (var i = 2; i < arguments.length; i++) if (arguments[i]) element.append(arguments[i]);
    return element;
  }

  function vider(element) { element.replaceChildren(); return element; }

  function lienExterne(url, contenu) {
    var sur = typeof url === "string" && /^https?:\/\//i.test(url) ? url : "#";
    return h("a", { href: sur, target: "_blank", rel: "noopener noreferrer", class: "lien-externe" }, contenu);
  }

  // --------------------------------------------------- stockage local sûr
  function lire(cle, defaut) {
    try {
      var v = localStorage.getItem("marches." + cle);
      return v === null ? defaut : JSON.parse(v);
    } catch (e) { return defaut; }
  }
  function ecrire(cle, valeurAEcrire) {
    try { localStorage.setItem("marches." + cle, JSON.stringify(valeurAEcrire)); } catch (e) { /* stockage indisponible */ }
  }

  // -------------------------------------------- chargement des données
  var chargements = {};
  /** Charge data/<nom>.js par une balise <script> (fonctionne en file://). Promesse résolue même en cas d'échec. */
  function charger(nom) {
    if (window.DONNEES && window.DONNEES[nom]) return Promise.resolve(window.DONNEES[nom]);
    if (chargements[nom]) return chargements[nom];
    chargements[nom] = new Promise(function (resoudre) {
      var s = document.createElement("script");
      s.src = "data/" + nom + ".js";
      s.async = true;
      s.onload = function () { resoudre((window.DONNEES || {})[nom] || null); };
      s.onerror = function () { delete chargements[nom]; resoudre(null); };
      document.head.append(s);
    });
    return chargements[nom];
  }

  // ------------------------------------------------------------ CSV
  function telechargerFichier(nomFichier, contenu, type) {
    var blob = new Blob([contenu], { type: type || "text/csv;charset=utf-8" });
    var a = h("a", { href: URL.createObjectURL(blob), download: nomFichier });
    document.body.append(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /** Nombre au format CSV belge (virgule décimale, sans séparateur de milliers). */
  function nombreCsv(v, decimales) {
    if (!estNombre(v)) return "";
    return v.toFixed(decimales === undefined ? 4 : decimales).replace(".", ",");
  }

  window.Outils = {
    MOINS: MOINS, INSECABLE: INSECABLE, LIBELLES_FREQUENCE: LIBELLES_FREQUENCE, PUBLICATION: PUBLICATION,
    estNombre: estNombre, nombre: nombre, signe: signe, date: date, dateSelon: dateSelon, moisLong: moisLong,
    dateHeure: dateHeure, valeur: valeur, variation: variation, fleche: fleche, rangOrdinal: rangOrdinal,
    h: h, ajouter: ajouter, svg: svg, vider: vider, lienExterne: lienExterne,
    lire: lire, ecrire: ecrire, charger: charger, telechargerFichier: telechargerFichier, nombreCsv: nombreCsv,
  };
})();
