<?php
session_start();
include("../php/conexion.php");

$error = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
  $usuario = trim($_POST['usuario']);
  $clave = trim($_POST['clave']);

  $stmt = $conn->prepare("SELECT * FROM usuarios WHERE usuario = ? AND clave = ?");
  $stmt->bind_param("ss", $usuario, $clave);
  $stmt->execute();
  $result = $stmt->get_result();

  if ($result->num_rows == 1) {
    $_SESSION['admin'] = $usuario;
    header("Location: dashboard.php");
    exit();
  } else {
    $error = "Usuario o contraseña incorrectos.";
  }
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Acceso al panel – Ciencia Hoy</title>
  <link rel="stylesheet" href="../css/estilo.css">
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      background-color: #0f111a;
      color: #e0e0e0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }
    .login-box {
      background-color: #1f2235;
      padding: 2em;
      border-radius: 10px;
      box-shadow: 0 0 10px #00ffe0;
      width: 300px;
    }
    h2 {
      text-align: center;
      color: #00ffe0;
    }
    input[type="text"], input[type="password"] {
      width: 100%;
      padding: 0.8em;
      margin: 1em 0;
      border: none;
      border-radius: 8px;
    }
    button {
      width: 100%;
      padding: 0.8em;
      background-color: #00ffe0;
      border: none;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
    }
    .error {
      color: #ff8080;
      text-align: center;
      margin-top: 1em;
    }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>Panel Ciencia Hoy</h2>
    <form method="POST">
      <input type="text" name="usuario" placeholder="Usuario" required>
      <input type="password" name="clave" placeholder="Contraseña" required>
      <button type="submit">Entrar</button>
    </form>
    <?php if ($error): ?>
      <div class="error"><?php echo $error; ?></div>
    <?php endif; ?>
  </div>
</body>
</html>
