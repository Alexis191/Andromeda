# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import conectar_y_contar_facturas, verificar_alertas_plan
from django.db.models import F

# Django contrib
from django.contrib import messages
from django.contrib.auth.models import User

# Models y forms locales
from .models import *
from .forms import *
from .services import conectar_y_contar_facturas

# Utils y otras bibliotecas
import json
import pyodbc
import openpyxl
from django.db import IntegrityError
from datetime import datetime


# ==========================================
# GESTIÓN DE USUARIOS
# ==========================================

# VISTA USUARIOS 1: DASHOBOARD
@login_required
def dashboard(request):
    return render(request, 'gestion/dashboard.html')

# VISTA USUARIOS 2: PERFIL DE USUARIO (Superadmin y Usuario)
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

# VISTA USUARIOS 3: LISTA DE USUARIOS (Solo Superadmin)
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def listar_usuarios(request):
    usuarios = User.objects.all().order_by('id')
    return render(request, 'gestion/lista_usuarios_admin.html', {'usuarios': usuarios})

# VISTA USUARIOS 4: CREAR/EDITAR USUARIO (Solo Superadmin)
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def guardar_usuario_admin(request, id_usuario=None):
    if id_usuario:
        usuario = get_object_or_404(User, pk=id_usuario)
        titulo = "Editar Usuario"
    else:
        usuario = None
        titulo = "Nuevo Usuario"

    if request.method == 'POST':
        form = AdminUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            user_obj = form.save(commit=False)
            user_obj.username = user_obj.email 
            if not id_usuario and not form.cleaned_data.get('nueva_clave'):
                 messages.error(request, "Para un usuario nuevo, la contraseña es obligatoria.")
                 return render(request, 'gestion/form_usuario_admin.html', {'form': form, 'titulo': titulo})
            form.save()
            messages.success(request, f'Usuario {user_obj.email} guardado correctamente.')
            return redirect('listar_usuarios')
    else:
        form = AdminUsuarioForm(instance=usuario)
    return render(request, 'gestion/form_usuario_admin.html', {'form': form, 'titulo': titulo})

# VISTA USUARIOS 5: ELIMINAR USUARIO (Solo Superadmin)
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

# ==========================================
# GESTIÓN DE CLIENTES
# ==========================================

# VISTA CLIENTES 1: LISTA DE CLIENTES
@login_required
def listar_clientes(request):
    lista_completa = DatosGeneralesCliente.objects.select_related(
        'servicio', 
        'servicio__producto', 
        'estado',
        'proveedor'
    ).all().order_by('-id') # Ordenar: Los más recientes primero
    
    # CONFIGURACIÓN PARA LOS FILTROS
    # Obtener valores del GET (URL) para los filtros
    filtro_nombre = request.GET.get('q', '')
    filtro_proveedor = request.GET.get('proveedor', '')
    filtro_estado = request.GET.get('estado', '')
    filtro_fecha_ini = request.GET.get('fecha_ini', '')
    filtro_fecha_fin = request.GET.get('fecha_fin', '')

    # 1. Filtro por Nombre o RUC
    if filtro_nombre:
        lista_completa = lista_completa.filter(
            Q(nombres_cliente__icontains=filtro_nombre) | 
            Q(ruc_cliente__icontains=filtro_nombre)
        )

    # 2. Filtro por Proveedor
    if filtro_proveedor:
        lista_completa = lista_completa.filter(proveedor_id=filtro_proveedor)

    # 3. Filtro por Estado
    if filtro_estado:
        lista_completa = lista_completa.filter(estado_id=filtro_estado)

    # 4. Filtro por Rango de Fechas (Vencimiento)
    if filtro_fecha_ini and filtro_fecha_fin:
        lista_completa = lista_completa.filter(
            servicio__fecha_vencimiento__range=[filtro_fecha_ini, filtro_fecha_fin]
        )

    # CONFIGURACIÓN PARA LOS NÚMERO DE PÁGINA EN LA LISTA CLIENTES
    # 1. Configurar el Paginador: 8 clientes por página
    paginator = Paginator(lista_completa, 8) 
    
    # 3. Obtener el número de página de la URL (ej: ?page=2)
    page_number = request.GET.get('page')
    
    # 4. Obtener solo los registros de esa página
    page_obj = paginator.get_page(page_number)
    
    proveedores = DatosProveedor.objects.all()
    estados = EstadoCliente.objects.all()

    #CONFIGURACIÓN PARA MANTENER LOS FILTROS AL PAGINAR
    # Creamos un string con los filtros actuales para pegarlo en los botones "Siguiente"
    url_params = request.GET.copy()
    if 'page' in url_params:
        del url_params['page'] # Quitamos la página actual para no duplicar
    str_params = url_params.urlencode()

    context = {
        'clientes': page_obj,
        'proveedores': proveedores,
        'estados': estados,
        'params': str_params,
    }
    
    return render(request, 'gestion/lista_clientes.html', context)

