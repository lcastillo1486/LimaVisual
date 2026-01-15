from django.shortcuts import render, redirect, get_object_or_404
from parametros.models import TipoFormaPago, TipoVenta, DiasCredito, clientes
from ubicaciones.models import ubicacion, SlotDigital, ReservaSlot
from .models import NumeroNotaAgencia, NumeroNotaBonificacion, NumeroNotaCanje, NumeroNotaDirecto, NumeroNotaProgramatica, EstadoNota
from datetime import date
from django.db.models import Q
from django.contrib import messages
from .models import NotaPedido, DetalleUbicacion
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
import io, json
from django.conf import settings
import tempfile, os
import base64
from django.urls import reverse
import locale
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core import serializers
from collections import defaultdict
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from collections import OrderedDict
from decimal import Decimal
from django.core.mail import send_mail

# Create your views here.

def generar_numero_nota_bonificacion():
    ultimo = NumeroNotaBonificacion.objects.order_by("-id").first()
    if not ultimo:
        nuevo_num = 1
    else:
        # tomar la parte numérica del último número
        ultimo_num = int(ultimo.numero.replace("LV-B", ""))
        nuevo_num = ultimo_num + 1

    return f"LV-B{nuevo_num:07d}"

def generar_numero_nota_canje():
    ultimo = NumeroNotaCanje.objects.order_by("-id").first()
    if not ultimo:
        nuevo_num = 1
    else:
        # tomar la parte numérica del último número
        ultimo_num = int(ultimo.numero.replace("LV-C", ""))
        nuevo_num = ultimo_num + 1

    return f"LV-C{nuevo_num:07d}"

def generar_numero_nota_agencia():
    ultimo = NumeroNotaAgencia.objects.order_by("-id").first()
    if not ultimo:
        nuevo_num = 1
    else:
        # tomar la parte numérica del último número
        ultimo_num = int(ultimo.numero.replace("LV-A", ""))
        nuevo_num = ultimo_num + 1

    return f"LV-A{nuevo_num:07d}"

def generar_numero_nota_directo():
    ultimo = NumeroNotaDirecto.objects.order_by("-id").first()
    if not ultimo:
        nuevo_num = 1
    else:
        # tomar la parte numérica del último número
        ultimo_num = int(ultimo.numero.replace("LV-D", ""))
        nuevo_num = ultimo_num + 1

    return f"LV-D{nuevo_num:07d}"

def generar_numero_nota_programatica():
    ultimo = NumeroNotaProgramatica.objects.order_by("-id").first()
    if not ultimo:
        nuevo_num = 1
    else:
        # tomar la parte numérica del último número
        ultimo_num = int(ultimo.numero.replace("LV-P", ""))
        nuevo_num = ultimo_num + 1

    return f"LV-P{nuevo_num:07d}"

