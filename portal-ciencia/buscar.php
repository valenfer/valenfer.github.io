<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Buscar noticias – Ciencia Hoy</title>
  <link rel="stylesheet" href="css/estilo.css" />
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      background-color: #f4f4f4;
      margin: 0;
      padding: 0;
    }
    header {
      background-color: #0f111a;
      color: #00ffe0;
      padding: 2em;
      text-align: center;
    }
    form {
      text-align: center;
      margin: 2em;
    }
    input[type="text"] {
      padding: 0.8em;
      width: 60%;
      max-width: 400px;
      border: 1px solid #ccc;
      border-radius: 8px;
    }
    button {
      padding: 0.8em 1.5em;
      background-color: #00ffe0;
      border: none;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      margin-left: 1em;
    }
    .contenedor {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 2em;
      padding: 2em;
    }
    .tarjeta {
      background-color: #fff;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
      width: 300px;
      overflow: hidden;
      transition: transform 0.2s;
    }
    .tarjeta:hover {
      transform: scale(1.02);
    }
    .tarjeta img {
      width: 100%;
      height: 180px;
      object-fit: cover;
    }
    .tarjeta .contenido {
      padding: 1em;
    }
    .tarjeta h3 {
      margin-top: 0;
      color: #0f111a;
    }
    .tarjeta p {
      font-size: 0.9em;
      color: #555;
    }
    .tarjeta a {
      display: inline-block;
      margin-top: 1em;
      color: #00c0b0;
      text-decoration: none;
      font-weight: bold;
    }
    footer {
      text-align: center;
      padding: 2em;
      font-size: 0.9em;
      color: #888;
    }
  </style>
</head>
<body>
  <header>
    <h1>Buscar noticias científicas</h1>
    <p>Introduce una palabra clave o DOI para encontrar artículos relevantes</p>
  </header>

  <form method="GET">
    <input type="text" name="q" placeholder="Ej: neurociencia, 10.1038/s41586-020-2649-2" required />
    <button type="submit">Buscar</button>
  </form>

  <div class="contenedor">
    <?php
      include("php/conexion.php");
      $q = $_GET['q'] ?? '';

      if (!empty($q)) {
        $q_like = "%$q%";
        $stmt = $conn->prepare("SELECT * FROM noticias WHERE titulo LIKE ? OR subtitulo LIKE ? OR contenido LIKE ? OR doi LIKE ? ORDER BY fecha DESC");
        $stmt->bind_param("ssss", $q_like, $q_like, $q_like, $q_like);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result->num_rows > 0) {
          while($row = $result->fetch_assoc()) {
            echo "<div class='tarjeta'>
                    <img src='{$row['imagen']}' alt='Imagen noticia'>
                    <div class='contenido'>
                      <h3>{$row['titulo']}</h3>
                      <p>{$row['subtitulo']}</p>
                      <p><strong>Fecha:</strong> {$row['fecha']}</p>
                      <a href='noticia.php?id={$row['id']}'>Leer más</a>
                    </div>
                  </div>";
          }
        } else {
          echo "<p style='text-align:center;'>No se encontraron resultados para <strong>" . htmlspecialchars($q) . "</strong>.</p>";
        }
      }
    ?>
  </div>

  <footer>
    © 2025 Ciencia Hoy · Proyecto de divulgación científica
  </footer>
</body>
</html>
