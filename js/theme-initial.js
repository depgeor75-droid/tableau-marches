// Applique le thème choisi (clair / sombre) avant le premier affichage, pour éviter un flash.
// « automatique » = aucun attribut : la page suit le réglage de l'appareil.
(function () {
  try {
    var theme = JSON.parse(localStorage.getItem("marches.theme") || '"automatique"');
    if (theme === "clair") document.documentElement.setAttribute("data-theme", "light");
    if (theme === "sombre") document.documentElement.setAttribute("data-theme", "dark");
  } catch (e) { /* stockage indisponible : thème automatique */ }
})();
