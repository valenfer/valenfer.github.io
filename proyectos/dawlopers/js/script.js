function ultimaActualizacion() {
    const lastUpdated = new Date(document.lastModified);
    return new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'long', year: 'numeric' }).format(lastUpdated);
}

function setActiveLink(link) {
    document.querySelectorAll('.nav-links a').forEach((item) => item.classList.remove('active'));
    if (link) link.classList.add('active');
}

function closeMenu() {
    const nav = document.getElementById('myNavbar');
    const toggle = document.querySelector('.nav-toggle');
    if (!nav || !toggle) return;
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
}

function toggleMenu() {
    const nav = document.getElementById('myNavbar');
    const toggle = document.querySelector('.nav-toggle');
    const isOpen = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(isOpen));
}

function cargarContenido(pagina, link) {
    fetch(pagina, { cache: 'no-cache' })
        .then((response) => {
            if (!response.ok) throw new Error(`No se pudo cargar ${pagina}`);
            return response.text();
        })
        .then((html) => {
            const content = document.getElementById('contenido');
            content.innerHTML = html;
            content.focus({ preventScroll: true });
            setActiveLink(link || document.querySelector(`.nav-links a[href="#${location.hash.replace('#', '')}"]`));
            closeMenu();
        })
        .catch(() => {
            document.getElementById('contenido').innerHTML = '<section class="panel"><h2>Ups, módulo no encontrado</h2><p>No se ha podido cargar esta sección. La web no se ha caído: solo está protestando con estilo.</p></section>';
        });
}

window.addEventListener('DOMContentLoaded', () => {
    const date = document.getElementById('lastUpdated');
    if (date) date.textContent = ultimaActualizacion();
    const routes = {
        '#uxui': './html/uxui.html',
        '#servidor': './html/servidor.html',
        '#cliente': './html/cliente.html',
        '#recursos': './html/recursos.html',
        '#articulos': './html/articulos.html',
        '#acercade': './html/acercade.html',
        '#inicio': './html/inicio.html'
    };
    const hash = routes[location.hash] ? location.hash : '#inicio';
    const link = document.querySelector(`.nav-links a[href="${hash}"]`);
    cargarContenido(routes[hash], link);
});
