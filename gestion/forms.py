from django import forms
from django.contrib.auth.models import User

class EstiloFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # VERIFICACIÓN: Si el campo es un Checkbox, usa 'form-check-input'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            # Si es cualquier otro campo, usa 'form-control'
            else:
                field.widget.attrs.update({'class': 'form-control'})
# --- FORMULARIO 1: PERFIL PERSONAL (Para que el usuario se edite a sí mismo) ---
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
        # REGLA DE ORO: El usuario normal NO puede cambiar su email
        # Lo ponemos como 'readonly' visualmente y deshabilitado
        if 'email' in self.fields:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].disabled = True 
            self.fields['email'].help_text = "Contacta al administrador para cambiar tu correo."

# --- FORMULARIO 2: GESTIÓN TOTAL (Solo para Superadmin) ---
class AdminUsuarioForm(EstiloFormMixin, forms.ModelForm):
    # Campo extra para contraseña (solo si se quiere cambiar)
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
        # Si el superadmin escribió una nueva clave, la encriptamos y guardamos
        nueva_clave = self.cleaned_data.get('nueva_clave')
        if nueva_clave:
            user.set_password(nueva_clave)
        if commit:
            user.save()
        return user
