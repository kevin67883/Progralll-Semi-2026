from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import crud_clientes
import crud_periodos

port = 3000
crudClientes = crud_clientes.crud_clientes()
crudPeriodos = crud_periodos.crud_periodos()
PAGINAS = ('/index.html', '/periodos.html')


class miServidor(SimpleHTTPRequestHandler):

    def _json(self, obj, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj, default=str).encode("utf-8"))

    def do_POST(self):
        try:
            longitud = int(self.headers.get('Content-Length', 0))
            datos = json.loads(self.rfile.read(longitud).decode("utf-8"))
            if self.path == "/cliente":
                respuesta = {'msg': crudClientes.administrar(datos)}
            elif self.path == "/periodo":
                respuesta = {'msg': crudPeriodos.administrar(datos)}
            else:
                return self._json({'msg': 'Ruta no encontrada'}, 404)
            self._json(respuesta)
        except Exception as e:
            self._json({'msg': f'Error: {e}'}, 500)

    def do_GET(self):
        url = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/clientes":
                return self._json(crudClientes.consultar(qs.get('buscar', '')))
            if url.path == "/productos":
                return self._json(crudPeriodos.productos())
            if url.path == "/periodos":
                return self._json(crudPeriodos.consultar(qs.get('idCliente')))
            if url.path == "/calcular":
                return self._json(crudPeriodos.calcular(
                    qs.get('idProducto'), qs.get('balance'), qs.get('desde')))
            if url.path == "/":
                self.path = "/index.html"
                return SimpleHTTPRequestHandler.do_GET(self)
            if url.path in PAGINAS:
                return SimpleHTTPRequestHandler.do_GET(self)
            self._json({'msg': 'Ruta no encontrada'}, 404)
        except Exception as e:
            self._json({'msg': f'Error: {e}'}, 500)


print(f"Servidor corriendo en el puerto {port}")
HTTPServer(("localhost", port), miServidor).serve_forever()