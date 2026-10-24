from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets

from .forms import ContactoForm, ProductoForm, ServicioForm
from .models import Producto, Servicio
from .serializers import ServicioSerializer


def inicio(request):
	data = {
		'nombre_tienda': 'RETAIL',
		'total_servicios': Servicio.objects.filter(activo=True).count(),
		'total_productos': Producto.objects.filter(activo=True).count(),
	}

	return render(request, 'tiendaApp/inicio.html', {'data': data})


def menu_principal(request):
	return render(request, 'tiendaApp/menu_principal.html')


def informacion(request):
	return render(request, 'tiendaApp/informacion.html')


def servicios(request):
	servicios_activos = Servicio.objects.filter(activo=True)
	return render(request, 'serviciosApp/servicios.html', {'servicios': servicios_activos})


def detalle_servicio(request, servicio_id):
	servicio = get_object_or_404(Servicio, id=servicio_id, activo=True)
	return render(request, 'serviciosApp/detalle.html', {'servicio': servicio})


def contacto(request):
	form = ContactoForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		send_mail(
			f"Contacto RETAIL: {form.cleaned_data['asunto']}",
			form.cleaned_data['mensaje'],
			form.cleaned_data['email'],
			['admin@retail.local'],
		)
		messages.success(request, 'Tu mensaje se ha enviado correctamente.')
		return redirect('tiendaApp:contacto')
	return render(request, 'tiendaApp/contacto.html', {'form': form})


def precios(request):
	return render(request, 'tiendaApp/precios.html')


def productos(request):
	productos_activos = Producto.objects.filter(activo=True)
	return render(request, 'tiendaApp/productos.html', {'productos': productos_activos})


# ---------- GESTIÓN (CRUD) ----------------------------------------

@login_required
def panel(request):
	data = {
		'total_servicios': Servicio.objects.count(),
		'total_productos': Producto.objects.count(),
		'stock_total': Producto.objects.aggregate(total=Sum('stock'))['total'] or 0,
		'sin_stock': Producto.objects.filter(stock=0).count(),
		'ultimos_servicios': Servicio.objects.order_by('-id')[:4],
		'ultimos_productos': Producto.objects.order_by('-id')[:4],
	}
	return render(request, 'gestion/panel.html', data)


def _guardar(request, form_class, instancia, contexto, volver):
	"""Crea o modifica un registro con el ModelForm recibido."""
	form = form_class(request.POST or None, instance=instancia)
	if request.method == 'POST' and form.is_valid():  # si cumple con las validaciones
		registro = form.save()
		accion = 'actualizado' if instancia else 'creado'
		messages.success(request, f'«{registro}» se ha {accion} correctamente.')
		return redirect(volver)
	contexto.update({'form': form, 'volver': volver, 'editando': instancia is not None})
	return render(request, 'gestion/formulario.html', contexto)


def _eliminar(request, registro, tipo, volver):
	"""Muestra la confirmación y elimina solo cuando llega un POST."""
	if request.method == 'POST':
		nombre = str(registro)
		registro.delete()
		messages.success(request, f'«{nombre}» se ha eliminado.')
		return redirect(volver)
	return render(request, 'gestion/confirmar_eliminar.html', {'registro': registro, 'tipo': tipo, 'volver': volver})


def _buscar(queryset, request):
	termino = request.GET.get('q', '').strip()
	if termino:
		queryset = queryset.filter(nombre__icontains=termino)
	return queryset, termino


@login_required
def gestion_servicios(request):
	lista, termino = _buscar(Servicio.objects.all(), request)
	return render(request, 'gestion/servicios.html', {'servicios': lista, 'q': termino})


@login_required
def crear_servicio(request):
	contexto = {'titulo': 'Nuevo servicio', 'tipo': 'servicio'}
	return _guardar(request, ServicioForm, None, contexto, 'tiendaApp:gestion_servicios')


@login_required
def editar_servicio(request, servicio_id):
	servicio = get_object_or_404(Servicio, id=servicio_id)
	contexto = {'titulo': f'Editar {servicio.nombre}', 'tipo': 'servicio'}
	return _guardar(request, ServicioForm, servicio, contexto, 'tiendaApp:gestion_servicios')


@login_required
def eliminar_servicio(request, servicio_id):
	servicio = get_object_or_404(Servicio, id=servicio_id)
	return _eliminar(request, servicio, 'servicio', 'tiendaApp:gestion_servicios')


@login_required
def gestion_productos(request):
	lista, termino = _buscar(Producto.objects.all(), request)
	return render(request, 'gestion/productos.html', {'productos': lista, 'q': termino})


@login_required
def crear_producto(request):
	contexto = {'titulo': 'Nuevo producto', 'tipo': 'producto'}
	return _guardar(request, ProductoForm, None, contexto, 'tiendaApp:gestion_productos')


@login_required
def editar_producto(request, producto_id):
	producto = get_object_or_404(Producto, id=producto_id)
	contexto = {'titulo': f'Editar {producto.nombre}', 'tipo': 'producto'}
	return _guardar(request, ProductoForm, producto, contexto, 'tiendaApp:gestion_productos')


@login_required
def eliminar_producto(request, producto_id):
	producto = get_object_or_404(Producto, id=producto_id)
	return _eliminar(request, producto, 'producto', 'tiendaApp:gestion_productos')


class ServicioViewSet(viewsets.ModelViewSet):
	queryset = Servicio.objects.all()
	serializer_class = ServicioSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # visitantes solo pueden leer
