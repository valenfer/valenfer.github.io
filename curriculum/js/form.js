(function() {
  const EMAILJS_PUBLIC_KEY = 'Kk62GwVycucac8LrV';
  const EMAILJS_SERVICE_ID = 'service_u1njbm8';
  const EMAILJS_TEMPLATE_ID = 'template_r9tnrmk';

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-contacto');
    if (!form) return;

    emailjs.init(EMAILJS_PUBLIC_KEY);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const btn = document.getElementById('form-enviar');
      const exito = document.getElementById('form-exito');
      btn.disabled = true;
      btn.querySelector('span').textContent = 'Enviando...';

      const datos = {
        nombre: document.getElementById('nombre').value,
        empresa: document.getElementById('empresa').value || 'No especificada',
        cargo: document.getElementById('cargo').value || 'No especificado',
        telefono: document.getElementById('telefono').value,
        email: document.getElementById('email').value,
        comentario: document.getElementById('comentario').value || 'Sin comentario'
      };

      try {
        await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, datos);
        form.reset();
        exito.classList.add('visible');
        setTimeout(() => exito.classList.remove('visible'), 5000);
      } catch (err) {
        alert('Error al enviar. Inténtalo de nuevo.');
      }

      btn.disabled = false;
      btn.querySelector('span').textContent = 'Enviar mensaje';
    });
  });
})();