from django.contrib import admin

# Register your models here.
from .models import TipoVenta, TipoFormaPago, DiasCredito, clientes

admin.site.register(TipoFormaPago)
admin.site.register(TipoVenta)
admin.site.register(DiasCredito)
admin.site.register(clientes)