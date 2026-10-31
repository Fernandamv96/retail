from urllib.parse import parse_qs, quote_plus, urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from .forms import ContactoForm, LoginForm, ProductoForm, ServicioForm
from .models import MensajeContacto, Orden, Producto, Servicio
from .pagos import confirmar_pago, iniciar_pago
from .serializers import ServicioSerializer


def _mapa():
	"""Datos del mapa de Google para la ubicación configurada en settings."""
	busqueda = quote_plus(f'{settings.UBICACION_DIRECCION}, Chile')
	return {
		'nombre': settings.UBICACION_NOMBRE,
		'direccion': settings.UBICACION_DIRECCION,
		# URL final de inserción: la corta (maps?q=...&output=embed) redirige con X-Frame-Options.
		'embed': f'https://www.google.com/maps/embed?origin=mfe&pb=!1m2!2m1!1s{busqueda}',
		'como_llegar': f'https://www.google.com/maps/dir/?api=1&destination={busqueda}',
	}


def _video_youtube(url):
	"""Convierte un enlace de YouTube (watch?v=... o youtu.be/...) en su URL para insertar."""
	if not url:
		return None
	enlace = urlparse(url)
	parametros = parse_qs(enlace.query)
	if enlace.netloc.endswith('youtu.be'):
		video = enlace.path.strip('/')
	else:
		video = parametros.get('v', [''])[0]
	if not video.replace('-', '').replace('_', '').isalnum():
		return None
	inicio = parametros.get('t', ['0'])[0].rstrip('s')
	segundos = int(inicio) if inicio.isdigit() else 0
	return f'https://www.youtube-nocookie.com/embed/{video}?start={segundos}'


def inicio(request):
	data = {'nombre_tienda': 'RETAIL'}
	# Los totales solo se calculan y muestran a usuarios que ya ingresaron.
	if request.user.is_authenticated:
		data['total_servicios'] = Servicio.objects.filter(activo=True).count()
		data['total_productos'] = Producto.objects.filter(activo=True).count()

	contexto = {'data': data, 'mapa': _mapa(), 'video': _video_youtube(settings.VIDEO_YOUTUBE)}
	return render(request, 'tiendaApp/inicio.html', contexto)


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
		# Se guarda siempre (se revisa en /admin/) y se envía por correo solo si hay SMTP configurado.
		MensajeContacto.objects.create(**form.cleaned_data)
		if settings.CORREO_CONTACTO:
			send_mail(
				f"Contacto RETAIL: {form.cleaned_data['asunto']}",
				f"De: {form.cleaned_data['nombre']} <{form.cleaned_data['email']}>\n\n{form.cleaned_data['mensaje']}",
				None,
				[settings.CORREO_CONTACTO],
				fail_silently=True,
			)
		messages.success(request, 'Tu mensaje se ha enviado correctamente.')
		return redirect('tiendaApp:contacto')
	return render(request, 'tiendaApp/contacto.html', {'form': form, 'mapa': _mapa()})


def precios(request):
	return render(request, 'serviciosApp/precios.html')


def productos(request):
	productos_activos = Producto.objects.filter(activo=True)
	return render(request, 'tiendaApp/productos.html', {'productos': productos_activos})


# ---------- PAGOS (Webpay Plus) -----------------------------------

@require_POST
def pagar_producto(request, producto_id):
	producto = get_object_or_404(Producto, id=producto_id, activo=True)
	if producto.stock < 1:
		messages.error(request, f'«{producto.nombre}» está agotado.')
		return redirect('tiendaApp:productos')

	orden = Orden.objects.create(producto=producto, descripcion=producto.nombre, monto=int(producto.precio))
	try:
		url, token = iniciar_pago(orden, request.build_absolute_uri(reverse('tiendaApp:retorno_pago')))
	except Exception:
		orden.estado = Orden.RECHAZADA
		orden.save(update_fields=['estado', 'actualizada'])
		messages.error(request, 'No pudimos conectar con Webpay. Inténtalo de nuevo en unos minutos.')
		return redirect('tiendaApp:productos')

	orden.token = token
	orden.save(update_fields=['token', 'actualizada'])
	return render(request, 'pagos/redirigir.html', {'url': url, 'token': token, 'orden': orden})


@csrf_exempt  # Webpay vuelve desde su dominio, sin token CSRF; la validez la confirma Transbank.
def retorno_pago(request):
	datos = request.POST if request.method == 'POST' else request.GET
	token = datos.get('token_ws')
	token_anulado = datos.get('TBK_TOKEN')

	if token and not token_anulado:
		orden = get_object_or_404(Orden, token=token)
		if orden.estado == Orden.PENDIENTE:  # al recargar la página no se confirma dos veces
			_confirmar(orden, token)
	elif token_anulado:
		orden = get_object_or_404(Orden, token=token_anulado)
		if orden.estado == Orden.PENDIENTE:
			orden.estado = Orden.ANULADA
			orden.save(update_fields=['estado', 'actualizada'])
	else:
		# Se agotó el tiempo en el formulario de Webpay: solo llega la orden de compra.
		numero = datos.get('TBK_ORDEN_COMPRA', '').removeprefix('RETAIL-')
		orden = get_object_or_404(Orden, id=int(numero) if numero.isdigit() else 0, estado=Orden.PENDIENTE)
		orden.estado = Orden.ANULADA
		orden.save(update_fields=['estado', 'actualizada'])

	return render(request, 'pagos/resultado.html', {'orden': orden})


