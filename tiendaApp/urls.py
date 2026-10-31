from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'tiendaApp'

router = DefaultRouter()
router.register('servicios', views.ServicioViewSet, basename='servicio-api')

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('menu-principal/', views.menu_principal, name='menu_principal'),
    path('informacion/', views.informacion, name='informacion'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/<int:servicio_id>/', views.detalle_servicio, name='detalle_servicio'),
    path('precios/', views.precios, name='precios'),
    path('productos/', views.productos, name='productos'),
    path('contacto/', views.contacto, name='contacto'),
    path('productos/<int:producto_id>/pagar/', views.pagar_producto, name='pagar_producto'),
    path('pago/retorno/', views.retorno_pago, name='retorno_pago'),
    path('ingresar/', views.IngresoView.as_view(), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('gestion/', views.panel, name='panel'),
    path('gestion/servicios/', views.gestion_servicios, name='gestion_servicios'),
    path('gestion/servicios/nuevo/', views.crear_servicio, name='crear_servicio'),
    path('gestion/servicios/<int:servicio_id>/editar/', views.editar_servicio, name='editar_servicio'),
    path('gestion/servicios/<int:servicio_id>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),
    path('gestion/productos/', views.gestion_productos, name='gestion_productos'),
    path('gestion/productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('gestion/productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('gestion/productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('api/', include(router.urls)),
]
