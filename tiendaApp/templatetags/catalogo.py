import unicodedata

from django import template

register = template.Library()

# Palabras clave del nombre -> ícono. El primero que coincida gana; si ninguno coincide se usa el genérico.
ICONOS_SERVICIO = [
    (('consult', 'asesor', 'diagnost'), 'brujula'),
    (('desarrollo', 'web', 'software', 'app'), 'codigo'),
    (('soporte', 'tecnic', 'mantencion', 'ayuda'), 'audifonos'),
    (('marketing', 'publicidad', 'redes'), 'megafono'),
    (('diseno', 'grafic', 'marca'), 'pincel'),
]
ICONOS_PRODUCTO = [
    (('lector', 'codigo', 'escaner', 'scanner'), 'codigo_barras'),
    (('impresora', 'boleta', 'etiqueta'), 'impresora'),
    (('cajon', 'dinero', 'caja', 'pos'), 'caja_dinero'),
    (('computador', 'notebook', 'monitor', 'pantalla', 'tablet'), 'pantalla'),
]
TONOS = 4  # cantidad de colores definidos en estilo.css (.icono-tono-0 a 3)


def _normalizar(texto):
    sin_tildes = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return sin_tildes.lower()


@register.inclusion_tag('includes/icono.html')
def icono(registro, tipo='servicio', grande=False):
    """Ícono animado para un servicio o producto, elegido según su nombre."""
    reglas, generico = (ICONOS_PRODUCTO, 'caja') if tipo == 'producto' else (ICONOS_SERVICIO, 'destello')
    nombre = _normalizar(getattr(registro, 'nombre', '') or '')
    figura = next((icono for claves, icono in reglas if any(c in nombre for c in claves)), generico)
    return {'figura': figura, 'tono': (getattr(registro, 'id', 0) or 0) % TONOS, 'grande': grande}
