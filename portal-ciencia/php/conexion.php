<?php
$host = "localhost";
$user = "ciencia_hoy";
$pass = "ciencia_hoy";
$db   = "ciencia_hoy";

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
  die("Error de conexión: " . $conn->connect_error);
}
?>
