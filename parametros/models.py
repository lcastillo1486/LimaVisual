from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# Create your models here.

class TipoVenta(models.Model):
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.descripcion}"
    
    class Meta:
        ordering = ["descripcion"]

class TipoFormaPago(models.Model):
    descripcion = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.descripcion}"
    
    class Meta:
        ordering = ["descripcion"]

class DiasCredito(models.Model):
    dias = models.IntegerField() 

    def __str__(self):
        return f"{self.dias}"
    
    class Meta:
        ordering = ["dias"]

class clientes(models.Model):
    ruc = models.CharField(max_length=20, null=True, blank=True, unique=True)
    razon_social = models.CharField(max_length=250, null=True, blank=True)
    nombre_comercial = models.CharField(max_length=250, null=True, blank=True)
    direccion = models.CharField(max_length=250, null=True, blank=True)
    telefono = models.CharField( max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{9}$',
                message="El número de teléfono debe tener 9 dígitos"
            )
        ],
    )
    correo = models.EmailField(
        max_length=254,
        unique=False,
        null=True,
        blank=True,
        help_text="Ingrese un correo electrónico válido."
    )
    correo_contacto = models.EmailField(
        max_length=254,
        unique=False,
        null=True,
        blank=True,
        help_text="Ingrese un correo electrónico válido."
    )
    contacto = models.CharField(max_length=250, null=True, blank=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Usuario asociado a este cliente"
    )
    def __str__(self):
        return f"{self.razon_social}"