@login_required
@transaction.atomic
def nuevo_pedido(request):
    abrir_pdf = request.GET.get('abrir_pdf')
    editar_id = request.GET.get('editar_id')  # <<--- NUEVO
    id_agente = request.user.id
    fecha = date.today()

    listado_tipo_venta = TipoVenta.objects.all()
    listado_tipo_pago = TipoFormaPago.objects.all()
    listado_dias = DiasCredito.objects.all()
    listado_ubicaciones = ubicacion.objects.filter(tipo_id=1).order_by('codigo')
    listado_clientes = clientes.objects.filter(
        Q(usuario_id=id_agente) | Q(usuario_id__isnull=True)
    ).order_by('nombre_comercial')

    ubicaciones_digitales = (
        ubicacion.objects.filter(tipo_id=2).prefetch_related("slots")
    )
    ubicaciones_con_slots = {
        u: u.slots.filter(activo=True).order_by("numero_slot")
        for u in ubicaciones_digitales
        if u.slots.filter(activo=True).exists()
    }

    # ======================================================
    # MODO EDICIÓN — MARCA NOTA ORIGINAL Y CARGA SOLO DATOS COMUNES
    # ======================================================
    nota_json = None
    if editar_id:
        try:
            nota = NotaPedido.objects.get(id=editar_id)

            # Marcar nota original como EDITADA
            nota.estado_id = 8  # Estado "EDITADA"
            nota.save()

            # Solo datos comunes para precargar
            nota_dict = {
                "cliente_id": nota.cliente_id,
                "cliente_nombre": nota.cliente.nombre_comercial if nota.cliente else "",
                "tipo_venta_id": nota.tipo_venta_id,
                "tipo_pago_id": nota.tipo_pago_id,
                "dias_credito_id": nota.dias_credito_id,
                "anunciante": nota.anunciante,
                "razon_social_id": nota.razon_social_id,
                "ruc": nota.ruc,
                "contacto": nota.contacto,
                "telefono": nota.telefono,
                "direccion": nota.direccion,
                "detalle_facturacion": nota.detalle_facturacion,
                "correo":nota.razon_social.correo
            }

            nota_json = json.dumps(nota_dict)
            print(nota_json)

        except NotaPedido.DoesNotExist:
            pass

    if request.method == 'POST':
        # 🧩 Campos directos del formulario
        fecha_nota = request.POST.get("fecha")
        tipo_venta_id = request.POST.get("tipo_venta")
        tipo_pago_id = request.POST.get("tipo_pago")
        dias_credito_id = request.POST.get("dias")
        cliente_id = request.POST.get("cliente")
        anunciante = request.POST.get("anunciante")
        tarifa_estatica = request.POST.get("tarifa_neg") or 0
        tarifa_digital = request.POST.get("tarifa_neg_dig") or 0
        igv = request.POST.get("igv") or 0
        total = request.POST.get("total") or 0
        razon_social_id = request.POST.get("razon_social")
        ruc = request.POST.get("ruc")
        contacto = request.POST.get("contacto")
        telefono = request.POST.get("telefono")
        direccion = request.POST.get("direccion")
        detalle_ubicaciones = request.POST.get("detalle_ubicaciones")
        detalle_facturacion = request.POST.get("detalle_facturacion")
        facturado = request.POST.get("facturado")

        # 📦 Procesar ubicaciones FIJAS
        ubicaciones = request.POST.getlist('ubicaciones_seleccionadas') or []

        # 📦 Procesar ubicaciones DIGITALES
        ocupaciones_json = request.POST.get('slot_ocupaciones_json', '[]')
        try:
            ocupaciones = json.loads(ocupaciones_json)
        except json.JSONDecodeError:
            ocupaciones = []

        try:
            # 1️⃣ Generar número de pedido
            tipo_numero_pedido = int(tipo_venta_id)
            if tipo_numero_pedido == 1:
                numero_nota = generar_numero_nota_directo()
            elif tipo_numero_pedido == 2: 
                numero_nota = generar_numero_nota_canje()
            elif tipo_numero_pedido == 3:
                numero_nota = generar_numero_nota_programatica()
            elif tipo_numero_pedido == 4:
                numero_nota = generar_numero_nota_bonificacion()
            elif tipo_numero_pedido == 5:
                numero_nota = generar_numero_nota_agencia()
            else:
                numero_nota = "SIN_NUMERO"

            print("DEBUG valores:",request.POST.get('tarifa_neg_dig'), request.POST.get('tarifa_neg'), request.POST.get('igv'), request.POST.get('total'))
            print("📤 JSON recibido:", request.POST.get('slot_ocupaciones_json'))

            # valida contra la tarifa minima, si es menor cambia esta a 6 y no PDF

            requiere_aprobacion = 0

            if [u for u in ubicaciones if u and str(u).strip()]:
                for n in ubicaciones:
                    ubi_id = ubicacion.objects.filter(id=n).first()
                    t_minima = ubicacion.objects.get(id = n).tarifa_minima 
                    tarifa_mes = Decimal(request.POST.get(f'tarifa_mes_{n}'))

                    if tarifa_mes < t_minima:
                        requiere_aprobacion = 1
                        estado_nota = 6
                        enviar_correo = 1
                        messages.error(request, "⚠️ Esta nota de pedido requiere autorización.")
            
            if ocupaciones:
                for i in ocupaciones:
                    slot_id = int(i.get('slot_id'))
                    slot_name = int(i.get('slot'))
                    ubi_id_s = int(i.get('ubicacion_id'))
                    tarifa_mes = i.get('tarifa_mes')
                    t_minima = SlotDigital.objects.get(ubicacion_id = ubi_id_s, numero_slot = slot_name ).tarifa_minima 
                    
                    if Decimal(tarifa_mes) < t_minima:
                        requiere_aprobacion = 1
                        estado_nota = 6
                        enviar_correo = 1
                        messages.error(request, "⚠️ Esta nota de pedido requiere autorización.")

            if requiere_aprobacion:
                # 2️⃣ Crear la nota
                nota = NotaPedido.objects.create(
                    fecha=fecha_nota or timezone.now(),
                    tipo_venta_id=tipo_venta_id,
                    tipo_pago_id=tipo_pago_id,
                    dias_credito_id=dias_credito_id or 1,
                    cliente_id=cliente_id,
                    anunciante=anunciante,
                    numero_np=numero_nota,
                    tarifa_estatica=tarifa_estatica,
                    tarifa_digital=tarifa_digital,
                    igv=igv,
                    total=total,
                    razon_social_id=razon_social_id,
                    ruc=ruc,
                    contacto=contacto,
                    telefono=telefono,
                    direccion=direccion,
                    detalle_ubicaciones=detalle_ubicaciones,
                    detalle_facturacion=detalle_facturacion,
                    estado_id = estado_nota,
                    usuario=request.user,
                    facturar = facturado
                )

            else:
            # 2️⃣ Crear la nota
                nota = NotaPedido.objects.create(
                    fecha=fecha_nota or timezone.now(),
                    tipo_venta_id=tipo_venta_id,
                    tipo_pago_id=tipo_pago_id,
                    dias_credito_id=dias_credito_id or 1,
                    cliente_id=cliente_id,
                    anunciante=anunciante,
                    numero_np=numero_nota,
                    tarifa_estatica=tarifa_estatica,
                    tarifa_digital=tarifa_digital,
                    igv=igv,
                    total=total,
                    razon_social_id=razon_social_id,
                    ruc=ruc,
                    contacto=contacto,
                    telefono=telefono,
                    direccion=direccion,
                    detalle_ubicaciones=detalle_ubicaciones,
                    detalle_facturacion=detalle_facturacion,
                    usuario=request.user,
                    facturar = facturado
                )

            # 3️⃣ Procesar ubicaciones FIJAS (solo si hay)
            if ubicaciones:
                for ubic_id in ubicaciones:
                    fecha_ini = request.POST.get(f'fecha_inicio_{ubic_id}')
                    fecha_fin = request.POST.get(f'fecha_fin_{ubic_id}')
                    dias_dif = request.POST.get(f'dias_dif_{ubic_id}')
                    tarifa_dia = request.POST.get(f'tarifa_dia_{ubic_id}')
                    tarifa_mes = request.POST.get(f'tarifa_mes_{ubic_id}')
                    total_tarifa = request.POST.get(f'monto_total_{ubic_id}')

                    print (tarifa_dia)
                    print (tarifa_mes)
                    print(total_tarifa)

                    if not (fecha_ini and fecha_fin):
                        continue

                    ubic = ubicacion.objects.filter(id=ubic_id).first()
                    if not ubic:
                        continue

                    DetalleUbicacion.objects.create(
                        nota=nota,
                        ubicacion=ubic,
                        fecha_inicio=fecha_ini,
                        fecha_fin=fecha_fin,
                        dias=dias_dif or 0,
                        tarifa_dia = tarifa_dia or 0,
                        tarifa_mes = tarifa_mes or 0,
                        total_tarifa_ubi = total_tarifa or 0
                    )

            # 4️⃣ Procesar ubicaciones DIGITALES (solo si hay)
            if ocupaciones:
                for u in ocupaciones:
                    try:
                        slot_id = u.get('slot_id')
                        fecha_inicio = u.get('fecha_inicio')
                        fecha_fin = u.get('fecha_fin')
                        tarifa_del_dia = u.get('tarifa_dia')
                        tarifa_mes = u.get('tarifa_mes')
                        tarifa_total = u.get('monto_total')

                        if not (slot_id and fecha_inicio and fecha_fin):
                            continue

                        slot = SlotDigital.objects.get(id=slot_id)
                        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

                        dias = (fecha_fin - fecha_inicio).days + 1

                        # 🚫 No verificamos conflictos, para evitar que falle el guardado completo
                        ReservaSlot.objects.create(
                            slot=slot,
                            nota_pedido=nota,
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin,
                            dias=dias,
                            tarifa_dia = tarifa_del_dia,
                            tarifa_mes = tarifa_mes,
                            total_tarifa_slot = tarifa_total,
                            estado_id=2
                        )

                    except Exception as e:
                        print(f"❌ Error procesando slot digital: {e}")

            if not requiere_aprobacion:
            # 5️⃣ Generar PDF siempre, aunque solo haya uno de los dos tipos
                pdf_url = request.build_absolute_uri(reverse('generar_pdf_nota', args=[nota.id]))
            
            if tipo_numero_pedido == 1:
                nota_pdf = NumeroNotaDirecto.objects.create(
                pedido=nota,
                numero=numero_nota,
                )
            if tipo_numero_pedido == 2:
                nota_pdf = NumeroNotaCanje.objects.create(
                pedido=nota,
                numero=numero_nota,
                )
            if tipo_numero_pedido == 3:
                nota_pdf = NumeroNotaProgramatica.objects.create(
                pedido=nota,
                numero=numero_nota,
                )
            if tipo_numero_pedido == 4:
                nota_pdf = NumeroNotaBonificacion.objects.create(
                pedido=nota,
                numero=numero_nota,
                )
            if tipo_numero_pedido == 5:
                nota_pdf = NumeroNotaAgencia.objects.create(
                pedido=nota,
                numero=numero_nota,
                )
            
            # VALIDAR SI ES CANJE NO SE GUARDE MAS DE 6 VECES PARA UNA MISMA UBICACION


            if not requiere_aprobacion:
                return redirect(f"{reverse('crear_pedido')}?abrir_pdf={pdf_url}")

            if enviar_correo:
                asunto = "⚠️ Verificación requerida: Nota de pedido inferior al monto minimo establecido" 
                link = "https://limavisual.onrender.com"
                mensaje = f"""
Estimado/a,

Se ha registrado una nota de pedido inferior al monto mínimo establecido para negociación.
Por tal motivo, se requiere su verificación y aprobación o rechazo antes de proceder con la gestión correspondiente.

Detalles del pedido:
- Número de nota: {numero_nota}
- Solicitante = {request.user.first_name} {request.user.last_name}"

Por favor, revise la información y realice la acción correspondiente en el sistema ({link}) (Aprobar / Rechazar) a la brevedad posible para no afectar el flujo operativo.

Gracias por su atención.

Atentamente,
Sistema de Gestión de Pedidos"""
                 
                send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        ['administracion@limavisual.pe','a.perales@limavisual.pe'],
        fail_silently=False,
    )
            
        except Exception as e:
            print(f"⚠️ Error en nuevo_pedido: {e}")
            return render(request, 'nuevo_pedido.html', {
                'listado_tipo_venta': listado_tipo_venta,
                'listado_tipo_pago': listado_tipo_pago,
                'listado_dias': listado_dias,
                'fecha': fecha,
                'listado_ubicaciones': listado_ubicaciones,
                'listado_clientes': listado_clientes,
                'ubicaciones_con_slots': ubicaciones_con_slots,
            })

    # Render normal (GET)
    return render(request, 'nuevo_pedido.html', {
        'listado_tipo_venta': listado_tipo_venta,
        'listado_tipo_pago': listado_tipo_pago,
        'listado_dias': listado_dias,
        'fecha': fecha,
        'listado_ubicaciones': listado_ubicaciones,
        'listado_clientes': listado_clientes,
        'ubicaciones_con_slots': ubicaciones_con_slots,
        "abrir_pdf": abrir_pdf,
        "nota_json": nota_json,   # <<-- Importante
    })
