CREATE DATABASE IF NOT EXISTS db_academica;
USE db_academica;

-- Cambie usis018804 por su código de estudiante
CREATE TABLE IF NOT EXISTS usuarios_usis018804 (
    idUsuario INT(10) NOT NULL AUTO_INCREMENT,
    usuario   CHAR(35),
    clave     CHAR(35),
    nombre    CHAR(85),
    direccion CHAR(100),
    telefono  CHAR(9),
    PRIMARY KEY (idUsuario)
);

-- Usuario inicial (clave: admin123, guardada en MD5). Ejecutar una sola vez.
INSERT INTO usuarios_usis018804 (usuario, clave, nombre, direccion, telefono)
VALUES ('admin', MD5('admin123'), 'Administrador', 'Usulután', '7777-7777');