# VISTA CLIENTES 2: CREAR CLIENTES
@login_required
def crear_cliente_completo(request):
    if request.method == 'POST':
        form_general = ClienteForm(request.POST)
        form_servicio = ServicioForm(request.POST)
        form_tecnico = TecnicoForm(request.POST)

        if form_general.is_valid() and form_servicio.is_valid() and form_tecnico.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar Servicio
                    servicio = form_servicio.save()

                    # 2. Guardar Cliente
                    cliente = form_general.save(commit=False)
                    cliente.servicio = servicio
                    cliente.save()

                    # 3. Guardar Técnico
                    tecnico = form_tecnico.save(commit=False)
                    tecnico.cliente = cliente
                    tecnico.save()

                messages.success(request, 'Cliente creado exitosamente.')
                return redirect('lista_clientes')
            except Exception as e:
                messages.error(request, f"Error interno al guardar: {e}")
        else:
            # Recorremos los 3 formularios buscando errores
            for form in [form_general, form_servicio, form_tecnico]:
                for field_name in form.errors:
                    # Si el error pertenece a un campo específico (y no es error general)
                    if field_name in form.fields:
                        # Recuperamos las clases CSS que ya tiene (ej: 'form-control uppercase-input')
                        clases_actuales = form.fields[field_name].widget.attrs.get('class', '')
                        # Le pegamos la clase 'is-invalid' de Bootstrap
                        form.fields[field_name].widget.attrs['class'] = clases_actuales + ' is-invalid'
                        
            messages.error(request, "Hay errores en el formulario. Revisa los campos en rojo.")
            
            # Esto imprimirá el error exacto en el terminal
            print("--- ERRORES DE VALIDACIÓN ---")
            print("General:", form_general.errors)
            print("Servicio:", form_servicio.errors)
            print("Técnico:", form_tecnico.errors)
            print("-----------------------------")
    
    else:
        form_general = ClienteForm()
        form_servicio = ServicioForm()
        form_tecnico = TecnicoForm()

    context = {
        'form_general': form_general,
        'form_servicio': form_servicio,
        'form_tecnico': form_tecnico
    }
    return render(request, 'gestion/cliente_form.html', context)

# VISTA CLIENTES 3: EDITAR CLIENTES
@login_required
def editar_cliente(request, id_cliente):
    # 1. Buscar el cliente general
    cliente = get_object_or_404(DatosGeneralesCliente, pk=id_cliente)
    
    # 2. Buscar sus partes relacionadas (Servicio y Técnico)
    servicio = cliente.servicio
    
    try:
        tecnico = cliente.datos_tecnicos
    except DatosTecnicosCliente.DoesNotExist:
        tecnico = None

    if request.method == 'POST':
        # Cargamos los formularios con los datos POST y las instancias existentes
        form_general = ClienteForm(request.POST, instance=cliente)
        form_servicio = ServicioForm(request.POST, instance=servicio)
        form_tecnico = TecnicoForm(request.POST, instance=tecnico)

        if form_general.is_valid() and form_servicio.is_valid() and form_tecnico.is_valid():
            try:
                with transaction.atomic():
                    form_servicio.save()
                    form_general.save()
                    tech = form_tecnico.save(commit=False)
                    tech.cliente = cliente
                    tech.save()

                messages.success(request, 'Datos del cliente actualizados correctamente.')
                return redirect('lista_clientes')
            except Exception as e:
                messages.error(request, f"Error al actualizar: {e}")
        else:
             messages.error(request, "Error en los datos. Revisa los campos en rojo.")
    
    else:
        form_general = ClienteForm(instance=cliente)
        form_servicio = ServicioForm(instance=servicio)
        form_tecnico = TecnicoForm(instance=tecnico)

    context = {
        'form_general': form_general,
        'form_servicio': form_servicio,
        'form_tecnico': form_tecnico,
        'es_edicion': True
    }
    return render(request, 'gestion/cliente_form.html', context)

# ==========================================
# GESTIÓN DE PRODUCTOS
# ==========================================

# VISTA PRODUCTOS 1: LISTAR PRODUCTOS
@login_required
def listar_productos(request):
    productos = DatosProducto.objects.all().order_by('id') # Ordenar por id
    return render(request, 'gestion/lista_productos.html', {'productos': productos})

