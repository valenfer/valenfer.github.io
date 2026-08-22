/* ═══════════════════════════════════════════════════
   VALENTÍN FERNÁNDEZ GUIJARRO — Scripts CV 2026
   ═══════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", function () {

  /* ── Acordeón: abrir/cerrar secciones ── */
  document.querySelectorAll(".titulo").forEach(function (titulo) {
    titulo.addEventListener("click", function () {
      const apartado  = this.closest(".apartado");
      const retractil = apartado.querySelector(".retractil");
      const flecha    = this.querySelector(".flecha");
      const estaAbierto = retractil.classList.contains("abierto");

      // Cerrar todos los demás (acordeón)
      document.querySelectorAll(".retractil.abierto").forEach(function (el) {
        if (el !== retractil) {
          el.classList.remove("abierto");
          const otraFlecha = el.closest(".apartado").querySelector(".flecha");
          if (otraFlecha) otraFlecha.classList.remove("rotado");
        }
      });

      // Toggle este
      retractil.classList.toggle("abierto", !estaAbierto);
      if (flecha) flecha.classList.toggle("rotado", !estaAbierto);
    });
  });

  /* ── Menú móvil ── */
  const botonMenu = document.querySelector(".boton-menu");
  const navUl     = document.querySelector("#links");

  if (botonMenu && navUl) {
    botonMenu.addEventListener("click", function () {
      navUl.classList.toggle("abrir");
      this.classList.toggle("abrir");
    });

    document.querySelectorAll("nav a").forEach(function (enlace) {
      enlace.addEventListener("click", function () {
        navUl.classList.remove("abrir");
        botonMenu.classList.remove("abrir");
      });
    });
  }

  /* ── Active nav link on scroll ── */
  const sections = document.querySelectorAll("section[id], hr[id], main[id]");
  const navLinks = document.querySelectorAll("nav a[href^='#']");

  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          navLinks.forEach(function (link) {
            link.style.color = "";
            link.style.background = "";
          });
          const active = document.querySelector('nav a[href="#' + entry.target.id + '"]');
          if (active) {
            active.style.color = "var(--accent)";
            active.style.background = "var(--accent-dim)";
          }
        }
      });
    },
    { rootMargin: "-40% 0px -55% 0px" }
  );

  sections.forEach(function (s) { observer.observe(s); });

  /* ── Header shrink on scroll ── */
  const header = document.querySelector(".site-header");
  window.addEventListener("scroll", function () {
    header.style.borderBottomColor = window.scrollY > 40
      ? "rgba(42,42,64,0.8)"
      : "var(--border)";
  }, { passive: true });

});

/* ── Última actualización (llamada inline desde HTML) ── */
function ultimaActualizacion() {
  var d = new Date(document.lastModified);
  return d.getDate() + "-" + (d.getMonth() + 1) + "-" + d.getFullYear();
}
