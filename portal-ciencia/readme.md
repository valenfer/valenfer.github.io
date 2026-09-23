# 🧠 Ciencia Hoy

**Ciencia Hoy** es un portal web de divulgación científica que presenta noticias basadas en estudios reales, con importación automática desde Europe PMC y Semantic Scholar. Incluye un panel editorial para gestionar contenidos, diseño adaptable y buscador por DOI o palabra clave.

---

## 🚀 Características principales

- Noticias científicas con imagen, resumen y enlace al paper original
- Importación automática desde DOI (Europe PMC y Semantic Scholar)
- Panel de administración con login, edición y eliminación
- Buscador por palabra clave o DOI
- Categorías temáticas: IA, neurociencia, salud, espacio
- Diseño adaptable y modular
- Página promocional (`landing.html`)

---

## 📁 Estructura del proyecto

ciencia-hoy/ ├── index.html # Página principal ├── categoria.php # Filtrado por categoría ├── noticia.php # Vista detallada ├── buscar.php # Buscador ├── landing.html # Página promocional │ ├── admin/ # Panel editorial │ ├── login.php │ ├── dashboard.php │ ├── nuevo.php │ ├── editar.php │ ├── eliminar.php │ ├── logout.php │ └── auth.php │ ├── php/ │ └── conexion.php # Conexión a la base de datos │ ├── css/ │ └── estilo.css # Estilos base │ ├── js/ │ └── script.js # Funciones JS │ ├── imagenes/ │ └── descarga.jpg # Imagen por defecto │ ├── sql/ │ └── estructura.sql # Script de base de datos


---

## 🛠 Instalación

1. Clona el repositorio o descarga el ZIP.
2. Crea una base de datos MySQL llamada `ciencia_hoy`.
3. Importa el archivo `sql/estructura.sql`.
4. Configura tus credenciales en `php/conexion.php`.
5. Accede al panel desde `/admin/login.php` con:

Usuario: admin Contraseña: admin123

Usuario: admin Contraseña: admin123

Código