# VISTA PRODUCTOS 2: CREAR PRODUCTOS
@login_required
def guardar_producto(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre_producto')
            plan_num = request.POST.get('plan_num')
            precio = request.POST.get('precio')
            vigencia = request.POST.get('vigencia')
            
            DatosProducto.objects.create(
                nombre_producto=nombre,
                plan_num=plan_num,
                precio=precio,
                vigencia=vigencia
            )
            messages.success(request, 'Producto creado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al crear: {e}')
            
    return redirect('lista_productos')

# VISTA PRODUCTOS 3: EDITAR PRODUCTOS
@login_required
def editar_producto(request):
    if request.method == 'POST':
        try:
            id_prod = request.POST.get('id_producto')
            producto = get_object_or_404(DatosProducto, pk=id_prod)
            
            producto.nombre_producto = request.POST.get('nombre_producto')
            producto.plan_num = request.POST.get('plan_num')
            producto.precio = request.POST.get('precio')
            producto.vigencia = request.POST.get('vigencia')
            producto.save()
            
            messages.success(request, 'Producto actualizado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al editar: {e}')
            
    return redirect('lista_productos')

# VISTA PRODUCTOS 4: ELIMINAR PRODUCTOS
@login_required
def eliminar_producto(request, id):
    try:
        producto = get_object_or_404(DatosProducto, pk=id)
        producto.delete()
        messages.warning(request, 'Producto eliminado.')
    except Exception as e:
        messages.error(request, 'Error al eliminar.')
    return redirect('lista_productos')

# ==========================================
# GESTIÓN DE PROVEEDORES
# ==========================================

# VISTA PROVEEDORES 1: LISTAR PROVEEDORES
@login_required
def listar_proveedores(request):
    proveedores = DatosProveedor.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_proveedores.html', {'proveedores': proveedores})

# VISTA PROVEEDORES 2: CREAR PROVEEDORES
@login_required
def guardar_proveedor(request):
    if request.method == 'POST':
        try:
            DatosProveedor.objects.create(
                nombre=request.POST.get('nombre'),
                ruc=request.POST.get('ruc'),
                direccion=request.POST.get('direccion'),
                telefono=request.POST.get('telefono')
            )
            messages.success(request, 'Proveedor registrado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
    return redirect('lista_proveedores')

# VISTA PROVEEDORES 3: EDITAR PROVEEDORES
@login_required
def editar_proveedor(request):
    if request.method == 'POST':
        try:
            id_prov = request.POST.get('id_proveedor')
            prov = get_object_or_404(DatosProveedor, pk=id_prov)
            
            prov.nombre = request.POST.get('nombre')
            prov.ruc = request.POST.get('ruc')
            prov.direccion = request.POST.get('direccion')
            prov.telefono = request.POST.get('telefono')
            prov.save()
            
            messages.success(request, 'Proveedor actualizado.')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')
    return redirect('lista_proveedores')

# VISTA PROVEEDORES 4: ELIMINAR PROVEEDORES
@login_required
def eliminar_proveedor(request, id):
    try:
        prov = get_object_or_404(DatosProveedor, pk=id)
        prov.delete()
        messages.warning(request, 'Proveedor eliminado.')
    except Exception as e:
        messages.error(request, 'Error al eliminar.')
    return redirect('lista_proveedores')

# ==========================================
# API INTERNA PARA CONSULTAR BASES EXTERNAS
# ==========================================

@csrf_exempt
def consultar_facturas_externas(request):
    """
    Vista manual para botón de consulta rápida.
    Recibe JSON con servidor, BD y fechas arbitrarias.
    """
    if request.method == 'POST':
        try:
            # 1. Decodificar JSON
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'mensaje': 'JSON inválido.'})
            
            # 2. Obtener datos
            servidor_id = data.get('servidor')
            db_name = data.get('db_name')
            fecha_inicio_str = data.get('fecha_inicio') # Viene como YYYY-MM-DD del input date
            fecha_fin_str = data.get('fecha_fin')

            if not all([servidor_id, db_name, fecha_inicio_str]):
                return JsonResponse({'status': 'error', 'mensaje': 'Faltan datos requeridos.'})

            # 3. Formatear Fechas para SQL Server (DD/MM/YYYY)
            try:
                f_obj_ini = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                f_obj_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
                
                fecha_sql_ini = f_obj_ini.strftime('%d/%m/%Y')
                fecha_sql_fin = f_obj_fin.strftime('%d/%m/%Y')
            except ValueError:
                return JsonResponse({'status': 'error', 'mensaje': 'Formato de fecha inválido.'})

            # 4. Obtener credenciales del servidor
            try:
                servidor_obj = ServidorBaseDatos.objects.get(pk=servidor_id)
            except ServidorBaseDatos.DoesNotExist:
                return JsonResponse({'status': 'error', 'mensaje': 'Servidor no encontrado.'})

            # 5. Usar el Servicio Centralizado (Reutilización de código)
            cantidad = conectar_y_contar_facturas(
                ip=servidor_obj.ip_host,
                puerto=servidor_obj.puerto,
                db=db_name,
                user=servidor_obj.usuario_sql,
                password=servidor_obj.clave_sql,
                fecha_ini_str=fecha_sql_ini,
                fecha_fin_str=fecha_sql_fin
            )

            if cantidad is not None:
                return JsonResponse({'status': 'ok', 'cantidad': cantidad})
            else:
                return JsonResponse({'status': 'error', 'mensaje': 'Error al conectar con la base de datos externa.'})

        except Exception as e:
            print(f"ERROR CRÍTICO EN VISTA: {e}")
            return JsonResponse({'status': 'error', 'mensaje': f'Error interno: {str(e)}'})
            
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})

