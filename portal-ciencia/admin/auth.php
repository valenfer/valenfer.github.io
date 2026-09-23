<?php
session_start();
// Verificar si el usuario está autenticado
function verificarAutenticacion() {
    if (!isset($_SESSION['usuario_id'])) {
        header('Location: login.php');
        exit();
    }
}
?>