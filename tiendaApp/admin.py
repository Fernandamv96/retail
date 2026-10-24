from django.contrib import admin
from .models import MensajeContacto, Producto, Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'precio', 'disponibilidad', 'activo')
	list_filter = ('activo',)
	search_fields = ('nombre', 'descripcion')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'precio', 'stock', 'activo')
	list_filter = ('activo',)
	search_fields = ('nombre', 'descripcion')


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
	list_display = ('asunto', 'nombre', 'email', 'recibido', 'leido')
	list_filter = ('leido',)
	search_fields = ('asunto', 'nombre', 'email', 'mensaje')
	readonly_fields = ('nombre', 'email', 'asunto', 'mensaje', 'recibido')
