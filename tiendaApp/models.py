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
