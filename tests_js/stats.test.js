// Tests de js/stats.js — lancer avec : node --test tests_js/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const S = require("../js/stats.js");

// Générateur pseudo-aléatoire reproductible (pour des séries « indépendantes »).
function aleatoire(graine) {
  let x = graine;
  return () => { x = (x * 1103515245 + 12345) % 2147483648; return x / 2147483648 - 0.5; };
}
function moisDepuis(debutAnnee, n) {
  const dates = [];
  for (let i = 0; i < n; i++) {
    const a = debutAnnee + Math.floor(i / 12), m = (i % 12) + 1;
    dates.push(`${a}-${String(m).padStart(2, "0")}-01`);
  }
  return dates;
}
const proche = (a, b, tol = 1e-9) => assert.ok(Math.abs(a - b) <= tol, `${a} ≠ ${b}`);

test("base 100 : première valeur = 100, valeurs ≤ 0 exclues", () => {
  assert.deepEqual(S.base100([null, 50, 75, 100]), [null, 100, 150, 200]);
  assert.deepEqual(S.base100([10, -5, 0, 20]), [100, null, null, 200]);
  assert.deepEqual(S.base100([null, null]), [null, null]);
});

test("corrélation : identiques → 1, opposées → −1, indépendantes ≈ 0", () => {
  const x = Array.from({ length: 50 }, (_, i) => Math.sin(i / 3) + i * 0.01);
  proche(S.pearson(x, x).r, 1);
  proche(S.pearson(x, x.map((v) => -2 * v + 5)).r, -1);
  const a = aleatoire(7), b = aleatoire(99991);
  const u = Array.from({ length: 2000 }, a), v = Array.from({ length: 2000 }, b);
  assert.ok(Math.abs(S.pearson(u, v).r) < 0.08);
});

test("corrélation : moins de 12 points communs → trop peu de données", () => {
  const x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13];
  const y = [1, 2, 3, null, 5, 6, 7, 8, 9, 10, 11, 12, null];
  const res = S.pearson(x, y);
  assert.equal(res.r, null);
  assert.equal(res.n, 11);
  assert.equal(S.classer(null, 11).libelle, "trop peu de données");
});

test("seuil de fiabilité : max(0,2 ; 2/√n) et repères du cahier des charges", () => {
  proche(S.seuilFiabilite(12), 2 / Math.sqrt(12));
  assert.equal(S.seuilFiabilite(12).toFixed(2), "0.58");
  assert.equal(S.seuilFiabilite(26).toFixed(2), "0.39");
  assert.equal(S.seuilFiabilite(36).toFixed(2), "0.33");
  assert.equal(S.seuilFiabilite(60).toFixed(2), "0.26");
  assert.equal(S.seuilFiabilite(100), 0.2);
  assert.equal(S.seuilFiabilite(400), 0.2);
  // r = 0,5 avec 12 points : sous le seuil (0,58) → gris
  const c = S.classer(0.5, 12);
  assert.equal(c.fiable, false);
  assert.equal(c.sens, 0);
  assert.equal(c.libelle, "pas de lien fiable");
  // r = −0,5 avec 200 points : fiable, modéré, sens inverse
  const d = S.classer(-0.5, 200);
  assert.deepEqual([d.fiable, d.force, d.sens, d.sensLibelle], [true, "modere", -1, "bougent en sens inverse"]);
  assert.equal(S.classer(0.75, 200).libelle, "lien fort");
  assert.equal(S.classer(0.25, 200).libelle, "lien faible");
  assert.equal(S.classer(0.1, 200).libelle, "aucun lien");
});

test("corrélation glissante : fenêtre complète seulement, sens détecté par fenêtre", () => {
  const n = 60;
  const ref = Array.from({ length: n }, (_, i) => Math.sin(i));
  const ind = ref.map((v, i) => (i < 30 ? v : -v));
  const g = S.correlationGlissante(ref, ind, 24);
  for (let i = 0; i < 23; i++) assert.equal(g[i], null);
  proche(g[23].r, 1);
  assert.equal(g[23].classe.sens, 1);
  proche(g[59].r, -1);
  assert.equal(g[59].classe.sens, -1);
});

