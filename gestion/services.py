import pyodbc
from datetime import date
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

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
                FROM Factur_TransaccionCabs 
                WHERE FechaTransaccion >= CONVERT(datetime, ?, 103) 
                  AND FechaTransaccion < CONVERT(datetime, ?, 103) AND TipoMovimiento = 02
            """
            cursor.execute(query, (fecha_ini_str, fecha_fin_str))
            row = cursor.fetchone()
            return row[0] if row else 0
    except Exception as e:
        print(f"Error de conexión SQL: {e}")
        return None

def verificar_alertas_plan(cliente, consumo_actual):
    """
    Verifica si el cliente superó el 80% o 90% y almacena la información.
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

    if porcentaje >= 90:
        tipo = "CRÍTICA (>=90%)"
    elif porcentaje >= 86:
        tipo = "ADVERTENCIA (>=86%)"
    else:
        return None

    return f"- [{tipo}] {cliente.nombres_cliente} (RUC: {cliente.ruc_cliente}): {consumo_actual}/{limite_plan} facturas consumidas ({porcentaje:.1f}%). Fecha de vencimiento: {cliente.servicio.fecha_vencimiento}"

def verificar_vencimiento_15_dias(cliente):
    """
    Verifica si faltan entre 15 y 20 días para el vencimiento y envía correo HTML.
    Utiliza una bandera de base de datos para evitar correos duplicados.
    """
    # 1. Validaciones previas
    if not cliente.servicio or not cliente.servicio.fecha_vencimiento:
        return

    # IMPORTANTE: Respetar la Ley de Protección de Datos
    if not cliente.envio_email:
        print(f"Omitiendo aviso de vencimiento a {cliente.nombres_cliente} (Desuscrito).")
        return

    # 2. Calcular días restantes
    hoy = date.today()
    fecha_venc = cliente.servicio.fecha_vencimiento
    dias_restantes = (fecha_venc - hoy).days

    # 3. Detectar si faltan entre 15 y 20 días y si aún no se ha enviado la alerta
    if 15 <= dias_restantes <= 20 and not cliente.servicio.alerta_vencimiento_enviada:
        print(f"Enviando aviso de {dias_restantes} días a {cliente.nombres_cliente}...")
        
        # Configuración del correo
        asunto = f"Tu plan vence en {dias_restantes} días - {cliente.nombres_cliente}"
        remitente = settings.DEFAULT_FROM_EMAIL
        destinatario = [cliente.correo_cliente]
        
        # URL de desuscripción (Ajusta el dominio 'tu-dominio.com' al tuyo real o IP)
        # En producción deberías usar: settings.BASE_URL o request.build_absolute_uri
        #link_baja = f"http://127.0.0.1:8000/desuscribir/{cliente.id}/" 

        # Contenido HTML Profesional
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Poppins, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #f4a51c; padding: 20px; text-align: center;">
                  <h2 style="color: white; margin: 0;">CORPORACIÓN MENATICS</h2>
                </div>
                
                <div style="padding: 20px;">
                  <h2 style="color: #f4a51c; text-align: center;">Sistema de Facturación Electrónica</h2>
                    <h3 style="color: #f4a51c;">Estimado(a) {cliente.nombres_cliente},</h3>
                    <p>Esperamos que te encuentres muy bien.</p>
                    <p>Te informamos que tu plan de facturación electrónica <strong>{cliente.servicio.producto.nombre_producto}</strong> está próximo a vencer.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #f4a51c; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Fecha de Vencimiento:</strong> {fecha_venc.strftime('%d/%m/%Y')}</p>
                        <p style="margin: 5px 0;"><strong>Días Restantes:</strong> {dias_restantes} días</p>
                    </div>

                    <p>Te invitamos a renovar tu servicio a tiempo para evitar interrupciones en la emisión de tus comprobantes.</p>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="https://wa.link/0z47oy" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Contactar para Renovar</a>
                    </p>
                </div>

                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                    <p>Has recibido este correo porque eres cliente de Menatics.</p>
                    <p>
                        ¿Ya no deseas recibir estos recordatorios?<br>
                        Envía un correo electrónico a: soportecnico@menaticscorp.com.ec 
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            msg = EmailMultiAlternatives(asunto, strip_tags(html_content), remitente, destinatario)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print("Correo enviado exitosamente.")
            cliente.servicio.alerta_vencimiento_enviada = True
            cliente.servicio.save()
            print(f"Bandera de seguridad actualizada para {cliente.nombres_cliente}.")
        except Exception as e:
            print(f"Error enviando correo a {cliente.nombres_cliente}: {e}")

#<a href="{link_baja}" style="color: #dc3545; text-decoration: underline;">Date de baja aquí</a>.