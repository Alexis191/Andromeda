from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Ruta raíz (Dashboard)
    path('', views.dashboard, name='dashboard'), 

    # --- RUTAS DE AUTENTICACIÓN ---
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # PERFIL PERSONAL
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    # GESTIÓN DE USUARIOS (SOLO SUPERADMIN)
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/nuevo/', views.guardar_usuario_admin, name='crear_usuario'),
    path('usuarios/editar/<int:id_usuario>/', views.guardar_usuario_admin, name='editar_usuario'),
    path('usuarios/eliminar/<int:id_usuario>/', views.eliminar_usuario, name='eliminar_usuario'),
]