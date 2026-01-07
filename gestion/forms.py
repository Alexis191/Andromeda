from django import forms
from django.contrib.auth.models import User
from .models import DatosGeneralesCliente, DatosServicio, DatosTecnicosCliente

class EstiloFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

# FORMULARIO 1: PERFIL PERSONAL (Para que el usuario se edite a sí mismo)
class PerfilUsuarioForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo Electrónico'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El usuario normal NO puede cambiar su email, lo ponemos como 'readonly' visualmente y deshabilitado
        if 'email' in self.fields:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].disabled = True 
            self.fields['email'].help_text = "Contacta al administrador para cambiar tu correo."

# FORMULARIO 2: GESTIÓN TOTAL (Solo para Superadmin)
class AdminUsuarioForm(EstiloFormMixin, forms.ModelForm):
    nueva_clave = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar vacío para mantener la actual'}),
        label="Nueva Contraseña"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_superuser']
        labels = {
            'email': 'Correo (Usuario/Login)',
            'is_active': 'Usuario Activo (Puede entrar)',
            'is_superuser': 'Es Superadministrador'
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva_clave = self.cleaned_data.get('nueva_clave')
        if nueva_clave:
            user.set_password(nueva_clave)
        if commit:
            user.save()
        return user

# FORMULARIO 3: DATOS DEL SERVICIO DEL CLIENTE
class ServicioForm(EstiloFormMixin, forms.ModelForm):

    class Meta:
        model = DatosServicio
        fields = [
            'producto', 'mod_ventas', 'mod_compras', 'mod_tesoreria', 'mod_inventario', 'fecha_creacion',
            'fecha_renovacion', 'fecha_vencimiento', 'fecha_caducidad_firma', 
            'facturas_consumidas', 'precio_pactado', 'observaciones'
        ]
        
        widgets = {
            'fecha_creacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_renovacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'}),
            'fecha_caducidad_firma': forms.DateInput(attrs={'type': 'date'}),
            'facturas_consumidas': forms.NumberInput(attrs={'readonly': 'readonly', 'id': 'id_facturas_consumidas'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Detalles del servicio'}),
            'precio_pactado': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'})
        }

# FORMULARIO 4: DATOS GENERALES DEL CLIENTE
class ClienteForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = DatosGeneralesCliente
        exclude = ['servicio'] 
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2}),
            'envio_email': forms.CheckboxInput(), 
            'contacto_alt': forms.CheckboxInput(),
            'activo': forms.CheckboxInput(),
            'nombres_cliente': forms.TextInput(attrs={'class': 'text-uppercase'}),
            'direccion': forms.Textarea(attrs={'rows': 2, 'class': 'text-uppercase'}),
            'observacion_alt': forms.Textarea(attrs={'rows': 1, 'class': 'text-uppercase'}),
        }
    
    # VALIDACIÓN PARA EVITAR UN RUC DUPLICADO
    def clean_ruc_cliente(self):
        ruc = self.cleaned_data.get('ruc_cliente')
        # Buscamos si existe otro cliente con este RUC
        if DatosGeneralesCliente.objects.filter(ruc_cliente=ruc).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"⚠️ El RUC {ruc} ya está registrado en otro cliente.")
        return ruc

    # CONVERTIR TEXTOS A MAYÚSCULAS AL GUARDAR
    def clean(self):
        cleaned_data = super().clean()
        
        # Lista de campos que queremos forzar a mayúsculas
        campos_mayusculas = ['nombres_cliente', 'direccion', 'observaciones', 'observacion_alt']
        
        for campo in campos_mayusculas:
            valor = cleaned_data.get(campo)
            if valor:
                cleaned_data[campo] = valor.upper()
        
        # Forzar email a minúsculas
        email = cleaned_data.get('email')
        if email:
            cleaned_data['email'] = email.lower()
            
        return cleaned_data

# FORMULARIO 5: DATOS TÉCNICOS DEL CLIENTE
class TecnicoForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = DatosTecnicosCliente
        exclude = ['cliente'] 
        widgets = {
        }