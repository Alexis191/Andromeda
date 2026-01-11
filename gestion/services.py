import pyodbc
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail

def conectar_y_contar_facturas(ip, puerto, db, user, password, fecha_ini_str, fecha_fin_str):
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={ip},{puerto};'
        f'DATABASE={db};'
        f'UID={user};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
        'Connection Timeout=10;'
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            query = """
                SELECT COUNT(*) 
                FROM FacElec_Documentos 
                WHERE FechaEmision >= ? AND FechaEmision < ?
            """
            cursor.execute(query, (fecha_ini_str, fecha_fin_str))
            row = cursor.fetchone()
            return row[0] if row else 0
    except Exception as e:
        print(f"Error de conexión SQL: {e}")
        return None

def verificar_alertas_plan(cliente, consumo_actual):
    """
    Verifica si el cliente superó el 80% o 90% y envía correo.
    """
    if not cliente.servicio or not cliente.servicio.producto:
        return

    producto = cliente.servicio.producto
    limite_plan = int(producto.plan_num) if str(producto.plan_num).isdigit() else 0
    nombre_plan = producto.nombre_producto.lower()

    # Si es ilimitado o plan 0, no alertamos
    if limite_plan <= 0 or "ilimitado" in nombre_plan:
        return

    porcentaje = (consumo_actual / limite_plan) * 100
    tipo_alerta = ""
    asunto = ""

    if porcentaje >= 90:
        tipo_alerta = "CRÍTICA"
        asunto = f"🚨 ALERTA CRÍTICA: Cliente {cliente.nombres_cliente} al {porcentaje:.1f}% de su plan"
    elif porcentaje >= 80:
        tipo_alerta = "ADVERTENCIA"
        asunto = f"⚠️ ALERTA DE CONSUMO: Cliente {cliente.nombres_cliente} al {porcentaje:.1f}% de su plan"

    if asunto:
        mensaje = (
            f"El cliente {cliente.nombres_cliente} (RUC: {cliente.ruc_cliente}) ha emitido "
            f"{consumo_actual} de {limite_plan} facturas permitidas.\n\n"
            f"Plan: {producto.nombre_producto}\n"
            f"Vencimiento: {cliente.servicio.fecha_vencimiento}\n\n"
            "Acción requerida: Contactar al cliente para ampliación de plan."
        )
        
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                settings.OPERATIONS_EMAIL, 
                fail_silently=False,
            )
            print(f"Correo enviado para {cliente.nombres_cliente} ({tipo_alerta})")
        except Exception as e:
            print(f"Error enviando correo: {e}")