test("décalage : une série décalée de 3 mois est retrouvée à +3 (l'indicateur précède)", () => {
  const a = aleatoire(42);
  const base = Array.from({ length: 160 }, a);
  // L'indicateur annonce la référence avec 3 mois d'avance : ind(t) = ref(t + 3).
  const ref = base.slice(0, 150);
  const ind = base.slice(3, 153);
  const res = S.meilleurDecalage(ref, ind, -12, 12, 20, 140);
  assert.equal(res.meilleur.k, 3);
  proche(res.meilleur.r, 1);
  assert.equal(res.annonce, true);
  // decaler place la valeur de t en t + k
  assert.deepEqual(S.decaler([1, 2, 3, 4], 1), [null, 1, 2, 3]);
  assert.deepEqual(S.decaler([1, 2, 3, 4], -1), [2, 3, 4, null]);
});

test("décalage : rien d'annoncé si le gain sur r sans décalage est < 0,10", () => {
  const x = Array.from({ length: 100 }, (_, i) => i % 7);
  const res = S.meilleurDecalage(x, x, -5, 5, 10, 90);
  assert.equal(res.meilleur.k, 0);
  assert.equal(res.annonce, false);
});

test("alignement : fréquences différentes → dernière valeur de chaque période, sans report", () => {
  const quotidien = { dates: ["2024-01-02", "2024-01-31", "2024-02-15", "2024-02-29", "2024-04-10"], valeurs: [1, 2, 3, null, 5] };
  const mensuel = { dates: ["2024-01-01", "2024-02-01", "2024-03-01"], valeurs: [10, 20, 30] };
  const freq = S.frequenceLaPlusLente(["J", "M"]);
  assert.equal(freq, "M");
  const al = S.aligner([quotidien, mensuel], freq);
  assert.deepEqual(al.dates, ["2024-01-31", "2024-02-29", "2024-03-31", "2024-04-30"]);
  assert.deepEqual(al.valeurs[0], [2, 3, null, 5]); // mars vide : le trou reste un trou
  assert.deepEqual(al.valeurs[1], [10, 20, 30, null]);
  // hebdomadaire : clé = dimanche de la semaine
  assert.equal(S.clePeriode("2026-11-20", "S"), "2026-11-22");
  assert.equal(S.clePeriode("2026-11-22", "S"), "2026-11-22");
  assert.equal(S.clePeriode("2026-05-15", "T"), "2026-06-30");
});

test("modes : traitement des types T, N et N*", () => {
  const dates = moisDepuis(2020, 26);
  const niveau = dates.map((_, i) => 100 + i * 2);
  const taux = dates.map((_, i) => 1 + i * 0.1);
  // Mouvements : N en %, T et N* en points
  const mvtN = S.transformer(dates, niveau, "N", "mouvements");
  assert.equal(mvtN[0], null);
  proche(mvtN[1], 2);
  const mvtT = S.transformer(dates, taux, "T", "mouvements");
  proche(mvtT[5], 0.1);
  const mvtNs = S.transformer(dates, [0, -1, 2], "N*", "mouvements");
  assert.deepEqual(mvtNs, [null, -1, 3]);
  // Mouvements sur N avec une valeur ≤ 0 : pas de variation en %
  assert.deepEqual(S.transformer(dates.slice(0, 3), [10, -2, 5], "N", "mouvements"), [null, null, null]);
  // Rythmes : N → variation sur 12 mois (appariée par date) ; T et N* → niveau
  const ryN = S.transformer(dates, niveau, "N", "rythmes");
  for (let i = 0; i < 12; i++) assert.equal(ryN[i], null);
  proche(ryN[12], (124 / 100 - 1) * 100);
  assert.deepEqual(S.transformer(dates, taux, "T", "rythmes"), taux);
  assert.deepEqual(S.transformer(dates, taux, "N*", "rythmes"), taux);
  // Niveaux bruts : inchangés
  assert.deepEqual(S.transformer(dates, niveau, "N", "niveaux"), niveau);
});

test("variation annuelle : appariement par date, mois manquant → point manquant", () => {
  const dates = moisDepuis(2024, 25).filter((d) => d !== "2024-10-01"); // octobre 2024 absent
  const valeurs = dates.map((_, i) => 100 + i);
  const v = S.variationsAnnuelles(dates, valeurs);
  const i2025oct = dates.indexOf("2025-10-01");
  assert.equal(v[i2025oct], null); // pas de valeur un an plus tôt
  const i2025nov = dates.indexOf("2025-11-01");
  const i2024nov = dates.indexOf("2024-11-01");
  proche(v[i2025nov], (valeurs[i2025nov] / valeurs[i2024nov] - 1) * 100);
});

