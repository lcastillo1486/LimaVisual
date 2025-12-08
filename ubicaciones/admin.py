from django.contrib import admin
from .models import TipoUbicacion, SlotDigital, ubicacion, EstadoFijasDigital

# Register your models here.
admin.site.register(TipoUbicacion)
admin.site.register(SlotDigital)
admin.site.register(ubicacion)
admin.site.register(EstadoFijasDigital)