from django.db import models

# Create your models here.

class EstadoFijasDigital(models.Model):
    descripcion = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion}"
    
    class Meta:
        ordering = ["descripcion"]

class TipoUbicacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class ubicacion(models.Model):
    codigo = models.CharField(max_length=10, blank=True, null=True)
    direccion = models.CharField(max_length=250, blank=True, null=True)
    referencia = models.CharField(max_length=250, blank=True, null=True)
    tipo = models.ForeignKey(TipoUbicacion, on_delete=models.SET_NULL, null=True, blank=True)
    tarifa_fria = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tarifa_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    medidas = models.CharField(max_length=100, null=True, blank=True, default='No especificado')
    medidas_pixel = models.CharField(max_length=100, null=True, blank=True, default='No especificado')
    pixel_pitch = models.CharField(max_length=100, null=True, blank=True, default='No especificado')
                               

    def __str__(self):
        return f"{self.codigo}"

class SlotDigital(models.Model):
    ubicacion = models.ForeignKey(ubicacion, on_delete=models.CASCADE, related_name='slots')
    numero_slot = models.PositiveIntegerField()  # 1..10
    nombre = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)
    es_canje = models.BooleanField(default=False)
    tarifa_fria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarifa_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        unique_together = ('ubicacion', 'numero_slot')

    def __str__(self):
        return f"{self.ubicacion.codigo} - Slot {self.numero_slot}"


class ReservaSlot(models.Model):
    slot = models.ForeignKey('ubicaciones.SlotDigital', on_delete=models.CASCADE, related_name='reservas')
    nota_pedido = models.ForeignKey('pedidos.NotaPedido', on_delete=models.CASCADE, related_name='reservas_nota')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveIntegerField(default=0)
    estado = models.ForeignKey(EstadoFijasDigital, on_delete=models.PROTECT, related_name='estado_ubi_slot')
    tarifa_mes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarifa_dia = models.DecimalField(max_digits=25, decimal_places=15, default=0)
    total_tarifa_slot = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        indexes = [models.Index(fields=['slot', 'fecha_inicio', 'fecha_fin'])]

    def __str__(self):
        return f"{self.slot} ({self.fecha_inicio} - {self.fecha_fin})"