from django.contrib import admin
from .models import Producto, Servicio


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
