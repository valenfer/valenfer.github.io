<?php
session_start();
require_once '../php/conexion.php';
require_once 'auth.php';
// Lógica para editar noticia
?><?php
session_start();
include("auth.php");
include("../php/conexion.php");

$id = $_GET['id'] ?? 0;
$stmt = $conn->prepare("SELECT * FROM noticias WHERE id = ?");
$stmt->bind_param("i", $id);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows != 1) {
  echo "Noticia no encontrada.";
  exit();
}

$row = $result->fetch_assoc();
$titulo = $row['titulo'];
$subtitulo = $row['subtitulo'];
$contenido = $row['contenido'];
$categoria = $row['categoria'];
$imagen = $row['imagen'];
$doi = $row['doi'];
$enlace_paper = $row['enlace_paper'];
$error = "";

// Importar desde Europe PMC
if (isset($_POST['importar_epmc']) && !empty($_POST['doi'])) {
  $doi = urlencode(trim($_POST['doi']));
  $url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:$doi&format=json";
  $json = file_get_contents($url);
  $data = json_decode($json, true);
  if (!empty($data['resultList']['result'][0])) {
    $paper = $data['resultList']['result'][0];
    $titulo = $paper['title'] ?? $titulo;
    $subtitulo = "Autores: " . ($paper['authorString'] ?? $subtitulo);
    $contenido = $paper['abstractText'] ?? $contenido;
    $enlace_paper = $paper['fullTextUrlList']['fullTextUrl'][0]['url'] ?? $enlace_paper;
  } else {
    $error = "No se encontró información en Europe PMC.";
  }
}

// Importar desde Semantic Scholar
if (isset($_POST['importar_ss']) && !empty($_POST['doi'])) {
  $doi = urlencode(trim($_POST['doi']));
  $url = "https://api.semanticscholar.org/graph/v1/paper/$doi?fields=title,authors,abstract,url";
  $json = file_get_contents($url);
  $data = json_decode($json, true);
  if (!empty($data['title'])) {
    $titulo = $data['title'];
    $autores = array_map(fn($a) => $a['name'], $data['authors'] ?? []);
    $subtitulo = "Autores: " . implode(", ", $autores);
    $contenido = $data['abstract'] ?? $contenido;
    $enlace_paper = $data['url'] ?? $enlace_paper;
  } else {
    $error = "No se encontró información en Semantic Scholar.";
  }
}

// Guardar cambios
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['guardar'])) {
  $titulo = trim($_POST['titulo']);
  $subtitulo = trim($_POST['subtitulo']);
  $contenido = trim($_POST['contenido']);
  $categoria = $_POST['categoria'];
  $doi = trim($_POST['doi']);
  $enlace_paper = trim($_POST['enlace_paper']);

  // Subida de nueva imagen
  if (isset($_FILES['imagen']) && $_FILES['imagen']['error'] == 0) {
    $nombre = basename($_FILES['imagen']['name']);
    $ruta = "../imagenes/" . time() . "_" . $nombre;
    if (move_uploaded_file($_FILES['imagen']['tmp_name'], $ruta)) {
      $imagen = $ruta;
    }
  }

  $stmt = $conn->prepare("UPDATE noticias SET titulo=?, subtitulo=?, contenido=?, categoria=?, imagen=?, doi=?, enlace_paper=? WHERE id=?");
  $stmt->bind_param("sssssssi", $titulo, $subtitulo, $contenido, $categoria, $imagen, $doi, $enlace_paper, $id);
  $stmt->execute();
  header("Location: dashboard.php");
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Editar noticia – Ciencia Hoy</title>
  <link rel="stylesheet" href="../css/estilo.css">
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
      max-width: 700px;
      margin: 2em auto;
      background-color: #fff;
      padding: 2em;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    input, textarea, select, button {
      width: 100%;
      margin-bottom: 1em;
      padding: 0.8em;
      border-radius: 8px;
      border: 1px solid #ccc;
    }
    button {
      background-color: #00ffe0;
      border: none;
      font-weight: bold;
      cursor: pointer;
    }
    .botones-importar {
      display: flex;
      gap: 1em;
      margin-bottom: 1em;
    }
    .error {
      color: #ff5050;
      text-align: center;
      margin-bottom: 1em;
    }
    .imagen-actual {
      text-align: center;
      margin-bottom: 1em;
    }
    .imagen-actual img {
      max-width: 300px;
      border-radius: 10px;
    }
  </style>
</head>
<body>
  <header>
    <h1>Editar noticia</h1>
    <p>Modifica el contenido o importa desde DOI</p>
  </header>

  <form method="POST" enctype="multipart/form-data">
    <?php if ($error): ?>
      <div class="error"><?php echo $error; ?></div>
    <?php endif; ?>

    <input type="text" name="titulo" placeholder="Título" value="<?php echo $titulo; ?>" required>
    <input type="text" name="subtitulo" placeholder="Subtítulo" value="<?php echo $subtitulo; ?>" required>
    <textarea name="contenido" rows="8" placeholder="Contenido" required><?php echo $contenido; ?></textarea>
    <select name="categoria" required>
      <option value="">Selecciona categoría</option>
      <option value="ia" <?php if($categoria=="ia") echo "selected"; ?>>Inteligencia Artificial</option>
      <option value="neurociencia" <?php if($categoria=="neurociencia") echo "selected"; ?>>Neurociencia</option>
      <option value="salud" <?php if($categoria=="salud") echo "selected"; ?>>Salud</option>
      <option value="espacio" <?php if($categoria=="espacio") echo "selected"; ?>>Espacio</option>
    </select>

    <div class="imagen-actual">
      <p>Imagen actual:</p>
      <img src="<?php echo $imagen; ?>" alt="Imagen actual">
    </div>
    <input type="file" name="imagen" accept="image/*">

    <input type="text" name="doi" placeholder="DOI del paper" value="<?php echo $doi; ?>">
    <div class="botones-importar">
      <button type="submit" name="importar_epmc">Importar desde Europe PMC</button>
      <button type="submit" name="importar_ss">Importar desde Semantic Scholar</button>
    </div>

    <input type="text" name="enlace_paper" placeholder="Enlace al estudio original" value="<?php echo $enlace_paper; ?>">

    <button type="submit" name="guardar">Guardar cambios</button>
  </form>
</body>
</html>
