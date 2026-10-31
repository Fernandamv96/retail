import shutil
import tempfile
from io import BytesIO, StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import MensajeContacto, Orden, Producto, Servicio
from .views import _video_youtube


class RetailViewsTests(TestCase):
	def setUp(self):
		self.servicio = Servicio.objects.create(
			nombre='Consultoría',
			descripcion='Acompañamiento para tu negocio.',
			precio='125.00',
			disponibilidad='Lunes a viernes',
		)

	def test_detalle_servicio(self):
		response = self.client.get(f'/servicios/{self.servicio.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Consultoría')

	def test_api_lista_y_creacion_de_servicios(self):
		response = self.client.get('/api/servicios/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.json()), 1)

		self.client.force_login(User.objects.create_user('admin', password='clave-segura-123'))
		response = self.client.post('/api/servicios/', {
			'nombre': 'Soporte',
			'descripcion': 'Asistencia continua.',
			'precio': '80.00',
			'disponibilidad': '24/7',
			'activo': True,
		}, content_type='application/json')
		self.assertEqual(response.status_code, 201)
		self.assertEqual(Servicio.objects.count(), 2)

	def test_contacto_esta_disponible(self):
		response = self.client.get('/contacto/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Enviar mensaje')

	def test_contacto_guarda_el_mensaje(self):
		response = self.client.post('/contacto/', {
			'nombre': 'Ana',
			'email': 'ana@example.com',
			'asunto': 'Cotización',
			'mensaje': 'Quiero una consultoría.',
		})
		self.assertRedirects(response, '/contacto/')
		self.assertTrue(MensajeContacto.objects.filter(email='ana@example.com', asunto='Cotización').exists())

	def test_api_no_permite_crear_sin_sesion(self):
		response = self.client.post('/api/servicios/', {'nombre': 'X'}, content_type='application/json')
		self.assertEqual(response.status_code, 403)
		self.assertEqual(Servicio.objects.count(), 1)

	def test_productos_publicos_muestra_solo_activos(self):
		Producto.objects.create(nombre='Lector', precio='19990.00', stock=4)
		Producto.objects.create(nombre='Descontinuado', precio='100.00', activo=False)
		response = self.client.get(reverse('tiendaApp:productos'))
		self.assertContains(response, 'Lector')
		self.assertContains(response, 'Últimas 4 u.')
		self.assertNotContains(response, 'Descontinuado')

	def test_inicio_muestra_datos_solo_con_sesion(self):
		response = self.client.get(reverse('tiendaApp:inicio'))
		self.assertNotContains(response, 'Servicios activos')
		self.assertNotContains(response, 'Gestión</a>')
		self.assertContains(response, reverse('tiendaApp:login'))

		self.client.force_login(User.objects.create_user('admin', password='clave-segura-123'))
		response = self.client.get(reverse('tiendaApp:inicio'))
		self.assertContains(response, 'Servicios activos')
		self.assertContains(response, 'Salir (admin)')

	def test_contacto_muestra_mapa(self):
		response = self.client.get(reverse('tiendaApp:contacto'))
		self.assertContains(response, 'https://www.google.com/maps/embed?')
		self.assertContains(response, 'Av. España 2250, Valparaíso')
		self.assertContains(response, 'Cómo llegar')
		self.assertIn('frame-src https://www.google.com', response.headers['Content-Security-Policy'])

	def test_inicio_muestra_video_y_mapa(self):
		response = self.client.get(reverse('tiendaApp:inicio'))
		self.assertContains(response, 'https://www.youtube-nocookie.com/embed/W5ACjyQuEf0?start=6')
		self.assertContains(response, 'https://www.google.com/maps/embed?')

	def test_enlaces_de_youtube(self):
		self.assertEqual(_video_youtube('https://youtu.be/W5ACjyQuEf0?t=90'), 'https://www.youtube-nocookie.com/embed/W5ACjyQuEf0?start=90')
		self.assertEqual(_video_youtube('https://www.youtube.com/watch?v=W5ACjyQuEf0'), 'https://www.youtube-nocookie.com/embed/W5ACjyQuEf0?start=0')
		self.assertIsNone(_video_youtube('https://www.youtube.com/watch?v="><script>'))
		self.assertIsNone(_video_youtube(''))

	def test_gestion_requiere_login(self):
		url = reverse('tiendaApp:eliminar_servicio', args=[self.servicio.id])
		response = self.client.post(url)
		self.assertRedirects(response, f"{reverse('tiendaApp:login')}?next={url}")
		self.assertTrue(Servicio.objects.filter(id=self.servicio.id).exists())

	def test_login_y_logout(self):
		User.objects.create_user('admin', password='clave-segura-123')
		response = self.client.post(reverse('tiendaApp:login'), {'username': 'admin', 'password': 'mala'})
		self.assertContains(response, 'Usuario o contraseña incorrectos')

		response = self.client.post(reverse('tiendaApp:login'), {'username': 'admin', 'password': 'clave-segura-123'})
		self.assertRedirects(response, reverse('tiendaApp:panel'))

		response = self.client.post(reverse('tiendaApp:logout'))
		self.assertRedirects(response, reverse('tiendaApp:inicio'))


class PagoWebpayTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(nombre='Impresora térmica', precio='89990', stock=3)
		self.url_pagar = reverse('tiendaApp:pagar_producto', args=[self.producto.id])

	def _iniciar(self):
		with patch('tiendaApp.views.iniciar_pago', return_value=('https://webpay3gint.transbank.cl/webpayserver/initTransaction', 'tok-123')):
			return self.client.post(self.url_pagar)

	def test_iniciar_pago_lleva_a_webpay(self):
		response = self._iniciar()
		self.assertContains(response, 'action="https://webpay3gint.transbank.cl/webpayserver/initTransaction"')
		self.assertContains(response, 'value="tok-123"')
		orden = Orden.objects.get()
		self.assertEqual((orden.monto, orden.estado, orden.token), (89990, Orden.PENDIENTE, 'tok-123'))

	def test_pagar_requiere_post_y_stock(self):
		self.assertEqual(self.client.get(self.url_pagar).status_code, 405)
		self.producto.stock = 0
		self.producto.save()
		self.assertRedirects(self._iniciar(), reverse('tiendaApp:productos'))
		self.assertFalse(Orden.objects.exists())

	def test_pago_aprobado_descuenta_stock(self):
		self._iniciar()
		respuesta = {'status': 'AUTHORIZED', 'response_code': 0, 'amount': 89990, 'authorization_code': '1213', 'card_detail': {'card_number': '6623'}}
		with patch('tiendaApp.views.confirmar_pago', return_value=respuesta) as confirmar:
			response = self.client.post(reverse('tiendaApp:retorno_pago'), {'token_ws': 'tok-123'})
			self.client.get(reverse('tiendaApp:retorno_pago'), {'token_ws': 'tok-123'})  # recargar no confirma de nuevo
		self.assertContains(response, 'Pago aprobado')
		self.assertEqual(confirmar.call_count, 1)
		orden = Orden.objects.get()
		self.assertEqual((orden.estado, orden.codigo_autorizacion, orden.tarjeta), (Orden.PAGADA, '1213', '6623'))
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 2)

	def test_monto_distinto_se_rechaza(self):
		self._iniciar()
		respuesta = {'status': 'AUTHORIZED', 'response_code': 0, 'amount': 1}
		with patch('tiendaApp.views.confirmar_pago', return_value=respuesta):
			response = self.client.get(reverse('tiendaApp:retorno_pago'), {'token_ws': 'tok-123'})
		self.assertContains(response, 'Pago rechazado')
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 3)

	def test_pago_anulado_por_el_cliente(self):
		self._iniciar()
		response = self.client.post(reverse('tiendaApp:retorno_pago'), {'TBK_TOKEN': 'tok-123', 'TBK_ORDEN_COMPRA': 'RETAIL-1'})
		self.assertContains(response, 'Pago anulado')
		self.assertEqual(Orden.objects.get().estado, Orden.ANULADA)

	def test_retorno_con_token_desconocido(self):
		response = self.client.get(reverse('tiendaApp:retorno_pago'), {'token_ws': 'no-existe'})
		self.assertEqual(response.status_code, 404)


