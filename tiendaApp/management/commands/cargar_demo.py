from django.core.management.base import BaseCommand

from tiendaApp.models import Producto, Servicio

SERVICIOS = [
    {'nombre': 'Consultoría digital', 'descripcion': 'Diagnóstico de procesos y hoja de ruta para digitalizar tu tienda.', 'precio': 125000, 'disponibilidad': 'Lunes a viernes'},
    {'nombre': 'Desarrollo web', 'descripcion': 'Sitios y tiendas en línea a medida, conectados a tu inventario.', 'precio': 480000, 'disponibilidad': '4 a 6 semanas'},
    {'nombre': 'Soporte técnico', 'descripcion': 'Asistencia continua para mantener tus sistemas funcionando.', 'precio': 45000, 'disponibilidad': '24/7'},
]

PRODUCTOS = [
    {'nombre': 'Lector de códigos', 'descripcion': 'Lector USB para códigos 1D y 2D.', 'precio': 19990, 'stock': 25},
    {'nombre': 'Impresora térmica', 'descripcion': 'Impresora de boletas de 80 mm.', 'precio': 89990, 'stock': 3},
    {'nombre': 'Cajón de dinero', 'descripcion': 'Cajón metálico con 5 compartimentos.', 'precio': 39990, 'stock': 0},
]


class Command(BaseCommand):
    help = 'Carga servicios y productos de ejemplo (no duplica los que ya existen por nombre).'

    def handle(self, *args, **options):
        creados = 0
        for modelo, registros in ((Servicio, SERVICIOS), (Producto, PRODUCTOS)):
            for datos in registros:
                _, nuevo = modelo.objects.get_or_create(nombre=datos['nombre'], defaults=datos)
                creados += nuevo
        self.stdout.write(self.style.SUCCESS(f'Datos de ejemplo listos: {creados} registros nuevos.'))