@require_GET
def obtener_ocupaciones_fijas(request):
    """
    Devuelve las ocupaciones (DetalleUbicacion) en formato JSON para FullCalendar.
    Permite filtrar por ubicación_id y rango de fechas (start, end).
    """
    qs = DetalleUbicacion.objects.select_related('ubicacion', 'nota', 'nota__tipo_venta')

    # 📌 Filtros
    ubicacion_id = request.GET.get('ubicacion_id')
    if ubicacion_id:
        qs = qs.filter(ubicacion_id=ubicacion_id, estado = 2) #OCUPADAS

    start = request.GET.get('start')
    end = request.GET.get('end')
    if start:
        start_date = parse_date(start)
        if start_date:
            qs = qs.filter(fecha_fin__gte=start_date)
    if end:
        end_date = parse_date(end)
        if end_date:
            qs = qs.filter(fecha_inicio__lte=end_date)

    # 📦 Convertimos cada registro en un evento
    events = []
    for d in qs:
        end_plus_one = d.fecha_fin + timedelta(days=1) if d.fecha_fin else None

        #### ARMAR MAPA DE COLORES SEGUN EL TIPO
        if d.nota.tipo_venta_id == 1:
            color = "#e9150e"  # DIRECTO
        elif d.nota.tipo_venta_id == 2:
            color = "#e95e0e"  # CANJE
        elif d.nota.tipo_venta_id == 3:
            color = "#e9150e"  # PROGRAMATICA
        elif d.nota.tipo_venta_id == 4:
            color = "#e95e0e"  # BONIFICACION
        else:
            color = "#e9150e" # AGENCIA

        events.append({
            "id": d.id,
            "title": f"{d.ubicacion.codigo} — Nota: {d.nota.numero_np} — Tipo: {d.nota.tipo_venta.descripcion}",
            "start": d.fecha_inicio.isoformat(),
            "end": end_plus_one.isoformat() if end_plus_one else d.fecha_fin.isoformat(),
            "color": color,
            "extendedProps": {
                "ubicacion_id": d.ubicacion_id,
                "dias": d.dias,
                "nota_id": d.nota_id,
                "direccion": d.ubicacion.direccion,
                "numero_nota":d.nota.numero_np
            }
        })

    return JsonResponse(events, safe=False)

