"""Cálculo puro del impuesto (sin BD ni HTTP). Todo con Decimal."""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

MILES = Decimal('1000')


def _r(valor, dec):
    return valor.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)


def calcular(balance, t):
    balance = Decimal(str(balance))
    base, adic = Decimal(str(t['precioBase'])), Decimal(str(t['adicional']))
    pct, desde = Decimal(str(t['porcentaje'])), Decimal(str(t['rangoDesde']))
    if t['formula'] == 'porcentaje':
        precio, bloques = balance * pct / 100, None
        detalle = f"{balance}*{pct}/100"
    else:
        # bloques de 1,000 sobre el excedente del rango, redondeados hacia arriba
        bloques = ((balance - desde) / MILES).to_integral_value(rounding=ROUND_CEILING)
        precio = base + bloques * adic
        detalle = f"{base:.6f}+({bloques}*{adic:.6f})"
    return {'balance': balance, 'rango': f"{t['rangoDesde']} a {t['rangoHasta']}",
            'precioBase': base, 'adicional': adic, 'porcentaje': pct, 'bloques': bloques,
            'formula': t['formula'], 'detalleCalculo': detalle,
            'precio': _r(precio, 6), 'precioMostrado': _r(precio, 2),
            'idTarifa': t['idTarifa']} 