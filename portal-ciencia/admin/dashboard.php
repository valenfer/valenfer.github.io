<?php
session_start();
require_once '../php/conexion.php';
require_once 'auth.php';
// Lógica del panel de administración
?><?php
session_start();
include("auth.php");
include("../php/conexion.php");
?>

<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Panel de administración – Ciencia Hoy</title>
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
    .acciones {
      text-align: center;
      margin: 2em;
    }
    .acciones a {
      background-color: #00ffe0;
      color: #0f111a;
      padding: 0.8em 1.5em;
      border-radius: 8px;
      text-decoration: none;
      font-weight: bold;
      margin: 0 1em;
    }
    table {
      width: 90%;
      margin: auto;
      border-collapse: collapse;
      background-color: #fff;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    th, td {
      padding: 1em;
      border-bottom: 1px solid #ccc;
      text-align: left;
    }
    th {
      background-color: #e0e0e0;
    }
    tr:hover {
      background-color: #f9f9f9;
    }
    .acciones-tabla a {
      margin-right: 1em;
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
    <h1>Panel de administración</h1>
    <p>Gestión de noticias científicas</p>
  </header>

  <div class="acciones">
    <a href="nuevo.php">➕ Nueva noticia</a>
    <a href="logout.php">🔒 Cerrar sesión</a>
  </div>

  <table>
    <tr>
      <th>ID</th>
      <th>Título</th>
      <th>Categoría</th>
      <th>Fecha</th>
      <th>Acciones</th>
    </tr>
    <?php
      $result = $conn->query("SELECT * FROM noticias ORDER BY fecha DESC");
      while($row = $result->fetch_assoc()) {
        echo "<tr>
                <td>{$row['id']}</td>
                <td>{$row['titulo']}</td>
                <td>{$row['categoria']}</td>
                <td>{$row['fecha']}</td>
                <td class='acciones-tabla'>
                  <a href='editar.php?id={$row['id']}'>✏️ Editar</a>
                  <a href='eliminar.php?id={$row['id']}' onclick='return confirm(\"¿Eliminar esta noticia?\")'>🗑 Eliminar</a>
                </td>
              </tr>";
      }
    ?>
  </table>

  <footer>
    © 2025 Ciencia Hoy · Panel editorial
  </footer>
</body>
</html>
