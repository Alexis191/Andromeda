# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

# Django contrib
from django.contrib import messages
from django.contrib.auth.models import User

# Models y forms locales
from .models import *
from .forms import *

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
    estados = DatosServicio.objects.all()

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

@csrf_exempt # Usamos csrf_exempt para facilitar la llamada AJAX rápida en el prototipo
def consultar_facturas_externas(request):
    if request.method == 'POST':
        try:
            # 0. Decodificar JSON
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'mensaje': 'JSON inválido enviado por el navegador.'})
            
            # 1. Obtener datos del Request
            servidor_id = data.get('servidor')
            db_name = data.get('db_name')
            fecha_inicio_str = data.get('fecha_inicio')
            fecha_fin_str = data.get('fecha_fin')

            # Validación básica
            if not servidor_id or not db_name or not fecha_inicio_str:
                return JsonResponse({'status': 'error', 'mensaje': 'Faltan datos (Servidor, BD o Fechas).'})

            # --- 2. CONVERSIÓN DE FECHAS (DD/MM/YYYY) ---
            try:
                # Convertir de YYYY-MM-DD (Input HTML) a Objeto Fecha
                fecha_obj_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                fecha_obj_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')

                # Convertir de Objeto Fecha a String DD/MM/YYYY (Formato SQL Server Exigido)
                fecha_sql_inicio = fecha_obj_inicio.strftime('%d/%m/%Y')
                fecha_sql_fin = fecha_obj_fin.strftime('%d/%m/%Y')
                
                print(f"DEBUG: Consultando fechas: {fecha_sql_inicio} y {fecha_sql_fin}")

            except ValueError:
                return JsonResponse({'status': 'error', 'mensaje': 'Formato de fecha inválido.'})

            # --- 3. BUSCAR CREDENCIALES DEL SERVIDOR ---
            try:
                servidor_obj = ServidorBaseDatos.objects.get(pk=servidor_id)
            except ServidorBaseDatos.DoesNotExist:
                return JsonResponse({'status': 'error', 'mensaje': 'Servidor no encontrado en catálogo.'})

            # --- 4. CONECTAR A LA BASE EXTERNA ---
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={servidor_obj.ip_host},{servidor_obj.puerto};'
                f'DATABASE={db_name};'
                f'UID={servidor_obj.usuario_sql};'
                f'PWD={servidor_obj.clave_sql};'
                'TrustServerCertificate=yes;'
                'Connection Timeout=5;'
            )

            print(f"DEBUG: Conectando a {servidor_obj.ip_host} -> {db_name}...")
            
            # --- MANEJO DE ERROR DE CONEXIÓN ESPECÍFICO ---
            try:
                conn = pyodbc.connect(conn_str)
            except Exception as e:
                print(f"ERROR CONEXIÓN: {e}")
                return JsonResponse({'status': 'error', 'mensaje': 'No se pudo conectar al SQL Server remoto. Revisa IP/Usuario.'})

            cursor = conn.cursor()
            
            # --- 5. EJECUTAR CONSULTA ---
            query = """
                SELECT COUNT(*) AS TotalDocumentos
                FROM FacElec_Documentos
                WHERE FechaEmision >= ? AND FechaEmision < ?
            """
            
            try:
                # Pasamos las fechas YA FORMATEADAS como strings "23/12/2024"
                cursor.execute(query, (fecha_sql_inicio, fecha_sql_fin))
                row = cursor.fetchone()
                cantidad = row[0] if row else 0
            except Exception as e:
                print(f"ERROR QUERY: {e}")
                return JsonResponse({'status': 'error', 'mensaje': f'Error al leer tabla FacElec_Documentos: {str(e)}'})
            
            conn.close()
            
            return JsonResponse({'status': 'ok', 'cantidad': cantidad})

        except Exception as e:
            # Captura cualquier otro error de Python (sintaxis, variables no definidas)
            print(f"ERROR CRÍTICO: {e}") 
            return JsonResponse({'status': 'error', 'mensaje': f'Error interno del servidor: {str(e)}'})
            
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
            errores = []

            for i, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
                if not any(fila): continue # Salta filas vacías

                # DESEMPAQUETADO EXACTO (36 columnas según la lista de arriba)
                (
                    nom, ruc, tel, mail, id_prov, id_est, id_reg, act, env_m, obs_gen,
                    c_alt, t_alt, m_alt, o_alt,
                    id_prod, p_pact, f_cre, f_ren, f_ven, f_firm, m_v, m_c, m_t, m_i, obs_serv,
                    id_srv, bdd, u_port, c_port, n_port, vers, firma, n_serv, mail_t, c_mail_t, cod_mail
                ) = fila

                try:
                    with transaction.atomic():
                        # 1. Crear DatosServicio
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

                        # 2. Crear DatosGeneralesCliente
                        cliente = DatosGeneralesCliente.objects.create(
                            servicio=servicio,
                            nombres_cliente=str(nom).upper(),
                            ruc_cliente=str(ruc),
                            telefono_cliente=str(tel),
                            correo_cliente=str(mail).lower() if mail else "",
                            proveedor_id=id_prov or 4, # Usa ID 4 si viene vacío
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

                        # 3. Crear DatosTecnicosCliente
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
                except IntegrityError:
                    errores.append(f"Fila {i}: El RUC {ruc} ya está registrado.")
                    continue
                except Exception as e:
                    errores.append(f"Fila {i}: Error inesperado: {str(e)}")
                    continue

            if exitos > 0:
                messages.success(request, f"Se cargaron {exitos} clientes con éxito.")
            if errores:
                for err in errores:
                    messages.error(request, err)
                    
            return redirect('lista_clientes')
    else:
        form = CargaMasivaForm() 
    
    return render(request, 'gestion/carga_masiva.html', {'form': form})