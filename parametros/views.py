from django.shortcuts import render, redirect, get_object_or_404
from .models import TipoFormaPago, TipoVenta, DiasCredito,  clientes
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

# Create your views here.

def CrearParametros(request):
    context = {
        "tipo_ventas": TipoVenta.objects.all(),
        "tipos_forma_pago": TipoFormaPago.objects.all(),
        "dias_creditos": DiasCredito.objects.all(),
        
    }
    return render(request, 'parametros.html', context)

def tipo_venta_guardar(request):
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        if descripcion:
            TipoVenta.objects.create(descripcion=descripcion)
    return redirect("crear_parametros")

def tipo_forma_pago_guardar(request):
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        if descripcion:
            TipoFormaPago.objects.create(descripcion=descripcion)
    return redirect("crear_parametros")

def dias_credito_guardar(request):
    if request.method == "POST":
        dias = request.POST.get("dias")
        if dias:
            DiasCredito.objects.create(dias=dias)
    return redirect("crear_parametros")


def crear_cliente(request):
    listado_ejecutivos = User.objects.all().order_by('first_name')

    if request.method == 'POST':
        clientes.objects.create(
            razon_social=request.POST['razon_social'],
            nombre_comercial=request.POST.get('nombre_comercial', ''),
            ruc=request.POST['ruc'],
            telefono=request.POST['telefono'],
            correo=request.POST.get('correo', ''),
            contacto=request.POST.get('contacto', ''),
            direccion=request.POST.get('direccion', ''),
            correo_contacto = request.POST.get('correo_contacto'),
            usuario_id=request.POST.get('usuario') or None
        )
        messages.success(request, "Cliente creado correctamente.")
        return redirect('crear_cliente')
    
    return render(request, 'clientes.html',{'listado_ejecutivos':listado_ejecutivos})

def verificar_ruc(request):
    ruc = request.GET.get('ruc')
    existe = clientes.objects.filter(ruc=ruc).exists()
    return JsonResponse({'exists': existe})

def listar_clientes(request):
    listado_clientes = clientes.objects.all().order_by('nombre_comercial')

    return render(request,'listado_clientes.html',{'listado_clientes':listado_clientes})

def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(clientes, id=cliente_id)
    usuarios = User.objects.all()

    if request.method == 'POST':
        ruc = request.POST.get('ruc')

        # ✅ Validar que el RUC no pertenezca a otro cliente
        if clientes.objects.filter(ruc=ruc).exclude(id=cliente.id).exists():
            messages.error(request, "⚠️ Este RUC ya pertenece a otro cliente.")
            return render(request, 'editar_cliente.html', {
                'cliente': cliente,
                'usuarios': usuarios
            })

        # 📝 Actualizamos los datos
        cliente.razon_social = request.POST['razon_social']
        cliente.nombre_comercial = request.POST.get('nombre_comercial', '')
        cliente.ruc = ruc
        cliente.telefono = request.POST['telefono']
        cliente.correo = request.POST.get('correo', '')
        cliente.correo_contacto = request.POST.get('correo_contacto', '')
        cliente.contacto = request.POST.get('contacto', '')
        cliente.direccion = request.POST.get('direccion', '')
        cliente.usuario_id = request.POST.get('usuario') or None
        cliente.save()

        messages.success(request, "Cliente actualizado correctamente.")
        return redirect('listar_cliente')

    return render(request, 'editar_cliente.html', {
        'cliente': cliente,
        'usuarios': usuarios
    })

def buscar_empresa(request):
    usuario = request.user.id
    termino = request.GET.get('q', '')
    proveedores = clientes.objects.filter(
        Q(razon_social__icontains=termino)|
        Q(nombre_comercial__icontains=termino) |
        Q(ruc__icontains=termino), usuario_id = usuario
        ).values('id', 'nombre_comercial', 'ruc')[:15]

    return JsonResponse(list(proveedores), safe=False)
