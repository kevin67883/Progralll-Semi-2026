# Backend en Python puro (sin Flask ni Django).
# Requiere:  python -m pip install mysql-connector-python
# Ejecutar:  python app.py   ->   http://127.0.0.1:5000
import os, json, hashlib, secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import mysql.connector

# Configuración por defecto de XAMPP
DB_CONFIG = dict(host="localhost", port=3306, user="root", password="", database="db_academica")
TABLA = "usuarios_usss027225"      # cambie por su código de estudiante
BASE = os.path.dirname(os.path.abspath(__file__))
SESIONES = {}                       # sid -> nombre de usuario
TIPOS = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".png": "image/png"}


def conectar():
    return mysql.connector.connect(**DB_CONFIG)


def encriptar(clave):
    # MD5 = 32 caracteres, cabe en char(35)
    return hashlib.md5(clave.encode("utf-8")).hexdigest()


class Usuarios:
    """Clase del CRUD de usuarios."""

    def validar_login(self, usuario, clave):
        con = conectar()
        try:
            cur = con.cursor()
            cur.execute(f"SELECT idUsuario FROM {TABLA} WHERE usuario=%s AND clave=%s",
                        (usuario, encriptar(clave)))
            return cur.fetchone() is not None
        finally:
            con.close()

    def crud_usuarios_usss027225(self, d):   # cambie por su código de estudiante
        accion = d.get("accion")
        con = conectar()
        try:
            cur = con.cursor(dictionary=True)

            if accion == "buscar":
                texto = f"%{(d.get('texto') or '').strip()}%"
                cur.execute(
                    f"SELECT idUsuario, usuario, nombre, direccion, telefono FROM {TABLA} "
                    "WHERE usuario LIKE %s OR nombre LIKE %s ORDER BY idUsuario", (texto, texto))
                return {"ok": True, "datos": cur.fetchall()}

            if accion == "eliminar":
                cur.execute(f"DELETE FROM {TABLA} WHERE idUsuario=%s", (d.get("idUsuario"),))
                con.commit()
                return {"ok": True, "msg": "Usuario eliminado"}

            if accion in ("guardar", "modificar"):
                usuario = (d.get("usuario") or "").strip()
                clave = d.get("clave") or ""
                nombre = (d.get("nombre") or "").strip()
                direccion = (d.get("direccion") or "").strip()
                telefono = (d.get("telefono") or "").strip()

                if not usuario or not nombre:
                    return {"ok": False, "msg": "Usuario y nombre son obligatorios"}
                if len(usuario) > 35 or len(nombre) > 85 or len(direccion) > 100 or len(telefono) > 9:
                    return {"ok": False, "msg": "Algún campo excede la longitud permitida"}

                # Evitar usuarios repetidos
                cur.execute(f"SELECT idUsuario FROM {TABLA} WHERE usuario=%s", (usuario,))
                existente = cur.fetchone()
                if existente and str(existente["idUsuario"]) != str(d.get("idUsuario") or ""):
                    return {"ok": False, "msg": "Ese usuario ya existe"}

                if accion == "guardar":
                    if not clave:
                        return {"ok": False, "msg": "La clave es obligatoria"}
                    cur.execute(
                        f"INSERT INTO {TABLA} (usuario, clave, nombre, direccion, telefono) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (usuario, encriptar(clave), nombre, direccion, telefono))
                    msg = "Usuario guardado"
                else:
                    if clave:   # si la clave viene vacía se conserva la anterior
                        cur.execute(
                            f"UPDATE {TABLA} SET usuario=%s, clave=%s, nombre=%s, direccion=%s, telefono=%s "
                            "WHERE idUsuario=%s",
                            (usuario, encriptar(clave), nombre, direccion, telefono, d.get("idUsuario")))
                    else:
                        cur.execute(
                            f"UPDATE {TABLA} SET usuario=%s, nombre=%s, direccion=%s, telefono=%s "
                            "WHERE idUsuario=%s",
                            (usuario, nombre, direccion, telefono, d.get("idUsuario")))
                    msg = "Usuario modificado"
                con.commit()
                return {"ok": True, "msg": msg}

            return {"ok": False, "msg": "Acción no válida"}
        except mysql.connector.Error as e:
            return {"ok": False, "msg": f"Error de base de datos: {e}"}
        finally:
            con.close()


crud = Usuarios()


class Handler(BaseHTTPRequestHandler):
    def sesion(self):
        c = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        return SESIONES.get(c["sid"].value) if "sid" in c else None

    def responder(self, codigo, cuerpo, tipo="application/json", extra=None):
        data = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo if tipo.startswith("image/") else tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def json(self, obj, codigo=200, extra=None):
        self.responder(codigo, json.dumps(obj, default=str), extra=extra)

    def redirigir(self, destino):
        self.responder(302, "", "text/plain", {"Location": destino})

    def archivo(self, carpeta, nombre):
        ruta = os.path.normpath(os.path.join(BASE, carpeta, nombre))
        if not ruta.startswith(os.path.join(BASE, carpeta)) or not os.path.isfile(ruta):
            return self.responder(404, "No encontrado", "text/plain")
        with open(ruta, "rb") as f:
            self.responder(200, f.read(), TIPOS.get(os.path.splitext(ruta)[1], "text/plain"))

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/":                          # el login es lo primero que se muestra
            if self.sesion():
                return self.redirigir("/usuarios")
            return self.archivo("templates", "login.html")
        if ruta == "/usuarios":
            if not self.sesion():
                return self.redirigir("/")
            return self.archivo("templates", "usuarios.html")
        if ruta == "/sesion":
            u = self.sesion()
            return self.json({"ok": bool(u), "usuario": u})
        if ruta == "/logout":
            c = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            if "sid" in c:
                SESIONES.pop(c["sid"].value, None)
            return self.redirigir("/")
        if ruta.startswith("/static/"):
            return self.archivo("static", ruta[len("/static/"):])
        self.responder(404, "No encontrado", "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            d = json.loads(self.rfile.read(n) or "{}")
        except ValueError:
            d = {}

        if self.path == "/validar_login":
            usuario = (d.get("usuario") or "").strip()
            clave = d.get("clave") or ""
            if not usuario or not clave:
                return self.json({"ok": False, "msg": "Ingrese usuario y clave"})
            try:
                valido = crud.validar_login(usuario, clave)
            except mysql.connector.Error as e:
                return self.json({"ok": False, "msg": f"Error de base de datos: {e}"})
            if valido:
                sid = secrets.token_hex(16)
                SESIONES[sid] = usuario
                return self.json({"ok": True}, extra={"Set-Cookie": f"sid={sid}; Path=/; HttpOnly"})
            return self.json({"ok": False, "msg": "Acceso denegado: usuario o clave incorrectos"})

        if self.path == "/crud_usuarios_usss027225":   # cambie por su código
            if not self.sesion():
                return self.json({"ok": False, "msg": "Sesión no válida", "login": True}, 401)
            return self.json(crud.crud_usuarios_usss027225(d))

        self.json({"ok": False, "msg": "Ruta no válida"}, 404)

    def log_message(self, fmt, *args):
        pass


def asegurar_usuario_inicial():
    # Crea la tabla y el usuario inicial si no existen. Queda guardado en MySQL.
    try:
        con = conectar()
        try:
            cur = con.cursor()
            cur.execute(f"""CREATE TABLE IF NOT EXISTS {TABLA} (
                idUsuario INT(10) NOT NULL AUTO_INCREMENT,
                usuario CHAR(35), clave CHAR(35), nombre CHAR(85),
                direccion CHAR(100), telefono CHAR(9), PRIMARY KEY (idUsuario))""")
            cur.execute(f"SELECT idUsuario FROM {TABLA} WHERE usuario=%s", ("admin",))
            if cur.fetchone() is None:
                cur.execute(f"INSERT INTO {TABLA} (usuario, clave, nombre, direccion, telefono) "
                            "VALUES (%s,%s,%s,%s,%s)",
                            ("admin", encriptar("usss027225"), "Administrador", "Usulután", "7777-7777"))
            con.commit()
        finally:
            con.close()
    except mysql.connector.Error as e:
        print("No se pudo conectar a MySQL. Encienda MySQL en XAMPP:", e)


if __name__ == "__main__":
    asegurar_usuario_inicial()
    print("Servidor en http://127.0.0.1:5000  (Ctrl+C para detener)")
    print("Ingrese con -> Usuario: admin | Clave: usss027225")
    ThreadingHTTPServer(("127.0.0.1", 5000), Handler).serve_forever()