class FotosProductoTests(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user('admin', password='clave-segura-123'))
		self.media = tempfile.mkdtemp()
		self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)

	def _foto(self):
		contenido = BytesIO()
		Image.new('RGB', (8, 8), 'teal').save(contenido, 'PNG')
		return SimpleUploadedFile('foto.png', contenido.getvalue(), content_type='image/png')

	def test_subir_foto_y_mostrarla_en_el_catalogo(self):
		datos = {'nombre': 'Lector de códigos', 'precio': '19990', 'stock': '5', 'activo': 'on', 'imagen': self._foto()}
		with override_settings(MEDIA_ROOT=self.media):
			response = self.client.post(reverse('tiendaApp:crear_producto'), datos)
			self.assertRedirects(response, reverse('tiendaApp:gestion_productos'))
			producto = Producto.objects.get(nombre='Lector de códigos')
			self.assertContains(self.client.get(reverse('tiendaApp:productos')), producto.imagen.url)

	def test_sin_fotos_activadas_el_campo_no_aparece(self):
		with override_settings(FOTOS_PRODUCTOS=False):
			response = self.client.get(reverse('tiendaApp:crear_producto'))
		self.assertNotContains(response, 'name="imagen"')


class GestionCrudTests(TestCase):
	def setUp(self):
		self.client.force_login(User.objects.create_user('admin', password='clave-segura-123'))
		self.servicio = Servicio.objects.create(
			nombre='Consultoría',
			descripcion='Acompañamiento para tu negocio.',
			precio='125000.00',
		)
		self.producto = Producto.objects.create(nombre='Lector', precio='19990.00', stock=3)

	def test_paginas_de_gestion_responden(self):
		urls = [
			reverse('tiendaApp:panel'),
			reverse('tiendaApp:gestion_servicios'),
			reverse('tiendaApp:gestion_productos'),
			reverse('tiendaApp:crear_servicio'),
			reverse('tiendaApp:crear_producto'),
			reverse('tiendaApp:editar_servicio', args=[self.servicio.id]),
			reverse('tiendaApp:editar_producto', args=[self.producto.id]),
			reverse('tiendaApp:eliminar_servicio', args=[self.servicio.id]),
			reverse('tiendaApp:eliminar_producto', args=[self.producto.id]),
		]
		for url in urls:
			with self.subTest(url=url):
				self.assertEqual(self.client.get(url).status_code, 200)

	def test_crear_servicio(self):
		response = self.client.post(reverse('tiendaApp:crear_servicio'), {
			'nombre': 'Soporte',
			'descripcion': 'Asistencia continua.',
			'precio': '80000',
			'disponibilidad': '24/7',
			'activo': 'on',
		})
		self.assertRedirects(response, reverse('tiendaApp:gestion_servicios'))
		self.assertTrue(Servicio.objects.filter(nombre='Soporte', activo=True).exists())

	def test_crear_producto_con_precio_invalido_muestra_error(self):
		response = self.client.post(reverse('tiendaApp:crear_producto'), {
			'nombre': 'Caja',
			'precio': '0',
			'stock': '5',
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'El precio debe ser mayor a 0.')
		self.assertEqual(Producto.objects.count(), 1)

	def test_editar_producto(self):
		response = self.client.post(reverse('tiendaApp:editar_producto', args=[self.producto.id]), {
			'nombre': 'Lector QR',
			'descripcion': '',
			'precio': '24990',
			'stock': '10',
		})
		self.assertRedirects(response, reverse('tiendaApp:gestion_productos'))
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.nombre, 'Lector QR')
		self.assertEqual(self.producto.stock, 10)
		self.assertFalse(self.producto.activo)

	def test_eliminar_requiere_post(self):
		url = reverse('tiendaApp:eliminar_servicio', args=[self.servicio.id])

		response = self.client.get(url)
		self.assertContains(response, 'Confirmar eliminación')
		self.assertTrue(Servicio.objects.filter(id=self.servicio.id).exists())

		response = self.client.post(url)
		self.assertRedirects(response, reverse('tiendaApp:gestion_servicios'))
		self.assertFalse(Servicio.objects.filter(id=self.servicio.id).exists())

	def test_buscar_productos(self):
		Producto.objects.create(nombre='Impresora', precio='99990.00')
		response = self.client.get(reverse('tiendaApp:gestion_productos'), {'q': 'impre'})
		self.assertContains(response, 'Impresora')
		self.assertNotContains(response, 'Lector')


