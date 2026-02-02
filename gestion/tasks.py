import logging
import sys
import os
import traceback
from datetime import datetime, date, timedelta
from django.conf import settings
from .models import DatosGeneralesCliente, EstadoCliente
from .services import *
from django.core.mail import send_mail

class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if line.strip():
                self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def enviar_alerta_operaciones(asunto, lista_errores):
    if not lista_errores:
        return

    mensaje_cuerpo = "Se han detectado los siguientes errores/advertencias en la tarea de monitoreo diario:\n\n"
    for error in lista_errores:
        mensaje_cuerpo += f"- {error}\n"
    
    mensaje_cuerpo += f"\nFecha de ejecución: {datetime.now()}"

    try:
        send_mail(
            subject=f"⚠️ [ALERTA ANDRÓMEDA] {asunto}",
            message=mensaje_cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.OPERATIONS_EMAIL,
            fail_silently=False,
        )
        print("Correo de alerta enviado a Operaciones.")
    except Exception as e:
        print(f"Error al enviar alerta por correo: {e}")

# --- FUNCIÓN PRINCIPAL ---
def tarea_monitoreo_diario():
    # 1. Configuración del LOG Dinámico
    hoy_str = date.today().strftime('%Y-%m-%d')
    log_filename = f"automatizacion_{hoy_str}.log"
    log_dir = getattr(settings, 'LOGS_DIR', 'logs') 
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(f'automatizacion_{hoy_str}')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.__stdout__)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    stdout_original = sys.stdout
    stderr_original = sys.stderr

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    logger.info("="*50)
    logger.info(f"INICIO EJECUCIÓN TAREA: {datetime.now()}")
    logger.info("="*50)

    errores_detectados = []

    try:
        print(f"--- Ejecutando Monitoreo de Estados: {date.today()} ---")

        try:
            estado_pendiente = EstadoCliente.objects.get(id=1)
        except EstadoCliente.DoesNotExist:
            print("ERROR CRÍTICO: No existe el estado con ID=1 (Pendiente). Revise la tabla EstadoCliente.")
            estado_pendiente = None

        clientes = DatosGeneralesCliente.objects.filter(
            activo=True, 
            servicio__isnull=False, 
            datos_tecnicos__isnull=False
        )
        
        hoy = date.today()
        DIAS_PARA_AVISO = 5
        
        count_cambios = 0
        exitos = 0
        errores = 0

        for cliente in clientes:
            try:
                if estado_pendiente and cliente.servicio.fecha_vencimiento:
                    dias = (cliente.servicio.fecha_vencimiento - hoy).days
                    
                    if 0 <= dias <= DIAS_PARA_AVISO and cliente.estado.id != 1:
                        print(f"-> CAMBIO ESTADO AUTOMÁTICO: {cliente.nombres_cliente}. (Vence en {dias} días).")
                        
                        cliente.estado = estado_pendiente
                        cliente.save(update_fields=['estado'])
                        count_cambios += 1
                
                srv = cliente.datos_tecnicos.servidor_alojamiento
                db = cliente.datos_tecnicos.nombre_basedatos
                
                if cliente.servicio.fecha_renovacion and cliente.servicio.fecha_vencimiento:
                    f_ini = cliente.servicio.fecha_renovacion.strftime('%d/%m/%Y')
                    f_fin = cliente.servicio.fecha_vencimiento.strftime('%d/%m/%Y')
                    
                    consumo = conectar_y_contar_facturas(
                        srv.ip_host, srv.puerto, db, 
                        srv.usuario_sql, srv.clave_sql, 
                        f_ini, f_fin
                    )
                    
                    if consumo is not None:
                        cliente.servicio.facturas_consumidas = consumo 
                        cliente.servicio.save(update_fields=['facturas_consumidas'])
                        
                        verificar_alertas_plan(cliente, consumo)
                        
                        print(f"[OK] {cliente.nombres_cliente}: {consumo} facturas.")
                        exitos += 1
                    else:
                        msg = f"[ERROR SQL] {cliente.nombres_cliente} en {srv.ip_host} ({db})"
                        print(msg)
                        errores_detectados.append(msg)
                        errores += 1

                verificar_vencimiento_15_dias(cliente)

            except Exception as e:
                msg = f"[ERROR PROCESANDO CLIENTE] {cliente.nombres_cliente}: {e}"
                print(msg)
                traceback.print_exc()
                errores_detectados.append(msg)
                errores += 1

        logger.info("-" * 50)
        logger.info(f"RESUMEN FINAL: Clientes procesados: {len(clientes)}")
        logger.info(f"   - Estados cambiados a Pendiente: {count_cambios}")
        logger.info(f"   - Lecturas SQL exitosas: {exitos}")
        logger.info(f"   - Errores encontrados: {errores}")

        if errores_detectados:
            logger.info(f"Enviando reporte de {len(errores_detectados)} errores a Operaciones...")
            enviar_alerta_operaciones("Reporte de Errores", errores_detectados)

    except Exception as e:
        msg_fatal = f"ERROR FATAL EN LA TAREA PRINCIPAL: {e}"
        logger.critical(msg_fatal)
        traceback.print_exc()

        enviar_alerta_operaciones("¡FALLO CRÍTICO DEL SCRIPT!", [msg_fatal])

    finally:
        sys.stdout = stdout_original
        sys.stderr = stderr_original
        
        logger.info(f"FIN EJECUCIÓN: {datetime.now()}")
        logger.info("=" * 50)
        
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)