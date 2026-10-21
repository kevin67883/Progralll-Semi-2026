const $ = id => document.getElementById(id);
const campos = ['idUsuario', 'usuario', 'clave', 'nombre', 'direccion', 'telefono'];

async function enviar(datos) {
  const r = await fetch('/crud_usuarios_usss027225', {  // cambie por su código
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos)
  });
  const res = await r.json();
  if (res.login) { window.location.href = '/'; }
  return res;
}

function mostrar(ok, texto) {
  $('msg').className = ok ? 'exito' : 'error';
  $('msg').textContent = texto;
}

function limpiar() {
  campos.forEach(c => $(c).value = '');
  $('btnGuardar').textContent = 'Guardar';
}

async function guardar() {
  // Recoge los datos del formulario y los envía a Python
  const datos = {};
  campos.forEach(c => datos[c] = $(c).value);
  datos.accion = datos.idUsuario ? 'modificar' : 'guardar';

  const res = await enviar(datos);
  mostrar(res.ok, res.msg || '');
  if (res.ok) { limpiar(); buscar(); }
}

async function buscar() {
  const res = await enviar({ accion: 'buscar', texto: $('buscar').value });
  const tbody = $('tabla');
  tbody.innerHTML = '';
  if (!res.ok) return;

  res.datos.forEach(u => {
    const tr = document.createElement('tr');
    [u.idUsuario, u.usuario, u.nombre, u.direccion, u.telefono].forEach(v => {
      const td = document.createElement('td');
      td.textContent = v ?? '';
      tr.appendChild(td);
    });

    const acc = document.createElement('td');
    const bEditar = document.createElement('button');
    bEditar.textContent = 'Editar';
    bEditar.className = 'verde';
    bEditar.onclick = () => editar(u);
    const bEliminar = document.createElement('button');
    bEliminar.textContent = 'Eliminar';
    bEliminar.className = 'rojo';
    bEliminar.onclick = () => eliminar(u);
    acc.append(bEditar, bEliminar);
    tr.appendChild(acc);
    tbody.appendChild(tr);
  });
}

function editar(u) {
  $('idUsuario').value = u.idUsuario;
  $('usuario').value = u.usuario;
  $('clave').value = '';
  $('nombre').value = u.nombre;
  $('direccion').value = u.direccion;
  $('telefono').value = u.telefono;
  $('btnGuardar').textContent = 'Modificar';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function eliminar(u) {
  if (!confirm(`¿Eliminar al usuario "${u.usuario}"?`)) return;
  const res = await enviar({ accion: 'eliminar', idUsuario: u.idUsuario });
  mostrar(res.ok, res.msg || '');
  if (res.ok) buscar();
}

$('btnGuardar').addEventListener('click', guardar);
$('btnLimpiar').addEventListener('click', limpiar);
$('buscar').addEventListener('input', buscar);

fetch('/sesion').then(r => r.json()).then(s => { $('sesionUsuario').textContent = s.usuario || ''; });
limpiar();
buscar();