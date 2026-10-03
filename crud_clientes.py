from mysql.connector import Error
import conexion

db = conexion.Conexion()


class crud_clientes:
    def consultar(self, buscar):
        like = f"%{buscar}%"
        return db.consultar(
            "SELECT * FROM clientes WHERE nombre LIKE %s OR codigo LIKE %s", (like, like))

    def administrar(self, datos):
        try:
            accion = datos['accion']
            if accion in ('nuevo', 'modificar') and datos.get('tipo') not in ('particular', 'empresa'):
                return "Tipo de cliente inválido."
            if accion == 'nuevo':
                sql = """INSERT INTO clientes(codigo,nombre,direccion,telefono,email,tipo)
                         VALUES(%s,%s,%s,%s,%s,%s)"""
                valores = (datos['codigo'], datos['nombre'], datos['direccion'],
                           datos['telefono'], datos['email'], datos['tipo'])
            elif accion == 'modificar':
                sql = """UPDATE clientes SET codigo=%s,nombre=%s,direccion=%s,telefono=%s,email=%s,tipo=%s
                         WHERE idCliente=%s"""
                valores = (datos['codigo'], datos['nombre'], datos['direccion'],
                           datos['telefono'], datos['email'], datos['tipo'], datos['idCliente'])
            else:
                usados = db.consultar(
                    "SELECT 1 FROM periodos WHERE idCliente=%s LIMIT 1", (datos['idCliente'],))
                if usados:
                    return "No se puede eliminar un cliente con períodos registrados."
                sql = "DELETE FROM clientes WHERE idCliente=%s"
                valores = (datos['idCliente'],)
            return db.ejecutar(sql, valores)
        except Error as e:
            return f"Error al guardar el cliente: {e}" 