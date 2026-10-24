from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Producto, Servicio


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
