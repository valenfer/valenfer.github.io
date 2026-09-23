<?php
session_start();
include("auth.php");
include("../php/conexion.php");

$id = $_GET['id'] ?? 0;

// Validar que el ID sea numérico
if (!is_numeric($id)) {
  echo "ID inválido.";
  exit();
}

// Eliminar la noticia
$stmt = $conn->prepare("DELETE FROM noticias WHERE id = ?");
$stmt->bind_param("i", $id);
$stmt->execute();

// Redirigir al panel
header("Location: dashboard.php");
exit();
