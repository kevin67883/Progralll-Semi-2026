import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager


class Conexion:
    def __init__(self):
        self.config = dict(host="localhost", user="root", password="",
                           database="db_sistema_impuestos", autocommit=True)
        self.conexion = None
        self._conectar()

    def _conectar(self):
        try:
            self.conexion = mysql.connector.connect(**self.config)
            print("Conexion exitosa")
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")

    def _asegurar(self):
        try:
            self.conexion.ping(reconnect=True, attempts=2, delay=1)
        except Exception:
            self._conectar()

    def consultar(self, sql, params=None):
        self._asegurar()
        cursor = self.conexion.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def ejecutar(self, sql, datos):
        try:
            self._asegurar()
            cursor = self.conexion.cursor()
            cursor.execute(sql, datos)
            cursor.close()
            return 'ok'
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return f'Error: {e}'

    @contextmanager
    def transaccion(self):
        """Uso: with db.transaccion() as cur: cur.execute(...). Rollback si falla."""
        self._asegurar()
        self.conexion.start_transaction()
        cur = self.conexion.cursor(dictionary=True)
        try:
            yield cur
            self.conexion.commit()
        except Exception:
            self.conexion.rollback()
            raise
        finally:
            cur.close() 