def _confirmar(orden, token):
	try:
		respuesta = confirmar_pago(token)
	except Exception:
		respuesta = {}
	aprobada = (
		respuesta.get('status') == 'AUTHORIZED'
		and respuesta.get('response_code') == 0
		and respuesta.get('amount') == orden.monto
	)
	if aprobada:
		orden.estado = Orden.PAGADA
		orden.codigo_autorizacion = respuesta.get('authorization_code', '')
		orden.tarjeta = (respuesta.get('card_detail') or {}).get('card_number', '')[-4:]
		Producto.objects.filter(id=orden.producto_id, stock__gt=0).update(stock=F('stock') - 1)
	else:
		orden.estado = Orden.RECHAZADA
	orden.save()


# ---------- INGRESO ------------------------------------------------

MAX_INTENTOS = 5           # intentos fallidos permitidos por IP y usuario
BLOQUEO_SEGUNDOS = 15 * 60  # tiempo de espera al superar el límite


def _ip_cliente(request):
	# En Vercel la IP real llega en X-Forwarded-For (Vercel la sobrescribe, no se puede falsificar).
	if settings.EN_VERCEL and request.META.get('HTTP_X_FORWARDED_FOR'):
		return request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
	return request.META.get('REMOTE_ADDR', '')


class IngresoView(auth_views.LoginView):
	"""Login de Django con límite de intentos fallidos para frenar ataques de fuerza bruta."""
	template_name = 'serviciosApp/login.html'
	authentication_form = LoginForm
	redirect_authenticated_user = True

	def post(self, request, *args, **kwargs):
		usuario = request.POST.get('username', '').strip().lower()
		clave = f'login-fallido:{_ip_cliente(request)}:{usuario}'
		if cache.get(clave, 0) >= MAX_INTENTOS:
			contexto = self.get_context_data(form=self.get_form(), bloqueado=True)
			return self.render_to_response(contexto, status=429)

		respuesta = super().post(request, *args, **kwargs)
		if respuesta.status_code == 302:
			cache.delete(clave)
		else:
			cache.set(clave, cache.get(clave, 0) + 1, BLOQUEO_SEGUNDOS)
		return respuesta


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


def _guardar(request, form_class, instancia, contexto, volver, plantilla='gestion/formulario.html'):
	"""Crea o modifica un registro con el ModelForm recibido."""
	form = form_class(request.POST or None, request.FILES or None, instance=instancia)
	if request.method == 'POST' and form.is_valid():  # si cumple con las validaciones
		registro = form.save()
		accion = 'actualizado' if instancia else 'creado'
		messages.success(request, f'«{registro}» se ha {accion} correctamente.')
		return redirect(volver)
	contexto.update({'form': form, 'volver': volver, 'editando': instancia is not None})
	return render(request, plantilla, contexto)


def _eliminar(request, registro, tipo, volver, plantilla='gestion/confirmar_eliminar.html'):
	"""Muestra la confirmación y elimina solo cuando llega un POST."""
	if request.method == 'POST':
		nombre = str(registro)
		registro.delete()
		messages.success(request, f'«{nombre}» se ha eliminado.')
		return redirect(volver)
	return render(request, plantilla, {'registro': registro, tipo: registro, 'tipo': tipo, 'volver': volver})


def _buscar(queryset, request):
	termino = request.GET.get('q', '').strip()
	if termino:
		queryset = queryset.filter(nombre__icontains=termino)
	return queryset, termino


@login_required
def gestion_servicios(request):
	lista, termino = _buscar(Servicio.objects.all(), request)
	return render(request, 'serviciosApp/listar.html', {'servicios': lista, 'q': termino})


@login_required
def crear_servicio(request):
	contexto = {'titulo': 'Nuevo servicio', 'tipo': 'servicio'}
	return _guardar(request, ServicioForm, None, contexto, 'tiendaApp:gestion_servicios', 'serviciosApp/crear.html')


@login_required
def editar_servicio(request, servicio_id):
	servicio = get_object_or_404(Servicio, id=servicio_id)
	contexto = {'titulo': f'Editar {servicio.nombre}', 'tipo': 'servicio', 'servicio': servicio}
	return _guardar(request, ServicioForm, servicio, contexto, 'tiendaApp:gestion_servicios', 'serviciosApp/editar.html')


@login_required
def eliminar_servicio(request, servicio_id):
	servicio = get_object_or_404(Servicio, id=servicio_id)
	return _eliminar(request, servicio, 'servicio', 'tiendaApp:gestion_servicios', 'serviciosApp/eliminar.html')


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
