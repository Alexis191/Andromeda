from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # RUTA PRINCIPAL (DASHBOARD)
    path('', views.dashboard, name='dashboard'), 

    # RUTAS DE AUTENTICACIÓN
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # RUTA DE PERFIL DE USUARIO
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),

    # RUTAS DE GESTIÓN DE USUARIOS (SOLO SUPERADMIN)
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/nuevo/', views.guardar_usuario_admin, name='crear_usuario'),
    path('usuarios/editar/<int:id_usuario>/', views.guardar_usuario_admin, name='editar_usuario'),
    path('usuarios/eliminar/<int:id_usuario>/', views.eliminar_usuario, name='eliminar_usuario'),

    # RUTAS DE CLIENTES
    path('clientes/', views.listar_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente_completo, name='crear_cliente'),
    path('clientes/editar/<int:id_cliente>/', views.editar_cliente, name='editar_cliente'),

    # RUTAS DE PRODUCTOS
    path('productos/', views.listar_productos, name='lista_productos'),
    path('productos/guardar/', views.guardar_producto, name='guardar_producto'),
    path('productos/editar/', views.editar_producto, name='editar_producto'), 
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),

    # RUTAS DE PROVEEDORES
    path('proveedores/', views.listar_proveedores, name='lista_proveedores'),
    path('proveedores/guardar/', views.guardar_proveedor, name='guardar_proveedor'),
    path('proveedores/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'), 

    # RUTA DE CONSUMO DE API PARA CONSULTA EXTERNA
    path('api/consultar-consumo/', views.consultar_facturas_externas, name='api_consultar_consumo'),

    # RUTA PARA IMPORTAR DATOS
    path('carga-masiva/', views.carga_masiva_clientes, name='carga_masiva'),

    # RUTA PARA CONSULTAR CONSUMO DE CLIENTES
    path('api/get-clientes-ids/', views.api_obtener_ids_clientes, name='api_get_ids'),
    path('api/sync-cliente/<int:id_cliente>/', views.api_sincronizar_cliente, name='api_sync_cliente'),

    # RUTA PARA EL CALENDARIO EN DASHBOARD
    path('api/eventos-calendario/', views.api_eventos_calendario, name='api_eventos_calendario'),
]