test("périodes : début de période et nombre de points", () => {
  assert.equal(S.debutPeriode("2026-11-20", "1A"), "2025-11-20");
  assert.equal(S.debutPeriode("2026-11-20", "1M"), "2026-10-20");
  assert.equal(S.debutPeriode("2026-11-20", "Max"), null);
  const mensuel = { dates: moisDepuis(2025, 23), valeurs: Array(23).fill(1) };
  // 1 mois d'une série mensuelle en quotidien : 1 ou 2 points (< 12 → bouton grisé)
  assert.ok(S.pointsDansPeriode(mensuel, "J", "2026-10-20", "2026-11-20") < 12);
  assert.equal(S.frequencePourPeriode("1M"), "J");
  assert.equal(S.frequencePourPeriode("1A"), "S");
  assert.equal(S.frequencePourPeriode("10A"), "M");
});

test("tableau des corrélations : symétrique, diagonale à 1", () => {
  const a = aleatoire(3);
  const x = Array.from({ length: 80 }, a);
  const y = x.map((v) => v * 2 + 0.01);
  const z = x.map((v) => -v);
  const m = S.matriceCorrelations([x, y, z]);
  proche(m[0][1].r, 1);
  proche(m[0][2].r, -1);
  proche(m[1][2].r, m[2][1].r);
  assert.equal(m[1][1].r, 1);
});

test("grille régulière (C1) : un mois absent de toutes les séries reste dans la grille", () => {
  const dates = moisDepuis(2024, 30).filter((d) => d !== "2025-10-01");
  const a = { dates, valeurs: dates.map((_, i) => 100 + i) };
  const b = { dates, valeurs: dates.map((_, i) => 50 + 2 * i) };
  const al = S.aligner([a, b], "M");
  assert.equal(al.dates.length, 30);
  const iOct = al.dates.indexOf("2025-10-31");
  assert.ok(iOct > 0);
  assert.equal(al.valeurs[0][iOct], null);
  const mvt = S.transformer(al.dates, al.valeurs[0], "N", "mouvements");
  assert.equal(mvt[iOct], null);
  assert.equal(mvt[iOct + 1], null); // la variation ne saute pas deux mois
  // un décalage de +3 mois est toujours retrouvé malgré le trou
  const r = aleatoire(5);
  const base = Array.from({ length: 63 }, r);
  const ref = { dates: moisDepuis(2020, 60), valeurs: base.slice(0, 60) };
  const ind = { dates: moisDepuis(2020, 60), valeurs: base.slice(3, 63) };
  ref.valeurs[30] = null; ind.valeurs[30] = null;
  const g = S.aligner([ref, ind], "M");
  const res = S.meilleurDecalage(g.valeurs[0], g.valeurs[1], -6, 6, 6, 59);
  assert.equal(res.meilleur.k, 3);
});

test("corrélation glissante (C2) : fenêtre trop peu remplie → null", () => {
  const x = Array.from({ length: 40 }, (_, i) => Math.sin(i));
  const y = x.map((v, i) => (i >= 10 && i < 30 && i % 2 ? null : v));
  const g = S.correlationGlissante(x, y, 24);
  assert.equal(g[29], null); // 14 paires sur 24 < 80 %
  assert.ok(g[39] === null || g[39].n >= 20);
});

test("fenêtres, décalage maximal et prolongement de grille (C3)", () => {
  assert.equal(S.fenetreGlissante("S", 52), 26);
  assert.equal(S.fenetreGlissante("M", 60), 24);
  assert.equal(S.fenetreGlissante("M", 120), 36);
  assert.equal(S.fenetreGlissante("J", 22), null);
  assert.equal(S.decalageMax("M", 120), 24);
  assert.equal(S.decalageMax("M", 60), 20);
  assert.equal(S.decalageMax("S", 52), 17);
  assert.deepEqual(S.prolongerGrille(["2026-09-30", "2026-10-31"], "M", 2), ["2026-09-30", "2026-10-31", "2026-11-30", "2026-12-31"]);
  assert.deepEqual(S.prolongerGrille(["2026-11-20"], "J", 1), ["2026-11-20", "2026-11-23"]);
});