def calendario_ocupaciones_fijas(request):
    listado_ubicaciones = ubicacion.objects.filter(tipo = 1).order_by('codigo')
    return render(request, 'calendario_fijas.html', {'listado_ubicaciones': listado_ubicaciones})

@require_GET
def obtener_ocupaciones_digitales(request):
    qs = ReservaSlot.objects.select_related('slot__ubicacion', 'nota_pedido', 'nota_pedido__tipo_venta') # OCUPADAS 

    # 📌 Filtros
    ubicacion_id = request.GET.get('ubicacion_id')
    slot_id = request.GET.get('slot_id')

    if ubicacion_id:
        qs = qs.filter(slot__ubicacion_id=ubicacion_id)
    if slot_id:
        qs = qs.filter(slot_id=slot_id)


    start = request.GET.get('start')
    end = request.GET.get('end')


    def parse_date(date_str):
        """Convierte 2025-09-28T00:00:00-05:00 → 2025-09-28"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except Exception:
            return None

    start_date = parse_date(start)
    end_date = parse_date(end)

    if start_date:
        qs = qs.filter(fecha_fin__gte=start_date)
    if end_date:
        qs = qs.filter(fecha_inicio__lte=end_date)

    # 📦 Convertir a eventos
    events = []
    for r in qs:
        end_plus_one = r.fecha_fin + timedelta(days=1)
        #### ARMAR MAPA DE COLORES SEGUN EL TIPO
        if r.nota_pedido.tipo_venta_id == 1:
            color = "#e9150e"  # DIRECTO
        elif r.nota_pedido.tipo_venta_id == 2:
            color = "#e95e0e"  # CANJE
        elif r.nota_pedido.tipo_venta_id == 3:
            color = "#e9150e"  # PROGRAMATICA
        elif r.nota_pedido.tipo_venta_id == 4:
            color = "#e95e0e"  # BONIFICACION
        else:
            color = "#e9150e" # AGENCIA 

        events.append({
            "id": r.id,
            "title": f"{r.slot.ubicacion.codigo} — Slot {r.slot.numero_slot} — {r.nota_pedido.numero_np}",
            "start": r.fecha_inicio.isoformat(),
            "end": end_plus_one.isoformat(),
            "color": color,
            "classNames": ["evento-reservado" if r.estado.descripcion == "OCUPADO" else "OCUPADO"],
            "extendedProps": {
                "ubicacion": r.slot.ubicacion.codigo,
                "slot": r.slot.numero_slot,
                "estado": r.estado.descripcion,
                "nota": r.nota_pedido_id
            }
        }) 

    return JsonResponse(events, safe=False)

def calendario_ocupaciones_digitales(request):
    ubicaciones = ubicacion.objects.filter(tipo = 2).order_by('codigo')
    slots = SlotDigital.objects.select_related('ubicacion').all().order_by('ubicacion', 'numero_slot')
    return render(request, 'calendario_digitales.html', {'slots': slots,'ubicaciones': ubicaciones})

def calendario_ocupaciones_digitales_canje(request):
    ubicaciones = ubicacion.objects.filter(tipo = 2).order_by('codigo')
    slots = (
    SlotDigital.objects
    .select_related('ubicacion')
    .filter(es_canje=True)
    .order_by('ubicacion', 'numero_slot')
)
    return render(request, 'calendario_canjes.html', {'slots': slots,'ubicaciones': ubicaciones})


def generar_pdf_nota(request, nota_id):
    # traer el objeto nota y detalles (ajusta imports según tus modelos)
    from pedidos.models import NotaPedido, DetalleUbicacion
    from ubicaciones.models import ReservaSlot

    nota = NotaPedido.objects.select_related('cliente', 'estado').get(id=nota_id)
    detalles_fijas = DetalleUbicacion.objects.filter(nota=nota).select_related('ubicacion')
    reservas_digitales = ReservaSlot.objects.filter(nota_pedido=nota).select_related('slot__ubicacion', 'estado')

    nombre_cliente_pdf = nota.cliente.nombre_comercial
    correo_admin_pdf = nota.razon_social.correo
    correo_contac_pdf = nota.cliente.correo_contacto
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')
    now = datetime.now()
    mes_letra = now.strftime("%B")

    # preparar datos sencillos para el template (evitar pasar objetos no serializables)
    reservas_list = []
    for r in reservas_digitales:
        reservas_list.append({
            'slot': r.slot,
            'fecha_inicio': r.fecha_inicio,
            'fecha_fin': r.fecha_fin,
            'dias': r.dias,
            'estado_nombre': getattr(r.estado, 'nombre', str(r.estado_id)),
            'tarifa_dia':r.tarifa_dia,
            'tarifa_mes':r.tarifa_mes,
            'total_tarifa_digital':r.total_tarifa_slot
        })

    logo_path = os.path.join(settings.BASE_DIR, "lima_visual", "static", "logo.png")
    logo_base64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    
    total_estaticas = sum([d.total_tarifa_ubi for d in detalles_fijas])
    total_digitales = sum([m.total_tarifa_slot for m in reservas_digitales])

    subtotal = total_estaticas + total_digitales

    context = {
        'nota': nota,
        'detalles_fijas': detalles_fijas,
        'reservas_digitales': reservas_list,
        'empresa_nombre': 'LIMA LED SAC',
        'empresa_direccion': 'CAL.TOMAS RAMSEY NRO. 751 URB. SAN FELIPE',
        'empresa_telefono': '958522150',
        'empresa_ruc': '20600801831',
        'logo_url': logo_base64,
        'now': datetime.now(),
        'usuario': request.user,
        'total_tarifa_estaticas':total_estaticas,
        'total_tarifa_digital':total_digitales,
        'subtotal':subtotal,
        'correo_admin':correo_admin_pdf,
        'correo_contacto':correo_contac_pdf
    }

    # renderizar html
    html = render_to_string('pdf_nota.html', context)

    # generar pdf
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.BytesIO(html.encode('UTF-8')), dest=result, encoding='UTF-8')
    if pdf.err:
        return HttpResponse('Hubo un error al generar el PDF', status=500, content_type='text/plain')

    # retorno
    result.seek(0)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=NP_{nota.numero_np}-{nombre_cliente_pdf}-{mes_letra}.pdf'
    return response


def verificar_disponibilidad(request):
    ubicacion_id = request.GET.get('ubicacion_id')
    slot_id = request.GET.get('slot_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except:
        return JsonResponse({'ok': False, 'error': 'Fechas inválidas'}, status=400)

    # Fijas
    if ubicacion_id:
        conflicto = DetalleUbicacion.objects.filter(
            ubicacion_id=ubicacion_id,
            fecha_inicio__lte=ff,
            fecha_fin__gte=fi
        ).exists()
        return JsonResponse({
            'ok': not conflicto,
            'mensaje': '✅ Disponible' if not conflicto else '⚠️ Esta ubicación ya está reservada en ese rango'
        })

    # Digitales
    if slot_id:
        conflicto = ReservaSlot.objects.filter(
            slot_id=slot_id,
            fecha_inicio__lte=ff,
            fecha_fin__gte=fi
        ).exists()
        return JsonResponse({
            'ok': not conflicto,
            'mensaje': '✅ Disponible' if not conflicto else '⚠️ Este slot ya está reservado en ese rango'
        })

    return JsonResponse({'ok': False, 'error': 'Faltan parámetros'}, status=400)


def verificar_disponibilidad_digital(request):
    ubicacion_id = request.GET.get('ubicacion_id')
    slot_id = request.GET.get('slot_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if not (ubicacion_id and slot_id and fecha_inicio and fecha_fin):
        return JsonResponse({'ok': False, 'mensaje': 'Faltan parámetros'}, status=400)

    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'ok': False, 'mensaje': 'Fechas inválidas'}, status=400)

    # 🔍 Buscar reservas que se superpongan en ese slot de esa ubicación

    qs = SlotDigital.objects.filter(ubicacion_id = ubicacion_id, numero_slot = slot_id).first()
    print("DEBUG SlotDigital ----------------")
    print("ubicacion_id:", ubicacion_id)
    print("slot_id:", slot_id)
    print("qs:", qs)
    if qs.es_canje == False:
        conflicto = ReservaSlot.objects.filter(
            slot__ubicacion_id=ubicacion_id,
            slot_id=slot_id,
            fecha_inicio__lte=ff,
            fecha_fin__gte=fi,
            estado_id = 2  
        ).exists()

        return JsonResponse({
            'ok': not conflicto,
            'mensaje': '✅ Disponible' if not conflicto else '⚠️ Ya reservado en ese rango.'
        })
    else:
        ### CUENTA CUANTAS HAY EN ESE MES SI HAY MAS DE 6 NO DEJA PASAR
        count_canje = (
                ReservaSlot.objects
                .annotate(
                    mes_inicio=ExtractMonth('fecha_inicio'),
                    anio_inicio=ExtractYear('fecha_inicio'),
                    mes_fin=ExtractMonth('fecha_fin'),
                    anio_fin=ExtractYear('fecha_fin')
                )
                .filter(
                    slot__ubicacion_id=ubicacion_id,
                    slot_id=slot_id,
                    estado_id=2,
                    mes_inicio=fi.month,
                    anio_inicio=fi.year,
                    mes_fin=ff.month,
                    anio_fin=ff.year
                )
                .count()
            )
        if count_canje >= 12:
            return JsonResponse({
            'mensaje': '⚠️ Maximo de canjes alcanzado en el mes seleccionado.'
            })
        
        return JsonResponse({
            'ok':'ok',
            'mensaje': '✅ Slot de canje disponible.'
        })

def gestion_notas(request):
    usuario=request.user
    if usuario.is_superuser:
        listado_notas = NotaPedido.objects.all()
        listado_estado = EstadoNota.objects.all().order_by('descripcion')
        return render(request, "mis_np.html", {'listado_notas':listado_notas, 'listado_estado':listado_estado})
    else:
        usuario=request.user
        listado_notas = NotaPedido.objects.filter(usuario_id = usuario)
        listado_estado = EstadoNota.objects.all().order_by('descripcion')
        return render(request, "mis_np.html", {'listado_notas':listado_notas, 'listado_estado':listado_estado})

def cambiar_estado_nota(request):
    if request.method == "POST":
        nota_id = request.POST.get("nota_id")
        nuevo_estado = request.POST.get("nuevo_estado")
        motivo_anulacion = request.POST.get("motivo_anulacion")
        nota = get_object_or_404(NotaPedido, id=nota_id)
        if nuevo_estado:

            # ACTUALIZAR EL ESTADO DE LA NOTA ###
            nota.estado_id = nuevo_estado
            nota.motivo_rechazo_anulacion = motivo_anulacion
            nota.save()

            ### SI ES ANULADA - COMPLETADA - RECHAZADA LIBERAR LAS UBI Y SLOT ####
            if int(nuevo_estado) in [2, 4, 5]:
            ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE ESTATICAS
                DetalleUbicacion.objects.filter(nota_id=nota_id).update(estado_id=1)
            ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE DIGITALES
                ReservaSlot.objects.filter(nota_pedido_id = nota_id).update(estado_id = 1)

            
            messages.success(request, "El estado de la nota se actualizó correctamente.")
    return redirect('gestion_notas')  # ajusta según tu vista/listado

def filtrar_notas(request):
    numero = request.GET.get('numero', '')
    anunciante = request.GET.get('anunciante', '')
    marca = request.GET.get('marca', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    estado = request.GET.get('estado', '')
    usuario=request.user

    notas = NotaPedido.objects.filter(usuario_id = usuario)

    if numero:
        notas = notas.filter(numero_np__icontains=numero)
    if anunciante:
        notas = notas.filter(cliente__nombre_comercial__icontains=anunciante)
    if marca:
        notas = notas.filter(anunciante__icontains=marca)
    if desde:
        notas = notas.filter(fecha__gte=desde)
    if hasta:
        notas = notas.filter(fecha__lte=hasta)
    if estado:
        notas = notas.filter(estado_id=estado)

    data = list(notas.values('id', 'numero_np', 'fecha', 'cliente__nombre_comercial', 'anunciante', 'estado__descripcion', 'estado', 'usuario__username'))
    return JsonResponse(data, safe=False)

def filtrar_notas_n_autoriza(request):
    numero = request.GET.get('numero', '')
    anunciante = request.GET.get('anunciante', '')
    marca = request.GET.get('marca', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    estado = request.GET.get('estado', '')
    usuario=request.user

    notas = NotaPedido.objects.filter(estado_id = 6)

    if numero:
        notas = notas.filter(numero_np__icontains=numero)
    if anunciante:
        notas = notas.filter(cliente__nombre_comercial__icontains=anunciante)
    if marca:
        notas = notas.filter(anunciante__icontains=marca)
    if desde:
        notas = notas.filter(fecha__gte=desde)
    if hasta:
        notas = notas.filter(fecha__lte=hasta)

    data = list(notas.values('id', 'numero_np', 'fecha', 'cliente__nombre_comercial', 'anunciante', 'estado__descripcion', 'estado', 'usuario__first_name', 'usuario__last_name'))
    return JsonResponse(data, safe=False)


def ver_dashboard(request):
    return render(request, 'dash.html')

def dashboard_data(request):
    """Devuelve todos los KPIs y datos de gráficos del dashboard (JSON)"""
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    notas = NotaPedido.objects.all()
    if fecha_inicio and fecha_fin:
        notas = notas.filter(fecha__range=[fecha_inicio, fecha_fin])

    total_notas = notas.count()
    total_facturado = notas.aggregate(total=Sum("total"))["total"] or 0
    promedio_factura = notas.aggregate(avg=Avg("total"))["avg"] or 0
    clientes_activos = notas.values("cliente").distinct().count()
    espacios_ocupados = DetalleUbicacion.objects.filter(nota__in=notas).count()
    total_dias_contratados = (
        DetalleUbicacion.objects.filter(nota__in=notas).aggregate(Sum("dias"))["dias__sum"]
        or 0
    )

    ingresos_mensuales = (
        notas.annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(total_mes=Sum("total"))
        .order_by("mes")
    )
    notas_por_estado = (
        notas.values("estado__descripcion")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")
    )
    top_clientes = (
        notas.values("cliente__razon_social")
        .annotate(total_cliente=Sum("total"))
        .order_by("-total_cliente")[:5]
    )
    ubicaciones_populares = (
        DetalleUbicacion.objects.filter(nota__in=notas)
        .values("ubicacion__codigo")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:5]
    )
    facturacion_por_usuario = (
        notas.values("usuario__username")
        .annotate(total_vendedor=Sum("total"))
        .order_by("-total_vendedor")
    )

    data = {
        "kpis": {
            "total_notas": total_notas,
            "total_facturado": float(total_facturado),
            "promedio_factura": float(promedio_factura),
            "clientes_activos": clientes_activos,
            "espacios_ocupados": espacios_ocupados,
            "total_dias_contratados": total_dias_contratados,
        },
        "graficos": {
            "ingresos_mensuales": list(ingresos_mensuales),
            "notas_por_estado": list(notas_por_estado),
            "top_clientes": list(top_clientes),
            "ubicaciones_populares": list(ubicaciones_populares),
            "facturacion_por_usuario": list(facturacion_por_usuario),
        },
    }
    return JsonResponse(data)


def dashboard(request):
    today = date.today()

    # --- Totales generales ---
    total_notas = NotaPedido.objects.count()
    total_negociado = NotaPedido.objects.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    monto_aprobadas = NotaPedido.objects.filter(estado = 1).aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    monto_anuladas = NotaPedido.objects.filter(estado = 2).aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    total_clientes = clientes.objects.count()

    # --- Distribución de estados ---
    total_aprobadas = NotaPedido.objects.filter(estado = 3).count()
    total_pendientes = NotaPedido.objects.filter(estado = 1).count()
    total_anuladas = NotaPedido.objects.filter(estado = 2).count()

    estado_dist = {
        'Aprobadas': total_aprobadas,
        'Pendientes': total_pendientes,
        'Anuladas': total_anuladas
    }

    # --- IGV y totales ---
    igv_total = total_negociado * Decimal('0.18')
    total_con_igv = total_negociado * Decimal('1.18')

    # --- Ingresos mensuales últimos 12 meses ---
    meses = OrderedDict()
    for i in range(12):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + ((today.month - i - 1) // 12)
        meses[f"{y}-{m:02d}"] = Decimal('0.00')

    registros = NotaPedido.objects.annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total')).order_by('mes')
    for r in registros:
        key = f"{r['mes'].year}-{r['mes'].month:02d}"
        if key in meses:
            meses[key] = r['total'] or Decimal('0.00')

    chart_labels = list(meses.keys())
    chart_values = [float(v) for v in meses.values()]

    # --- Ocupación ---
    total_ubicaciones = ubicacion.objects.count()
    ocupadas = ubicacion.objects.filter(activa=True).count() if hasattr(ubicacion, 'activa') else 0
    porcentaje_ocupacion = round((ocupadas / total_ubicaciones * 100), 2) if total_ubicaciones else 0

    # --- Top rankings ---
    top_clientes = list(
        NotaPedido.objects.values('cliente__nombre_comercial')
        .annotate(total=Sum('total'))
        .order_by('-total')[:5]
    )
    # top_ubicaciones = list(
    #     ubicacion.objects.annotate(cnt=Count('notapedido')).values('codigo', 'cnt').order_by('-cnt')[:5]
    # )

    # --- KPI comerciales adicionales ---
    tasa_aprobacion = round((total_aprobadas / total_notas * 100), 2) if total_notas else 0
    notas_pendientes = total_pendientes
    notas_anuladas = total_anuladas

    context = {
        'total_notas': total_notas,
        'total_negociado': total_negociado,
        'monto_aprobadas': monto_aprobadas,
        'monto_anuladas': monto_anuladas,
        'total_clientes': total_clientes,
        'igv_total': igv_total,
        'total_con_igv': total_con_igv,
        'porcentaje_ocupacion': porcentaje_ocupacion,
        'tasa_aprobacion': tasa_aprobacion,
        'estado_dist': estado_dist,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'top_clientes': top_clientes,
        # 'top_ubicaciones': top_ubicaciones,
        'notas_pendientes': notas_pendientes,
        'notas_anuladas': notas_anuladas
    }

    return render(request, 'dashboard.html', context)

def aprobar_negar_np(request):

    usuario=request.user
    listado_notas = NotaPedido.objects.filter(estado_id = 6)
    listado_estado = EstadoNota.objects.all().order_by('descripcion')
    return render(request, "aprobar_negar_np.html", {'listado_notas':listado_notas, 'listado_estado':listado_estado})

def detalle_aprobar_negar_np(request, nota_id):

    nota = NotaPedido.objects.select_related('cliente', 'estado').get(id=nota_id)
    detalles_fijas = DetalleUbicacion.objects.filter(nota=nota).select_related('ubicacion')
    reservas_digitales = ReservaSlot.objects.filter(nota_pedido=nota).select_related('slot__ubicacion', 'estado')

    nombre_cliente_pdf = nota.cliente.nombre_comercial
    correo_admin_pdf = nota.razon_social.correo
    correo_contac_pdf = nota.cliente.correo_contacto
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')
    now = datetime.now()
    mes_letra = now.strftime("%B")

    # CALCULAR EL DESVIO CON RELACION A LA TARIFA MINIMA

    detalles_fijas_list = []

    for n in detalles_fijas:
        desviacion_porcentual = 0
        cumplimiento_tarifario = 100
        pinta = 0
        if n.tarifa_mes < n.ubicacion.tarifa_minima:
            desviacion_porcentual = round(((n.tarifa_mes - n.ubicacion.tarifa_minima)/ n.ubicacion.tarifa_minima)*100,2)
            cumplimiento_tarifario = round(((n.tarifa_mes / n.ubicacion.tarifa_minima))*100,2)
            pinta = 1
        
        detalles_fijas_list.append({
        "codigo": n.ubicacion.codigo,
        "direccion": n.ubicacion.direccion,
        "fecha_inicio": n.fecha_inicio,
        "fecha_fin": n.fecha_fin,
        "dias":n.dias,
        "tarifa_mes": n.tarifa_mes,
        "tarifa_dia": n.tarifa_dia,
        "total_tarifa": n.total_tarifa_ubi,
        "tarifa_minima": n.ubicacion.tarifa_minima,
        "desviacion":desviacion_porcentual,
        'cumplimiento':cumplimiento_tarifario,
        'pinta':pinta
    })




    # preparar datos sencillos para el template (evitar pasar objetos no serializables)
    reservas_list = []
    for r in reservas_digitales:
        desviacion_porcentual_slot = 0
        cumplimiento_tarifario_slot = 100
        pinta_slot = 0
        
        if r.tarifa_mes < r.slot.tarifa_minima:
            desviacion_porcentual_slot = round(((r.tarifa_mes - r.slot.tarifa_minima)/ r.slot.tarifa_minima)*100,2)
            cumplimiento_tarifario_slot = round(((r.tarifa_mes / r.slot.tarifa_minima))*100,2)
            pinta_slot = 1
                
        reservas_list.append({
            'slot': r.slot,
            'fecha_inicio': r.fecha_inicio,
            'fecha_fin': r.fecha_fin,
            'dias': r.dias,
            'estado_nombre': getattr(r.estado, 'nombre', str(r.estado_id)),
            'tarifa_dia':r.tarifa_dia,
            'tarifa_mes':r.tarifa_mes,
            'total_tarifa_digital':r.total_tarifa_slot,
            'desviacion_slot':desviacion_porcentual_slot,
            'cumplimiento_slot':cumplimiento_tarifario_slot,
            'pinta_slot':pinta_slot,
            'tarifa_minima':r.slot.tarifa_minima
        })

    logo_path = os.path.join(settings.BASE_DIR, "lima_visual", "static", "logo.png")
    logo_base64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    
    total_estaticas = sum([d.total_tarifa_ubi for d in detalles_fijas])
    total_digitales = sum([m.total_tarifa_slot for m in reservas_digitales])


    subtotal = total_estaticas + total_digitales

    context = {
        'nota': nota,
        'detalles_fijas': detalles_fijas_list,
        'reservas_digitales': reservas_list,
        'empresa_nombre': 'LIMA LED SAC',
        'empresa_direccion': 'Cal. Tomas Ramsey Nro. 751',
        'empresa_telefono': '958522150',
        'empresa_ruc': '20600801831',
        'logo_url': logo_base64,
        'now': datetime.now(),
        'usuario': request.user,
        'total_tarifa_estaticas':total_estaticas,
        'total_tarifa_digital':total_digitales,
        'subtotal':subtotal,
        'correo_admin':correo_admin_pdf,
        'correo_contacto':correo_contac_pdf
    }
    return render(request, 'detalle_aprobar_negar_np.html', context)

def aprobar_nota(request, nota_id):

    nota = NotaPedido.objects.get(id = nota_id)
    nota.estado_id = 1
    nota.save()

    # ENVIAR EL CORREO DE VUELTA
    correo = nota.usuario.email
    asunto = "✅ Nota de Pedido aprobada." 
    link = "https://limavisual.onrender.com"
    mensaje = f"""

