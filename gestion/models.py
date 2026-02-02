from django.db import models

# TABLA PARA LOS DATOS DEL SERVIDOR DE BASE DE DATOS EXTERNAS
class ServidorBaseDatos(models.Model):
    nombre_identificador = models.CharField(max_length=50, help_text="Ej: Servidor Principal, Servidor Secundario")
    ip_host = models.CharField(max_length=50, help_text="Dirección IP o DNS del servidor SQL")
    puerto = models.IntegerField(default=1433)
    usuario_sql = models.CharField(max_length=100, help_text="Usuario con permisos de lectura")
    clave_sql = models.CharField(max_length=100, help_text="Contraseña de conexión a la BD externa")

    def __str__(self):
        return f"{self.nombre_identificador} ({self.ip_host})"

# TABLA PARA LOS DATOS DE LOS ESTADOS DEL CLIENTE
class EstadoCliente(models.Model):
    estado = models.CharField(max_length=50)

    def __str__(self):
        return self.estado

# TABLA PARA LOS DATOS DE LOS PRODUCTOS
class DatosProducto(models.Model):
    nombre_producto = models.CharField(max_length=50)
    plan_num = models.IntegerField(help_text="Número de facturas permitidas al año")
    precio = models.DecimalField(max_digits=10, decimal_places=2) 
    vigencia = models.IntegerField(help_text="Vigencia en meses o días según lógica de negocio")

    def __str__(self):
        return f"{self.nombre_producto} - ${self.precio}"
    
# TABLA PARA LOS DATOS DE LOS REGÍMENES TRIBUTARIOS
class DatosRegimen(models.Model):
    nombre = models.CharField(max_length=50) 

    def __str__(self):
        return self.nombre

# TABLA PARA LOS DATOS DE LOS PROVEEDORES
class DatosProveedor(models.Model):
    nombre = models.CharField(max_length=200)
    ruc = models.CharField(max_length=13, unique=True, verbose_name="RUC Proveedor")
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=10)

    def __str__(self):
        return self.nombre

# TABLA PARA LOS DATOS DEL SERVICIO DEL CLIENTE
class DatosServicio(models.Model):
    # Relaciones
    producto = models.ForeignKey(DatosProducto, on_delete=models.PROTECT)
    
    # Fechas
    fecha_creacion = models.DateField(null=True, blank=True, verbose_name="Fecha de Creación")
    fecha_renovacion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_caducidad_firma = models.DateField(null=True, blank=True, verbose_name="Caducidad Firma")

    # Consumo de facturas electrónicas
    facturas_consumidas = models.IntegerField(default=0, help_text="Actualizado automáticamente desde BD externa")

    # Otros campos
    precio_pactado = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(null=True, blank=True)

    # Módulos del sistema
    mod_ventas = models.BooleanField(default=True, verbose_name="Ventas (Facturación)")
    mod_compras = models.BooleanField(default=False, verbose_name="Compras (Liq/Ret)")
    mod_tesoreria = models.BooleanField(default=False, verbose_name="Tesoreria (C x P/C)")
    mod_inventario = models.BooleanField(default=False, verbose_name="Inventario (Kardex)")

    def __str__(self):
        return f"Servicio {self.id} - Plan: {self.producto.nombre_producto}"

# TABLA PARA LOS DATOS GENERALES DEL CLIENTE
class DatosGeneralesCliente(models.Model):
    # Relaciones
    servicio = models.OneToOneField(DatosServicio, on_delete=models.CASCADE)
    
    # Campos generales
    nombres_cliente = models.CharField(max_length=200)
    ruc_cliente = models.CharField(max_length=13, unique=True, verbose_name="RUC Cliente")
    telefono_cliente = models.CharField(max_length=10)
    correo_cliente = models.EmailField(max_length=100)
    activo = models.BooleanField(default=True, verbose_name="Cliente Activo")
    proveedor = models.ForeignKey(DatosProveedor, on_delete=models.PROTECT, default=4)
    estado = models.ForeignKey(EstadoCliente, on_delete=models.PROTECT, default=4)
    regimen = models.ForeignKey(DatosRegimen, on_delete=models.SET_NULL, null=True, blank=True, default=2, verbose_name="Régimen Tributario")  
    envio_email = models.BooleanField(default=True)
    observaciones = models.TextField(null=True, blank=True)

    # Campos Alternativos
    contacto_alt = models.BooleanField(default=False)
    telefono_alt = models.CharField(max_length=10, null=True, blank=True)
    correo_alt = models.EmailField(max_length=100, null=True, blank=True)
    observacion_alt = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombres_cliente} ({self.ruc_cliente})"

# TABLA PARA LOS DATOS TÉCNICOS DEL CLIENTE
class DatosTecnicosCliente(models.Model):
    # Relaciones
    cliente = models.OneToOneField(DatosGeneralesCliente, on_delete=models.CASCADE, related_name='datos_tecnicos')
    
    # CONEXIÓN BASE DE DATOS EXTERNA 
    servidor_alojamiento = models.ForeignKey(ServidorBaseDatos, on_delete=models.PROTECT)
    nombre_basedatos = models.CharField(max_length=100)

    # Datos del Portal Web
    url_portal = models.CharField(max_length=200, blank=True, null=True)
    clave_portal = models.CharField(max_length=100, blank=True, null=True)
    num_portal = models.IntegerField(null=True, blank=True)
    
    # Otros datos técnicos
    version = models.IntegerField(null=True, blank=True)
    firma = models.CharField(max_length=100, null=True, blank=True)
    num_servicios = models.IntegerField(null=True, blank=True)
    
    # Email técnico
    email_tecnico = models.EmailField(max_length=100, null=True, blank=True)
    clave_email = models.CharField(max_length=100, null=True, blank=True)
    code_email = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Datos Técnicos: {self.nombre_basedatos} en {self.servidor_alojamiento}"