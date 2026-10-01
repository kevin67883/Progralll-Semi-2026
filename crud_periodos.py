import conexion
from decimal import Decimal, ROUND_HALF_UP
import math

db = conexion.Conexion()


class crud_periodos:

    def consultar(self, buscar=""):
        sql = """
            SELECT p.*, c.nombre AS nombreCliente, pr.nombre AS nombreProducto
            FROM periodos p
            JOIN clientes  c  ON c.idCliente  = p.idCliente
            JOIN productos pr ON pr.idProducto = p.idProducto
            WHERE c.nombre LIKE %s OR c.codigo LIKE %s
            ORDER BY p.desde DESC
        """
        like = f"%{buscar}%"
        return db.consultar(sql, (like, like))

    def obtener_tarifa(self, idProducto, balance, fechaDesde):
        sql = """
            SELECT * FROM tarifas
            WHERE idProducto = %s
              AND vigenciaDesde <= %s
              AND desde <= %s AND hasta >= %s
        """
        return db.consultar(sql, (idProducto, fechaDesde, balance, balance))

    def hay_superposicion(self, idCliente, idProducto, desde, hasta, idPeriodo=None):
        sql = """
            SELECT COUNT(*) AS n FROM periodos
            WHERE idCliente = %s AND idProducto = %s
              AND desde < %s AND hasta > %s
        """
        datos = [idCliente, idProducto, hasta, desde]
        if idPeriodo:
            sql += " AND idPeriodo <> %s"
            datos.append(idPeriodo)
        r = db.consultar(sql, tuple(datos))
        return r[0]["n"] > 0 if r else False

    def es_empresa(self, idCliente):
        try:
            idCliente = int(idCliente)
        except (TypeError, ValueError):
            return False
        r = db.consultar("SELECT tipo FROM clientes WHERE idCliente = %s", (idCliente,))
        if not r:
            return False
        return str(r[0]["tipo"]).strip().lower() == "empresa"

    def calcular(self, balance, tarifa):
        balance = Decimal(str(balance))
        desde   = Decimal(str(tarifa["desde"]))
        base    = Decimal(str(tarifa["precioBase"]))
        adic    = Decimal(str(tarifa["adicional"]))
        pct     = Decimal(str(tarifa["porcentaje"]))

        if pct > 0:
            precio  = balance * pct / Decimal("100")
            detalle = f"{balance} x {pct}/100"
            return precio.quantize(Decimal("0.01"), ROUND_HALF_UP), "porcentaje", detalle

        excedente = balance - desde
        bloques = 0 if excedente <= 0 else math.ceil(float(excedente) / 1000)
        precio = base + (Decimal(bloques) * adic)
        detalle = f"{base}+({bloques}*{adic})"
        return precio.quantize(Decimal("0.01"), ROUND_HALF_UP), "bloque", detalle

    def previsualizar(self, idCliente, idProducto, balance, desde):
        if not self.es_empresa(idCliente):
            return {"msg": "El Impuesto a las Actividades Economicas requiere un cliente de tipo empresa."}
        try:
            balance = Decimal(str(balance))
        except Exception:
            return {"msg": "Ingrese un balance mayor que cero."}
        if balance <= 0:
            return {"msg": "Ingrese un balance mayor que cero."}

        tarifas = self.obtener_tarifa(idProducto, balance, desde)
        if len(tarifas) == 0:
            return {"msg": "No existe una tarifa configurada para el balance indicado."}
        if len(tarifas) > 1:
            return {"msg": "Existe mas de una tarifa aplicable. Corrija la tabla tarifaria."}

        t = tarifas[0]
        precio, formula, detalle = self.calcular(balance, t)
        return {
            "msg": "ok",
            "precio": float(precio),
            "formula": formula,
            "detalle": detalle,
            "tarifa": {
                "desde":       float(t["desde"]),
                "hasta":       float(t["hasta"]),
                "precioBase":  float(t["precioBase"]),
                "adicional":   float(t["adicional"]),
                "porcentaje":  float(t["porcentaje"]),
            }
        }

    def administrar(self, datos):
        try:
            accion = datos["accion"]

            if accion == "calcular":
                r = self.previsualizar(datos["idCliente"], datos["idProducto"],
                                       datos["balance"], datos["desde"])
                return "ok" if r.get("msg") == "ok" else r.get("msg")

            if accion in ("nuevo", "modificar"):
                if not self.es_empresa(datos["idCliente"]):
                    return "El Impuesto a las Actividades Economicas requiere un cliente de tipo empresa."

                balance = Decimal(str(datos["balance"]))
                if balance <= 0:
                    return "Ingrese un balance mayor que cero."
                if datos["desde"] >= datos["hasta"]:
                    return "La fecha Hasta debe ser posterior a la fecha Desde."

                if self.hay_superposicion(datos["idCliente"], datos["idProducto"],
                                          datos["desde"], datos["hasta"],
                                          datos.get("idPeriodo")):
                    return "El periodo indicado se superpone con un periodo existente."

                tarifas = self.obtener_tarifa(datos["idProducto"], balance, datos["desde"])
                if len(tarifas) == 0:
                    return "No existe una tarifa configurada para el balance indicado."
                if len(tarifas) > 1:
                    return "Existe mas de una tarifa aplicable. Corrija la tabla tarifaria."

                t = tarifas[0]
                precio, formula, detalle = self.calcular(balance, t)

                if accion == "nuevo":
                    sql = """
                        INSERT INTO periodos
                        (idCliente,idProducto,desde,hasta,balance,cantidad,precio,subtotal,
                         idTarifaAplicada,formula,detalleCalculo,estado)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'vigente')
                    """
                    valores = (datos["idCliente"], datos["idProducto"], datos["desde"],
                               datos["hasta"], balance, 1.00, precio, precio,
                               t["idTarifa"], formula, detalle)
                else:
                    sql = """
                        UPDATE periodos SET
                            desde=%s, hasta=%s, balance=%s, precio=%s, subtotal=%s,
                            idTarifaAplicada=%s, formula=%s, detalleCalculo=%s
                        WHERE idPeriodo=%s
                    """
                    valores = (datos["desde"], datos["hasta"], balance, precio, precio,
                               t["idTarifa"], formula, detalle, datos["idPeriodo"])
                return db.ejecutar(sql, valores)

            return db.ejecutar("DELETE FROM periodos WHERE idPeriodo=%s",
                               (datos["idPeriodo"],))
        except Exception as e:
            return f"Error: {e}"