from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
from urllib.parse import urlparse, parse_qs
import crud_clientes
import crud_periodos
import json

port = 3000
crudClientes = crud_clientes.crud_clientes()
crudPeriodos = crud_periodos.crud_periodos()


class miServidor(SimpleHTTPRequestHandler):

    def _json(self, obj):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj, default=str).encode("utf-8"))

    def do_POST(self):
        longitud = int(self.headers.get('Content-Length', 0))
        datos = self.rfile.read(longitud).decode("utf-8")
        datos = parse.unquote(datos)
        datos = json.loads(datos)

        if self.path == "/cliente":
            respuesta = {'msg': crudClientes.administrar(datos)}
        elif self.path == "/periodo":
            respuesta = {'msg': crudPeriodos.administrar(datos)}
        elif self.path == "/periodo/calcular":
            respuesta = crudPeriodos.previsualizar(
                datos["idCliente"], datos["idProducto"],
                datos["balance"], datos["desde"])
        else:
            respuesta = {'msg': 'Ruta no encontrada'}

        self._json(respuesta)

    def do_GET(self):
        urlParse = urlparse(self.path)
        qs = parse_qs(urlParse.query)
        buscar = qs.get("buscar", [""])[0]

        if urlParse.path == "/clientes":
            self._json(crudClientes.consultar(buscar))
        elif urlParse.path == "/periodos":
            self._json(crudPeriodos.consultar(buscar))
        elif urlParse.path == "/":
            self.path = "/index.html"
            return SimpleHTTPRequestHandler.do_GET(self)
        else:
            return SimpleHTTPRequestHandler.do_GET(self)

print(f"Servidor corriendo en el puerto {port}")
server = HTTPServer(("localhost", port), miServidor)
server.serve_forever()