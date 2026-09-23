// === script.js para Ciencia Hoy ===

// Confirmación antes de eliminar una noticia
function confirmarEliminacion(event) {
  if (!confirm("¿Estás seguro de que deseas eliminar esta noticia? Esta acción no se puede deshacer.")) {
    event.preventDefault();
  }
}

// Asignar confirmación a todos los enlaces de eliminación
document.addEventListener("DOMContentLoaded", () => {
  const enlacesEliminar = document.querySelectorAll("a[href*='eliminar.php']");
  enlacesEliminar.forEach(enlace => {
    enlace.addEventListener("click", confirmarEliminacion);
  });
});

// Scroll suave para anclas internas
document.querySelectorAll('a[href^="#"]').forEach(ancla => {
  ancla.addEventListener("click", function (e) {
    e.preventDefault();
    const destino = document.querySelector(this.getAttribute("href"));
    if (destino) {
      destino.scrollIntoView({ behavior: "smooth" });
    }
  });
});

// Validación mínima de formularios (ejemplo)
function validarFormulario(form) {
  const campos = form.querySelectorAll("input[required], textarea[required], select[required]");
  for (let campo of campos) {
    if (!campo.value.trim()) {
      alert("Por favor, completa todos los campos obligatorios.");
      campo.focus();
      return false;
    }
  }
  return true;
}
