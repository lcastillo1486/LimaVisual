from django.urls import path
from .views import CrearParametros, tipo_forma_pago_guardar, tipo_venta_guardar, dias_credito_guardar, crear_cliente, verificar_ruc, listar_clientes, editar_cliente, buscar_empresa


urlpatterns = [
    path('crear-parametros/',CrearParametros, name='crear_parametros'),
    path("tipo-venta/guardar/", tipo_venta_guardar, name="tipo_venta_guardar"),
    path("tipo-forma-pago/guardar/", tipo_forma_pago_guardar, name="tipo_forma_pago_guardar"),
    path("dias-credito/guardar/", dias_credito_guardar, name="dias_credito_guardar"),
    path("crear-cliente/", crear_cliente, name="crear_cliente"),
    path("listar-cliente/", listar_clientes, name="listar_cliente"),
    path("editar-cliente/<int:cliente_id>", editar_cliente, name="editar_cliente"),
    path('verificar_ruc/',verificar_ruc, name='verificar_ruc'),
    path('buscar-empresa/', buscar_empresa, name='buscar_empresa')

]
