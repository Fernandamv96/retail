from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

from .models import Producto, Servicio


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Tu usuario', 'autofocus': True})
        self.fields['password'].label = 'Contraseña'
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '••••••••'})


class ContactoForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    asunto = forms.CharField(max_length=150, label='Asunto', widget=forms.TextInput(attrs={'class': 'form-control'}))
    mensaje = forms.CharField(label='Mensaje', widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))


class CatalogoForm(forms.ModelForm):
    """Validaciones compartidas por los formularios de servicios y productos."""

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        return nombre

    def clean_precio(self):
        precio = self.cleaned_data['precio']
        if precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio


class ServicioForm(CatalogoForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio', 'disponibilidad', 'activo']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'disponibilidad': 'Disponibilidad',
            'activo': 'Visible en el sitio',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Consultoría digital'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '¿Qué incluye este servicio?'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 45000', 'min': '0', 'step': '1'}),
            'disponibilidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lunes a viernes'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }


class ProductoForm(CatalogoForm):
    TAMANO_MAXIMO_FOTO = 2 * 1024 * 1024  # 2 MB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sin un almacenamiento persistente (por ejemplo en Vercel) el campo se oculta para no perder fotos.
        if not settings.FOTOS_PRODUCTOS:
            del self.fields['imagen']

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen and imagen.size > self.TAMANO_MAXIMO_FOTO:
            raise forms.ValidationError('La foto no puede pesar más de 2 MB.')
        return imagen

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'stock': 'Stock',
            'imagen': 'Foto del producto (opcional)',
            'activo': 'Visible en el sitio',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lector de códigos'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detalles del producto (opcional)'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 19990', 'min': '0', 'step': '1'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 25', 'min': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }
