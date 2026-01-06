from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import json
import pyodbc
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .forms import PerfilUsuarioForm, AdminUsuarioForm
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def dashboard(request):
    return render(request, 'gestion/dashboard.html')

# --- VISTA 1: MI PERFIL (Para todos) ---
@login_required
def perfil_usuario(request):
    usuario = request.user
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu información ha sido actualizada.')
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=usuario)

    return render(request, 'gestion/perfil.html', {'form': form})

# --- VISTA 2: LISTA DE USUARIOS (Solo Superadmin) ---
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard') # Candado de seguridad
def listar_usuarios(request):
    usuarios = User.objects.all().order_by('id')
    return render(request, 'gestion/lista_usuarios_admin.html', {'usuarios': usuarios})

# --- VISTA 3: CREAR/EDITAR USUARIO (Solo Superadmin) ---
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def guardar_usuario_admin(request, id_usuario=None):
    if id_usuario:
        # EDITAR
        usuario = get_object_or_404(User, pk=id_usuario)
        titulo = "Editar Usuario"
    else:
        # CREAR NUEVO
        usuario = None
        titulo = "Nuevo Usuario"

    if request.method == 'POST':
        form = AdminUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            # Truco: Si es nuevo, el username será el email
            user_obj = form.save(commit=False)
            user_obj.username = user_obj.email 
            
            # Si es nuevo y no puso clave, poner una por defecto o obligar (aquí asumimos que puso)
            if not id_usuario and not form.cleaned_data.get('nueva_clave'):
                 messages.error(request, "Para un usuario nuevo, la contraseña es obligatoria.")
                 return render(request, 'gestion/form_usuario_admin.html', {'form': form, 'titulo': titulo})

            form.save() # Aquí se guarda y se setea el password si vino en el form
            messages.success(request, f'Usuario {user_obj.email} guardado correctamente.')
            return redirect('listar_usuarios')
    else:
        form = AdminUsuarioForm(instance=usuario)

    return render(request, 'gestion/form_usuario_admin.html', {'form': form, 'titulo': titulo})

# --- VISTA 4: ELIMINAR USUARIO ---
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def eliminar_usuario(request, id_usuario):
    if request.user.id == id_usuario:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect('listar_usuarios')
        
    user = get_object_or_404(User, pk=id_usuario)
    user.delete()
    messages.warning(request, "Usuario eliminado permanentemente.")
    return redirect('listar_usuarios')