from django.urls import path
from .views import crea_ubicacion, verificar_codigo, editar_ubicacion

urlpatterns = [
    path('crear/ubicacion/',crea_ubicacion, name='crear_ubicacion'),
    path('verificar-codigo/', verificar_codigo, name='verificar_codigo'),
    path('editar-ubicacion/<int:ubicacion_id>/', editar_ubicacion, name='editar_ubicacion'),
]