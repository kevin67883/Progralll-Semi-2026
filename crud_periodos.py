from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from mysql.connector import Error
import conexion
import motor_calculo

db = conexion.Conexion()

SELECT = """
    SELECT p.idPeriodo, p.idCliente, p.idProducto, p.desde, p.hasta, p.balance, p.cantidad,
      p.precio, p.subtotal, p.idTarifaAplicada, p.formula, p.detalleCalculo,
      CASE WHEN CURDATE() < p.desde THEN 'futuro'
           WHEN CURDATE() >= p.hasta THEN 'historico' ELSE 'vigente' END AS estado,
      p.facturado, p.fechaCalculo, c.nombre AS nombreCliente, pr.nombre AS nombreProducto
    FROM periodos p
    JOIN clientes c ON c.idCliente = p.idCliente
    JOIN productos pr ON pr.idProducto = p.idProducto
"""


def _num(v):
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return Decimal(0)


def _fecha(v):
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        return None


class crud_periodos:
    def productos(self):
        return db.consultar("SELECT idProducto, nombre FROM productos ORDER BY idProducto")

    def consultar(self, idCliente=None):
        if idCliente:
            return db.consultar(SELECT + " WHERE p.idCliente=%s ORDER BY p.desde", (idCliente,))
        return db.consultar(SELECT + " ORDER BY p.idCliente, p.desde")

    def _tarifa(self, idProducto, balance, fecha):
        """Devuelve (tarifa, None) o (None, mensaje). Nunca usa un precio general."""
        filas = db.consultar(
            """SELECT * FROM tarifas WHERE idProducto=%s AND rangoDesde<=%s AND %s<=rangoHasta
               AND vigenteDesde<=%s AND (vigenteHasta IS NULL OR vigenteHasta>%s)""",
            (idProducto, balance, balance, fecha, fecha))
        if not filas:
            return None, "No existe una tarifa configurada para el balance indicado."
        if len(filas) > 1:
            return None, "Existe más de una tarifa aplicable. Corrija la tabla tarifaria."
        return filas[0], None

    def calcular(self, idProducto, balance, desde):
        balance = _num(balance)
        if not idProducto:
            return {'msg': 'Seleccione el producto.'}
        if balance <= 0:
            return {'msg': 'Ingrese un balance mayor que cero.'}
        t, error = self._tarifa(idProducto, balance, _fecha(desde) or date.today())
        if error:
            return {'msg': error}
        return {'msg': 'ok', 'detalle': motor_calculo.calcular(balance, t)}

    def administrar(self, d):
        try:
            cli = db.consultar("SELECT tipo FROM clientes WHERE idCliente=%s", (d.get('idCliente'),))
            if not cli or cli[0]['tipo'] != 'empresa':
                return "Seleccione una empresa."
            if not d.get('idProducto'):
                return "Seleccione el producto."
            balance = _num(d.get('balance'))
            if balance <= 0:
                return "Ingrese un balance mayor que cero."
            desde, hasta = _fecha(d.get('desde')), _fecha(d.get('hasta'))
            if not desde or not hasta or desde >= hasta:
                return "La fecha Hasta debe ser posterior a la fecha Desde."
            if db.consultar(
                    """SELECT 1 FROM periodos WHERE idCliente=%s AND idProducto=%s
                       AND desde<%s AND hasta>%s LIMIT 1""",
                    (d['idCliente'], d['idProducto'], hasta, desde)):
                return "El período se superpone con uno existente."
            t, error = self._tarifa(d['idProducto'], balance, desde)
            if error:
                return error
            r = motor_calculo.calcular(balance, t)
            cantidad = _num(d.get('cantidad') or 1)
            # Inserción única: el precio queda guardado y los históricos nunca se recalculan.
            return db.ejecutar(
                """INSERT INTO periodos(idCliente,idProducto,desde,hasta,balance,cantidad,precio,
                   subtotal,idTarifaAplicada,formula,detalleCalculo,fechaCalculo)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (d['idCliente'], d['idProducto'], desde, hasta, balance, cantidad, r['precio'],
                 cantidad * r['precio'], r['idTarifa'], r['formula'], r['detalleCalculo'],
                 datetime.now()))
        except Error as e:
            return f"Error al guardar el período: {e}"