Estimado/a,

Su nota de pedido ha sido aprobada.

Detalles del pedido:
- Número de nota: {nota.numero_np}
- Anunciante = {nota.cliente.nombre_comercial} 

Gracias por su atención.

Atentamente,
Sistema de Gestión de Pedidos"""
                 
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [f'{correo}'],
        fail_silently=False,
    )

    return redirect('autorizar')

def rechazar_nota(request, nota_id):

    nota = NotaPedido.objects.get(id = nota_id)
    nota.estado_id = 4
    nota.save()

    # LIBERAR LAS UBICACIONES

    ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE ESTATICAS
    DetalleUbicacion.objects.filter(nota_id=nota_id).update(estado_id=1)
    ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE DIGITALES
    ReservaSlot.objects.filter(nota_pedido_id = nota_id).update(estado_id = 1)

    # ENVIAR EL CORREO DE VUELTA
    correo = nota.usuario.email
    asunto = "❌ Nota de Pedido rechazada." 
    link = "https://limavisual.onrender.com"
    mensaje = f"""

Estimado/a,

Su nota de pedido ha sido rechazada.

Detalles del pedido:
- Número de nota: {nota.numero_np}
- Anunciante = {nota.cliente.nombre_comercial} 

Gracias por su atención.

Atentamente,
Sistema de Gestión de Pedidos"""
                 
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [f'{correo}'],
        fail_silently=False,
    )

    return redirect('autorizar')

