from django.urls import path
from .views import nuevo_pedido, obtener_ocupaciones_fijas, calendario_ocupaciones_fijas, obtener_ocupaciones_digitales, calendario_ocupaciones_digitales, generar_pdf_nota, verificar_disponibilidad, verificar_disponibilidad_digital, gestion_notas, generar_pdf_nota, cambiar_estado_nota, filtrar_notas, ver_dashboard, dashboard_data, dashboard, aprobar_negar_np, filtrar_notas_n_autoriza, detalle_aprobar_negar_np, aprobar_nota, rechazar_nota, calendario_ocupaciones_digitales_canje, editar_fechas_montos

urlpatterns = [
    path('crear/pedido/',nuevo_pedido, name='crear_pedido'),
    path('api/ocupaciones-fijas/', obtener_ocupaciones_fijas, name='api_ocupaciones_fijas'),
    path('calendario/fijas/', calendario_ocupaciones_fijas, name='calendario_fijas'),
    path('api/ocupaciones-digitales/', obtener_ocupaciones_digitales, name='api_ocupaciones_digitales'),
    path('calendario/digitales/', calendario_ocupaciones_digitales, name='calendario_digitales'),
    path('calendario/canjes/', calendario_ocupaciones_digitales_canje, name='calendario_canjes'),
    path('nota/pdf/<int:nota_id>/', generar_pdf_nota, name='generar_pdf_nota'),
    path('api/verificar_disponibilidad/', verificar_disponibilidad, name='verificar_disponibilidad'),
    path('api/verificar_disponibilidad_digital/', verificar_disponibilidad_digital, name='verificar_disponibilidad_digital'),
    path('mis-pedidos/', gestion_notas, name='gestion_notas'),
    path('nota/cambiar_estado/', cambiar_estado_nota, name='cambiar_estado_nota'),
    path('filtrar_notas/', filtrar_notas, name='filtrar_notas'),
    path('dashboard/', ver_dashboard, name='dashboard-data'),
    path("dashboard-data/", dashboard_data, name="dashboard_data"),
    path('dashboard1/', dashboard, name='dashboard'),
    path('aprobar-negar-np/', aprobar_negar_np, name='autorizar'),
    path('filtrar_notas_n_autoriza/', filtrar_notas_n_autoriza, name='filtrar_notas_n_autoriza'),
    path('detalle_notas_n_autoriza/<int:nota_id>/', detalle_aprobar_negar_np, name='detalle_aprobar_negar_np'),
    path('aprobar-np/<int:nota_id>/', aprobar_nota, name='aprobacion'),
    path('rechazar-np/<int:nota_id>/', rechazar_nota, name='rechazo'),
    path('editar_fechas_montos/<int:nota_id>/', editar_fechas_montos, name='editar_fechas_montos'),
]