# ==========================================
# IMPORTAR DATOS DESDE EXCEL
# ==========================================

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def carga_masiva_clientes(request):
    if request.method == 'POST':
        form = CargaMasivaForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo)
            hoja = wb.active
            
            exitos = 0
            omitidos = 0  # Contador para los clientes saltados
            errores = []

            for i, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
                if not any(fila): continue 

                (
                    nom, ruc, tel, mail, id_prov, id_est, id_reg, act, env_m, obs_gen,
                    c_alt, t_alt, m_alt, o_alt,
                    id_prod, p_pact, f_cre, f_ren, f_ven, f_firm, m_v, m_c, m_t, m_i, obs_serv,
                    id_srv, bdd, u_port, c_port, n_port, vers, firma, n_serv, mail_t, c_mail_t, cod_mail
                ) = fila

                # 1. LIMPIEZA DE DATOS (Crucial para evitar errores por espacios invisibles)
                ruc_limpio = str(ruc).strip()
                nombre_limpio = str(nom).strip().upper()
                
                # 2. VERIFICACIÓN PREVIA: Si el RUC ya existe, saltamos al siguiente
                if DatosGeneralesCliente.objects.filter(ruc_cliente=ruc_limpio).exists():
                    omitidos += 1
                    continue # Omite este ciclo y pasa a la siguiente fila del Excel

                try:
                    with transaction.atomic():
                        # Crear DatosServicio
                        servicio = DatosServicio.objects.create(
                            producto_id=id_prod,
                            fecha_creacion=f_cre,
                            fecha_renovacion=f_ren,
                            fecha_vencimiento=f_ven,
                            fecha_caducidad_firma=f_firm,
                            precio_pactado=p_pact,
                            observaciones=obs_serv,
                            mod_ventas=bool(m_v) or 1,
                            mod_compras=bool(m_c) or 0,
                            mod_tesoreria=bool(m_t) or 0,
                            mod_inventario=bool(m_i) or 0
                        )

                        # Crear DatosGeneralesCliente (Usando los datos limpios)
                        cliente = DatosGeneralesCliente.objects.create(
                            servicio=servicio,
                            nombres_cliente=nombre_limpio,
                            ruc_cliente=ruc_limpio,  # Usamos el RUC sin espacios
                            telefono_cliente=str(tel).strip(),
                            correo_cliente=str(mail).strip().lower() if mail else "",
                            proveedor_id=id_prov or 4,
                            estado_id=id_est or 4,
                            regimen_id=id_reg or 2,
                            activo=bool(act),
                            envio_email=bool(env_m),
                            observaciones=obs_gen,
                            contacto_alt=bool(c_alt),
                            telefono_alt=t_alt,
                            correo_alt=m_alt,
                            observacion_alt=o_alt
                        )

                        # Crear DatosTecnicosCliente
                        DatosTecnicosCliente.objects.create(
                            cliente=cliente,
                            servidor_alojamiento_id=id_srv,
                            nombre_basedatos=bdd,
                            url_portal=u_port,
                            clave_portal=c_port,
                            num_portal=n_port,
                            version=vers,
                            firma=firma,
                            num_servicios=n_serv,
                            email_tecnico=mail_t,
                            clave_email=c_mail_t,
                            code_email=cod_mail
                        )
                        exitos += 1
                
                except DatosProducto.DoesNotExist:
                    errores.append(f"Fila {i}: El ID de Plan {id_prod} no existe.")
                    continue
                # Ya no necesitamos el IntegrityError para RUCs porque lo filtramos antes,
                # pero lo dejamos por seguridad para otros campos únicos si existieran.
                except IntegrityError as e:
                    errores.append(f"Fila {i}: Error de integridad (posible duplicado no detectado): {str(e)}")
                    continue
                except Exception as e:
                    errores.append(f"Fila {i}: Error inesperado: {str(e)}")
                    continue

            # Mensajes finales al usuario
            if exitos > 0:
                messages.success(request, f"Proceso finalizado. Cargados: {exitos}. Omitidos (Repetidos): {omitidos}.")
            elif omitidos > 0:
                messages.warning(request, f"No se cargaron nuevos clientes. {omitidos} registros ya existían.")
            
            if errores:
                for err in errores:
                    messages.error(request, err)
                    
            return redirect('lista_clientes')
    else:
        form = CargaMasivaForm() 
    
    return render(request, 'gestion/carga_masiva.html', {'form': form})

