-- ===============================
-- ESTRUCTURA DE BASE DE DATOS: CIENCIA HOY
-- ===============================

-- Crear base de datos (opcional si ya existe)
CREATE DATABASE IF NOT EXISTS ciencia_hoy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ciencia_hoy;

-- ===============================
-- Tabla: usuarios
-- ===============================
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario VARCHAR(50) NOT NULL UNIQUE,
  clave VARCHAR(100) NOT NULL
);

-- Usuario por defecto
INSERT INTO usuarios (usuario, clave) VALUES ('admin', 'admin123');

-- ===============================
-- Tabla: noticias
-- ===============================
CREATE TABLE IF NOT EXISTS noticias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(255) NOT NULL,
  subtitulo VARCHAR(255),
  contenido TEXT NOT NULL,
  categoria VARCHAR(50) NOT NULL,
  imagen VARCHAR(255),
  fecha DATE NOT NULL,
  doi VARCHAR(100),
  enlace_paper VARCHAR(255)
);
