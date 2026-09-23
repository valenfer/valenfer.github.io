<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Noticia científica – Ciencia Hoy</title>
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
    .contenido {
      max-width: 800px;
      margin: 2em auto;
      background-color: #fff;
      padding: 2em;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .contenido img {
      width: 100%;
      max-height: 400px;
      object-fit: cover;
      border-radius: 10px;
      margin-bottom: 1em;
    }
    .contenido h2 {
      margin-top: 0;
      color: #0f111a;
    }
    .contenido p {
      font-size: 1em;
      color: #333;
      line-height: 1.6em;
    }
    .meta {
      font-size: 0.9em;
      color: #666;
      margin-bottom: 1em;
    }
    .enlace-paper {
      margin-top: 1em;
      font-size: 0.95em;
    }
    .enlace-paper a {
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
    <h1>Ciencia Hoy</h1>
    <p>Detalle completo de la noticia científica</p>
  </header>

  <div class="contenido">
    <?php
      include("php/conexion.php");
      $id = $_GET['id'] ?? 0;
      $stmt = $conn->prepare("SELECT * FROM noticias WHERE id = ?");
      $stmt->bind_param("i", $id);
      $stmt->execute();
      $result = $stmt->get_result();

      if ($result->num_rows == 1) {
        $row = $result->fetch_assoc();
        echo "<img src='{$row['imagen']}' alt='Imagen noticia'>";
        echo "<h2>{$row['titulo']}</h2>";
        echo "<p class='meta'><strong>Categoría:</strong> {$row['categoria']} · <strong>Fecha:</strong> {$row['fecha']}</p>";
        echo "<p><em>{$row['subtitulo']}</em></p>";
        echo "<p>{$row['contenido']}</p>";

        if (!empty($row['doi'])) {
          echo "<p class='enlace-paper'><strong>DOI:</strong> {$row['doi']}</p>";
        }
        if (!empty($row['enlace_paper'])) {
          echo "<p class='enlace-paper'><a href='{$row['enlace_paper']}' target='_blank'>Ver estudio original</a></p>";
        }
      } else {
        echo "<p>Noticia no encontrada.</p>";
      }
    ?>
  </div>

  <footer>
    © 2025 Ciencia Hoy · Proyecto de divulgación científica
  </footer>
</body>
</html>
