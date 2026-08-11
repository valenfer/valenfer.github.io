/* AIDA · Nodo 20 — comportamiento compartido (defensivo) */

(function () {
  "use strict";

  /* ---- Navegación móvil ---- */

  var boton = document.getElementById("nav-boton");
  var lista = document.getElementById("nav-lista");

  if (boton && lista) {
    function abrir() {
      boton.setAttribute("aria-expanded", "true");
      lista.setAttribute("data-abierto", "true");
    }

    function cerrar() {
      boton.setAttribute("aria-expanded", "false");
      lista.setAttribute("data-abierto", "false");
    }

    boton.addEventListener("click", function () {
      if (boton.getAttribute("aria-expanded") === "true") {
        cerrar();
      } else {
        abrir();
      }
    });

    lista.addEventListener("click", function (evento) {
      var objetivo = evento.target;
      if (objetivo && objetivo.tagName === "A") {
        cerrar();
      }
    });

    document.addEventListener("keydown", function (evento) {
      if (evento.key === "Escape" && boton.getAttribute("aria-expanded") === "true") {
        cerrar();
        boton.focus();
      }
    });
  }

  /* ---- Indicador de lectura ---- */

  var progreso = document.getElementById("progreso");
  var barra = progreso ? progreso.querySelector("i") : null;

  if (progreso && barra) {
    var actualizar = function () {
      var total = document.documentElement.scrollHeight - window.innerHeight;
      if (total <= 0) {
        barra.style.transform = "scaleX(0)";
        return;
      }
      var proporcion = window.scrollY / total;
      barra.style.transform = "scaleX(" + Math.max(0, Math.min(1, proporcion)) + ")";
    };

    window.addEventListener("scroll", actualizar, { passive: true });
    window.addEventListener("resize", actualizar);
    actualizar();
  }
})();