@login_required
def api_obtener_ids_clientes(request):
    """Retorna lista de IDs de clientes activos para iterar en el frontend"""
    # Filtramos clientes que tengan datos técnicos y servicio configurado
    ids = list(DatosGeneralesCliente.objects.filter(
        activo=True,
        datos_tecnicos__isnull=False,
        servicio__isnull=False
    ).values_list('id', flat=True))
    
    return JsonResponse({'ids': ids})

@login_required
def api_sincronizar_cliente(request, id_cliente):
    try:
        cliente = DatosGeneralesCliente.objects.get(pk=id_cliente)
        
        srv = cliente.datos_tecnicos.servidor_alojamiento
        db = cliente.datos_tecnicos.nombre_basedatos
        f_ini = cliente.servicio.fecha_renovacion.strftime('%d/%m/%Y')
        f_fin = cliente.servicio.fecha_vencimiento.strftime('%d/%m/%Y')

        cantidad = conectar_y_contar_facturas(
            srv.ip_host, srv.puerto, db, 
            srv.usuario_sql, srv.clave_sql, 
            f_ini, f_fin
        )

        if cantidad is not None:
            cliente.servicio.facturas_consumidas = cantidad
            cliente.servicio.save(update_fields=['facturas_consumidas'])
            verificar_alertas_plan(cliente, cantidad)
            
            return JsonResponse({
                'status': 'ok', 
                'cliente': cliente.nombres_cliente, 
                'cantidad': cantidad
            })
        else:
            return JsonResponse({
                'status': 'error', 
                'cliente': cliente.nombres_cliente, 
                'mensaje': 'Error de conexión'
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
    
@login_required
def api_eventos_calendario(request):
    start_param = request.GET.get('start')
    end_param = request.GET.get('end')

    if start_param:
        start = start_param.split('T')[0]
    else:
        start = None
        
    if end_param:
        end = end_param.split('T')[0]
    else:
        end = None
    
    if not start or not end:
        return JsonResponse([], safe=False)

    clientes = DatosGeneralesCliente.objects.filter(
        servicio__fecha_vencimiento__range=[start, end],
        activo=True
    ).select_related('servicio', 'estado')

    eventos = []

    for c in clientes:
        if not c.servicio.fecha_vencimiento:
            continue
            
        partes_nombre = c.nombres_cliente.split()
        if len(partes_nombre) >= 2:
            titulo = f"{partes_nombre[0]} {partes_nombre[1]}"
        else:
            titulo = c.nombres_cliente

        nombre_estado = c.estado.estado.lower().strip() if c.estado else ""
        
        color = "#ffc107" 
        
        if "pendiente" in nombre_estado:
            color = "#f4a51c" 
        elif "activo" in nombre_estado or "renovado" or "nuevo" in nombre_estado:
            color = "#28a745" 
            
        eventos.append({
            'title': titulo,
            'start': c.servicio.fecha_vencimiento.strftime('%Y-%m-%d'),
            'color': color,
            'url': f"/clientes/editar/{c.id}/",
            'extendedProps': {
                'estado': c.estado.estado
            }
        })

    return JsonResponse(eventos, safe=False)

# VISTA PARA DESUSCRIBIRSE DE CORREOS
def desuscribir_cliente(request, id_cliente):
    cliente = get_object_or_404(DatosGeneralesCliente, pk=id_cliente)
    
    if request.method == 'GET':
        # Cambiamos la bandera a False
        cliente.envio_email = False
        cliente.save()
        
        # Renderizamos una página de confirmación simple
        return render(request, 'gestion/desuscrito.html', {'cliente': cliente})