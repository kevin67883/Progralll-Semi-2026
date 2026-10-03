-- Importar en phpMyAdmin (pestaña Importar o SQL). Crea toda la base desde cero.
DROP DATABASE IF EXISTS db_sistema_impuestos;
CREATE DATABASE db_sistema_impuestos DEFAULT CHARSET utf8mb4;
USE db_sistema_impuestos;

CREATE TABLE IF NOT EXISTS clientes (
  idCliente INT(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  codigo CHAR(10) NOT NULL,
  nombre CHAR(100) NOT NULL,
  direccion CHAR(150) NOT NULL,
  telefono CHAR(10) NOT NULL,
  email CHAR(150) NOT NULL,
  tipo CHAR(10) NOT NULL DEFAULT 'particular'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS productos (
  idProducto INT NOT NULL PRIMARY KEY,           -- 11801 / 11802
  nombre VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tarifas (
  idTarifa INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  idProducto INT NOT NULL,
  rangoDesde DECIMAL(14,2) NOT NULL,
  rangoHasta DECIMAL(14,2) NOT NULL,
  precioBase DECIMAL(14,6) NOT NULL,
  adicional DECIMAL(14,6) NOT NULL DEFAULT 0,
  porcentaje DECIMAL(9,6) NOT NULL DEFAULT 0,
  formula ENUM('bloque','porcentaje') NOT NULL DEFAULT 'bloque',
  vigenteDesde DATE NOT NULL,
  vigenteHasta DATE NULL,
  FOREIGN KEY (idProducto) REFERENCES productos(idProducto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS periodos (
  idPeriodo INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  idCliente INT(10) NOT NULL,
  idProducto INT NOT NULL,
  desde DATE NOT NULL,
  hasta DATE NOT NULL,
  balance DECIMAL(14,2) NOT NULL,
  cantidad DECIMAL(10,2) NOT NULL DEFAULT 1.00,
  precio DECIMAL(14,6) NOT NULL,                 -- se guarda; nunca se recalcula
  subtotal DECIMAL(14,6) NOT NULL,
  idTarifaAplicada INT NOT NULL,
  formula VARCHAR(20) NOT NULL,
  detalleCalculo VARCHAR(255) NOT NULL,
  facturado TINYINT(1) NOT NULL DEFAULT 0,
  fechaCalculo DATETIME NOT NULL,
  CHECK (desde < hasta),
  FOREIGN KEY (idCliente) REFERENCES clientes(idCliente),
  FOREIGN KEY (idProducto) REFERENCES productos(idProducto),
  FOREIGN KEY (idTarifaAplicada) REFERENCES tarifas(idTarifa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO productos VALUES
 (11801,'Impuesto a las Actividades Económicas Comercio'),
 (11802,'Impuesto a las Actividades Económicas Industria');

INSERT INTO clientes(codigo,nombre,direccion,telefono,email,tipo) VALUES
 ('C001','Empresa de Prueba S.A.','San Salvador','2222-0000','prueba@correo.com','empresa');

-- Tarifas de Industria (11802). Falta el rango 6,000.01 a 8,000.00 (pendiente de aprobación).
INSERT INTO tarifas (idProducto,rangoDesde,rangoHasta,precioBase,adicional,porcentaje,formula,vigenteDesde) VALUES
 (11802,0.01,500.00,1.50,0.00,0,'bloque','2000-01-01'),
 (11802,500.01,1000.00,1.50,3.00,0,'bloque','2000-01-01'),
 (11802,1000.01,2000.00,3.00,3.00,0,'bloque','2000-01-01'),
 (11802,2000.01,3000.00,6.00,3.00,0,'bloque','2000-01-01'),
 (11802,3000.01,6000.00,9.00,2.00,0,'bloque','2000-01-01'),
 (11802,8000.01,18000.00,15.00,2.00,0,'bloque','2000-01-01'),
 (11802,18000.01,30000.00,39.00,2.00,0,'bloque','2000-01-01'),
 (11802,30000.01,60000.00,63.00,1.00,0,'bloque','2000-01-01'),
 (11802,60000.01,100000.00,93.00,0.80,0,'bloque','2000-01-01'),
 (11802,100000.01,200000.00,125.00,0.70,0,'bloque','2000-01-01'),
 (11802,200000.01,300000.00,195.00,0.60,0,'bloque','2000-01-01'),
 (11802,300000.01,400000.00,255.00,0.45,0,'bloque','2000-01-01'),
 (11802,400000.01,500000.00,300.00,0.40,0,'bloque','2000-01-01'),
 (11802,500000.01,1000000.00,340.00,0.30,0,'bloque','2000-01-01'),
 (11802,1000000.01,99999999.99,490.00,0.18,0,'bloque','2000-01-01');

-- Comercio (11801): se copia la misma tabla mientras se confirma la tarifa propia.
INSERT INTO tarifas (idProducto,rangoDesde,rangoHasta,precioBase,adicional,porcentaje,formula,vigenteDesde)
 SELECT 11801,rangoDesde,rangoHasta,precioBase,adicional,porcentaje,formula,vigenteDesde
 FROM tarifas WHERE idProducto=11802; 