class CargarDemoTests(TestCase):
	def test_carga_datos_sin_duplicar(self):
		salida = StringIO()
		call_command('cargar_demo', stdout=salida)
		call_command('cargar_demo', stdout=salida)
		self.assertIn('0 registros nuevos', salida.getvalue())
		self.assertEqual(Servicio.objects.count(), 3)
		self.assertEqual(Producto.objects.count(), 3)


class SeguridadTests(TestCase):
	def setUp(self):
		cache.clear()
		User.objects.create_user('admin', password='clave-segura-123')

	def test_login_se_bloquea_tras_cinco_intentos_fallidos(self):
		url = reverse('tiendaApp:login')
		for _ in range(5):
			self.client.post(url, {'username': 'admin', 'password': 'mala'})

		response = self.client.post(url, {'username': 'admin', 'password': 'clave-segura-123'})
		self.assertEqual(response.status_code, 429)
		self.assertContains(response, 'Demasiados intentos fallidos', status_code=429)

	def test_login_correcto_reinicia_el_contador(self):
		url = reverse('tiendaApp:login')
		for _ in range(4):
			self.client.post(url, {'username': 'admin', 'password': 'mala'})
		response = self.client.post(url, {'username': 'admin', 'password': 'clave-segura-123'})
		self.assertRedirects(response, reverse('tiendaApp:panel'))

	def test_cabeceras_de_seguridad(self):
		response = self.client.get(reverse('tiendaApp:inicio'))
		self.assertIn("script-src 'self'", response['Content-Security-Policy'])
		self.assertEqual(response['X-Frame-Options'], 'DENY')
		self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
		self.assertNotIn('<script>', response.content.decode())
