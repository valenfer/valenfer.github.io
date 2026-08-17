document.addEventListener("DOMContentLoaded", function() {
  const flechas = document.querySelectorAll(".flecha");
  const botonMenu = document.createElement('button');

  botonMenu.className = 'boton-menu';
  botonMenu.innerHTML = '<span></span><span></span><span></span>';
  botonMenu.setAttribute('aria-label', 'Menú de navegación');
  const header = document.querySelector('.contenido-header');
  header.insertBefore(botonMenu, header.children[1]);

  const navUl = document.querySelector('#links');
  botonMenu.addEventListener('click', function() {
    navUl.classList.toggle('abrir');
    this.classList.toggle('abrir');
  });

  flechas.forEach(flecha => {
    flecha.addEventListener("click", function() {
      const apartado = this.closest('.apartado');
      const retractil = apartado.querySelector('.retractil');
      const titulo = apartado.querySelector('.titulo');
      const todasLasRetractiles = document.querySelectorAll('.retractil');

      // Cerrar todas las demás secciones abiertas (acordeón)
      todasLasRetractiles.forEach(div => {
        if (div !== retractil && div.classList.contains('abierto')) {
          div.classList.remove('abierto');
          const tituloAnterior = div.previousElementSibling.querySelector('.flecha');
          if (tituloAnterior) {
            tituloAnterior.classList.remove('rotado');
          }
        }
      });

      // Toggle esta sección
      titulo.classList.toggle('rotado');

      if (retractil.classList.contains('abierto')) {
        retractil.classList.remove('abierto');
      } else {
        retractil.classList.add('abierto');
      }
    });
  });

  // Cerrar menú al hacer clic en un enlace
  document.querySelectorAll('nav a').forEach(enlace => {
    enlace.addEventListener('click', () => {
      navUl.classList.remove('abrir');
      botonMenu.classList.remove('abrir');
    });
  });
});

function ultimaActualizacion(){
    var lastUpdated = new Date(document.lastModified);

    var formattedDate = lastUpdated.getDate() + "-" + (lastUpdated.getMonth()+1) + "-" + lastUpdated.getFullYear();
    return formattedDate;
}