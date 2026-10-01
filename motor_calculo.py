"""Motor de cálculo puro: sin base de datos ni HTTP. Todo con Decimal."""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

VERSION_FORMULA = 2  # 1 = proporcional histórica (solo lectura), 2 = bloques con CEIL
MILES = Decimal('1000')


def _r(valor, decimales):
    return valor.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def calcular(balance, tarifa):
    balance = Decimal(str(balance))
    base = Decimal(str(tarifa['precio_base']))
    adicional = Decimal(str(tarifa['adicional']))
    porcentaje = Decimal(str(tarifa['porcentaje']))
    desde = Decimal(str(tarifa['desde_monto']))

    if porcentaje > 0:
        precio = balance * porcentaje / 100
        excedente = bloques = None
        texto = f"{balance} x {porcentaje} / 100"
    else:
        excedente = balance - desde
        bloques = (excedente / MILES).to_integral_value(rounding=ROUND_CEILING)
        precio = base + bloques * adicional
        texto = f"{base} + ({bloques} x {adicional})"

    return {
        'precio': _r(precio, 6),            # interno, hasta 6 decimales
        'precio_mostrado': _r(precio, 2),   # mostrado y cobrado
        'balance': balance,
        'rango': f"{tarifa['desde_monto']} a {tarifa['hasta_monto']}",
        'precio_base': base,
        'excedente': excedente,
        'bloques': bloques,
        'adicional': adicional,
        'porcentaje': porcentaje,
        'formula': texto,
        'formula_version': VERSION_FORMULA,
        'idTarifa': tarifa['idTarifa'],
    }