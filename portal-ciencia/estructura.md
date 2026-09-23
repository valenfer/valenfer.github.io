ciencia-hoy/
├── index.html                  # Página principal con tarjetas de noticias
├── categoria.php              # Filtro por categoría
├── noticia.php                # Vista detallada de cada noticia
├── buscar.php                 # Buscador por palabra clave o DOI
├── landing.html               # Página promocional del proyecto
├── manual_instalacion.txt     # Guía paso a paso para instalar y configurar
│
├── admin/                     # Panel de administración
│   ├── login.php              # Acceso al panel
│   ├── dashboard.php          # Tabla con todas las noticias
│   ├── nuevo.php              # Crear nueva noticia (con imagen y DOI)
│   ├── editar.php             # Editar noticia existente (con importación)
│   ├── eliminar.php           # Eliminar noticia
│   ├── logout.php             # Cerrar sesión
│   └── auth.php               # Protección de acceso
│
├── php/
│   └── conexion.php           # Conexión a la base de datos MySQL
│
├── css/
│   └── estilo.css             # Estilos visuales del sitio
│
├── js/
│   └── script.js              # Scripts JS para interactividad futura
│
├── imagenes/
│   └── descarga.jpg           # Imagen por defecto para noticias
│
├── sql/
│   └── estructura.sql         # Script SQL para crear la base de datos
