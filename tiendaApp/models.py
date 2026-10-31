from django.db import models


class Servicio(models.Model):
	nombre = models.CharField(max_length=120)
	descripcion = models.TextField()
	precio = models.DecimalField(max_digits=10, decimal_places=2)
	disponibilidad = models.CharField(max_length=120, default='A convenir')
	activo = models.BooleanField(default=True)

	class Meta:
		ordering = ['nombre']

	def __str__(self):
		return self.nombre


class Producto(models.Model):
	nombre = models.CharField(max_length=120)
	descripcion = models.TextField(blank=True)
	precio = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)
	imagen = models.ImageField(upload_to='productos/', blank=True)
	activo = models.BooleanField(default=True)

	class Meta:
		ordering = ['nombre']

	def __str__(self):
		return self.nombre


class MensajeContacto(models.Model):
	nombre = models.CharField(max_length=100)
	email = models.EmailField()
	asunto = models.CharField(max_length=150)
	mensaje = models.TextField()
	recibido = models.DateTimeField(auto_now_add=True)
	leido = models.BooleanField(default=False)

	class Meta:
		ordering = ['-recibido']
		verbose_name = 'mensaje de contacto'
		verbose_name_plural = 'mensajes de contacto'

	def __str__(self):
		return f'{self.asunto} ({self.email})'


class Orden(models.Model):
	"""Compra de un producto pagada con Webpay Plus."""
	PENDIENTE = 'pendiente'
	PAGADA = 'pagada'
	RECHAZADA = 'rechazada'
	ANULADA = 'anulada'
	ESTADOS = [
		(PENDIENTE, 'Pendiente'),
		(PAGADA, 'Pagada'),
		(RECHAZADA, 'Rechazada'),
		(ANULADA, 'Anulada por el cliente'),
	]

	producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, related_name='ordenes')
	descripcion = models.CharField(max_length=120)  # nombre del producto al momento de la compra
	monto = models.PositiveIntegerField()
	estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
	token = models.CharField(max_length=64, unique=True, null=True, blank=True)
	codigo_autorizacion = models.CharField(max_length=20, blank=True)
	tarjeta = models.CharField(max_length=4, blank=True)  # últimos 4 dígitos
	creada = models.DateTimeField(auto_now_add=True)
	actualizada = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-creada']
		verbose_name = 'orden'
		verbose_name_plural = 'órdenes'

	def __str__(self):
		return f'Orden #{self.id} · {self.descripcion}'

	@property
	def orden_compra(self):
		return f'RETAIL-{self.id}'
