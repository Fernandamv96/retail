# RETAIL

Sitio web en Django para una tienda: muestra servicios, productos y precios, recibe consultas de contacto y tiene un panel con login para gestionar el catálogo (crear, modificar, eliminar y buscar).

## Requisitos

- Python 3.12 o superior
- Las dependencias de `requirements.txt` (Django 6.1 y Django REST Framework)

## Puesta en marcha (Windows)

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py createsuperuser   # usuario para entrar al panel
venv\Scripts\python.exe manage.py cargar_demo       # opcional: datos de ejemplo
venv\Scripts\python.exe manage.py runserver
```

Luego abre <http://127.0.0.1:8000/>.

## Rutas principales

| Ruta | Qué hay | ¿Requiere login? |
| --- | --- | --- |
| `/` | Inicio | No |
| `/servicios/` y `/servicios/<id>/` | Servicios activos y su detalle | No |
| `/productos/` | Catálogo de productos activos con stock | No |
| `/precios/`, `/informacion/`, `/contacto/` | Páginas informativas y formulario de contacto | No |
| `/gestion/` | Panel con resumen del catálogo | Sí |
| `/gestion/servicios/` y `/gestion/productos/` | Listado con buscador; desde aquí se crea, modifica y elimina | Sí |
| `/ingresar/` | Inicio de sesión (el botón "Salir" aparece en el menú) | — |
| `/api/servicios/` | API REST de servicios: lectura pública y escritura solo con sesión iniciada | Para escribir |
| `/admin/` | Administración de Django | Sí |

## Cómo está organizado

- `tiendaApp/models.py`: modelos `Servicio` y `Producto`.
- `tiendaApp/forms.py`: `ServicioForm` y `ProductoForm` (ModelForms con validaciones), además de los formularios de contacto y login.
- `tiendaApp/views.py`: vistas públicas y CRUD del panel. Eliminar pide confirmación y solo borra cuando recibe un POST.
- `templates/`: `base.html` y las páginas; el panel está en `templates/gestion/`.
- `static/css/estilo.css` y `static/js/efectos.js`: diseño oscuro con efectos inspirados en [React Bits](https://reactbits.dev) (Aurora, BlurText, ShinyText, SpotlightCard, CountUp, StarBorder, ClickSpark), escritos en CSS y JavaScript puro, sin React. Se desactivan si el sistema tiene activada la opción de reducir movimiento.

## Pruebas

```powershell
venv\Scripts\python.exe manage.py test tiendaApp
```

## Antes de publicar en producción

Por defecto el proyecto arranca en modo desarrollo. Para publicarlo, define estas variables de entorno:

| Variable | Valor en producción |
| --- | --- |
| `DJANGO_SECRET_KEY` | Una clave larga y aleatoria. La clave por defecto solo sirve en tu computador. |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | Los dominios separados por coma, por ejemplo `retail.cl,www.retail.cl` |

Además, los correos de contacto solo se muestran en la consola (`MAILERS` en `negocio/settings.py`) y la base de datos es SQLite. Para producción conviene configurar un servidor de correo real y una base de datos como PostgreSQL.
