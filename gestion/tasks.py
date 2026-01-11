from datetime import datetime
from .models import DatosGeneralesCliente
from .services import *

def tarea_monitoreo_diario():
    print(f"--- Iniciando Monitoreo Automático: {datetime.now()} ---")
    
    # Solo clientes activos que tengan servicio y datos técnicos
    clientes = DatosGeneralesCliente.objects.filter(
        activo=True, 
        servicio__isnull=False, 
        datos_tecnicos__isnull=False
    )
    
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
                verificar_alertas_plan(cliente, consumo)
                
                print(f"✅ {cliente.nombres_cliente}: {consumo} facturas actualizadas.")
            else:
                print(f"❌ {cliente.nombres_cliente}: Error de conexión SQL (No se pudo contar facturas).")

            # --- BLOQUE 3: VENCIMIENTO DE PLAN (NUEVO REQUERIMIENTO) ---
            # Esto se ejecuta INCLUSO si falló la conexión SQL arriba.
            # Es vital que el aviso de fecha se envíe independientemente del estado del servidor del cliente.
            verificar_vencimiento_15_dias(cliente)
                
        except Exception as e:
            print(f"Error procesando cliente {cliente.id}: {e}")

    print("--- Fin del Monitoreo ---")