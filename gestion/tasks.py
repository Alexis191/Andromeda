import logging
from datetime import datetime
from .models import DatosGeneralesCliente
from .services import *

logger = logging.getLogger('gestion_logger')

def tarea_monitoreo_diario():
    logger.info(f"--- Iniciando Monitoreo Automático: {datetime.now()} ---")
    
    # Solo clientes activos que tengan servicio y datos técnicos
    clientes = DatosGeneralesCliente.objects.filter(
        activo=True, 
        servicio__isnull=False, 
        datos_tecnicos__isnull=False
    )

    # Contadores para el resumen final
    exitos = 0
    errores = 0
    for cliente in clientes:
        try:
            # --- BLOQUE 1: DATOS DE CONEXIÓN ---
            srv = cliente.datos_tecnicos.servidor_alojamiento
            db = cliente.datos_tecnicos.nombre_basedatos
            
            # Formatear fechas del servicio actual
            f_ini = cliente.servicio.fecha_renovacion.strftime('%d/%m/%Y')
            f_fin = cliente.servicio.fecha_vencimiento.strftime('%d/%m/%Y')
            
            # --- BLOQUE 2: CONSUMO DE FACTURAS ---
            consumo = conectar_y_contar_facturas(
                srv.ip_host, srv.puerto, db, 
                srv.usuario_sql, srv.clave_sql, 
                f_ini, f_fin
            )
            
            if consumo is not None:
                # 2.1 Guardar en Base de Datos
                cliente.servicio.facturas_consumidas = consumo 
                cliente.servicio.save(update_fields=['facturas_consumidas'])
                
                # 2.2 Verificar Alertas de Consumo (80% / 90%)
                alerta_enviada = verificar_alertas_plan(cliente, consumo) # Asumiendo que esta función devuelve True si envió email
                
                msg_extra = " | Alerta enviada" if alerta_enviada else ""
                logger.info(f"CLIENTE: {cliente.nombres_cliente} | ID: {cliente.id} | Consumo: {consumo} facturas{msg_extra}")
                exitos += 1
            else:
                logger.warning(f"FALLO CONEXION SQL: {cliente.nombres_cliente} | Host: {srv.ip_host} | DB: {db}")
                errores += 1
                
            # --- BLOQUE 3: VENCIMIENTO DE PLAN (NUEVO REQUERIMIENTO) ---
            # Esto se ejecuta INCLUSO si falló la conexión SQL arriba.
            # Es vital que el aviso de fecha se envíe independientemente del estado del servidor del cliente.
            verificar_vencimiento_15_dias(cliente)
                
        except Exception as e:
            logger.error(f"ERROR CRITICO Cliente {cliente.nombres_cliente}: {str(e)}", exc_info=True)
            errores += 1

    logger.info(f"--- Fin del Monitoreo. Procesados: {len(clientes)} | Exitos: {exitos} | Errores: {errores} ---")