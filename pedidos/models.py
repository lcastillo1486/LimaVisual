from django.db import models
from django.utils import timezone
from parametros.models import TipoVenta, TipoFormaPago, clientes, DiasCredito
from django.contrib.auth.models import User

# Create your models here.

class EstadoNota(models.Model):
    descripcion = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion}"
    
    class Meta:
        ordering = ["descripcion"]

class NotaPedido(models.Model):

    numero_np = models.CharField(max_length=100, null=True, blank=True)
    fecha = models.DateField(default=timezone.now)
    tipo_venta = models.ForeignKey(TipoVenta, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_pago = models.ForeignKey(TipoFormaPago, on_delete=models.SET_NULL, null=True, blank=True)
    dias_credito = models.ForeignKey(DiasCredito, on_delete=models.SET_NULL, null=True, blank=True, default=1)

    cliente = models.ForeignKey(clientes, on_delete=models.SET_NULL, null=True, blank=True, related_name='n_cliente')
    anunciante = models.CharField(max_length=200, null=True, blank=True)

    tarifa_estatica = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarifa_digital = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    razon_social = models.ForeignKey(clientes, on_delete=models.SET_NULL, null=True, blank=True, related_name='n_razon_social')
    ruc = models.CharField(max_length=20, null=True, blank=True)
    contacto = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)

    detalle_ubicaciones = models.TextField(null=True, blank=True)
    detalle_facturacion = models.TextField(null=True, blank=True)

    motivo_rechazo_anulacion = models.CharField(max_length=250, blank=True, null=True)
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Usuario asociado a este cliente"
    )
    estado = models.ForeignKey(EstadoNota, on_delete=models.SET_NULL, null=True, blank=True, default=1)
    rel_edicion = models.IntegerField(null=True, blank=True)

class DetalleUbicacion(models.Model):
    nota = models.ForeignKey(
            'NotaPedido', 
            on_delete=models.CASCADE, 
            related_name='detalles_ubicacion'
        )
    ubicacion = models.ForeignKey(
            'ubicaciones.ubicacion',   
            on_delete=models.SET_NULL, 
            null=True, 
            blank=True
        )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    dias = models.PositiveIntegerField(default=0)
    tarifa_mes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarifa_dia = models.DecimalField(max_digits=25, decimal_places=15, default=0)
    total_tarifa_ubi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.ForeignKey('ubicaciones.EstadoFijasDigital', on_delete=models.PROTECT, related_name='estado_ubi_fija', default=2)

class NumeroNotaBonificacion(models.Model):
    pedido = models.OneToOneField(NotaPedido, on_delete=models.CASCADE, related_name="nota_bonificacion")
    numero = models.CharField(max_length=20, unique=True)  
    archivo_pdf = models.FileField(upload_to="guias/", blank=True, null=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.numero} - Pedido {self.pedido.id}"
    
class NumeroNotaAgencia(models.Model):
    pedido = models.OneToOneField(NotaPedido, on_delete=models.CASCADE, related_name="nota_agencia")
    numero = models.CharField(max_length=20, unique=True)  
    archivo_pdf = models.FileField(upload_to="guias/", blank=True, null=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.numero} - Pedido {self.pedido.id}"
    
class NumeroNotaCanje(models.Model):
    pedido = models.OneToOneField(NotaPedido, on_delete=models.CASCADE, related_name="nota_canje")
    numero = models.CharField(max_length=20, unique=True)  
    archivo_pdf = models.FileField(upload_to="guias/", blank=True, null=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.numero} - Pedido {self.pedido.id}"

class NumeroNotaDirecto(models.Model):
    pedido = models.OneToOneField(NotaPedido, on_delete=models.CASCADE, related_name="nota_directo")
    numero = models.CharField(max_length=20, unique=True)  
    archivo_pdf = models.FileField(upload_to="guias/", blank=True, null=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.numero} - Pedido {self.pedido.id}"
    
class NumeroNotaProgramatica(models.Model):
    pedido = models.OneToOneField(NotaPedido, on_delete=models.CASCADE, related_name="nota_programatica")
    numero = models.CharField(max_length=20, unique=True)  
    archivo_pdf = models.FileField(upload_to="guias/", blank=True, null=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.numero} - Pedido {self.pedido.id}"

class ControlUsuario(models.Model):
    name_user = models.CharField(max_length=200, blank=True, null= True)
    fecha = models.DateField()
    primer_login = models.BooleanField(default=False)