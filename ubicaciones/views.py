from django.shortcuts import render, get_object_or_404, redirect
from parametros.models import TipoVenta
from django.http import JsonResponse
from .models import ubicacion, TipoUbicacion
from django.contrib import messages

# Create your views here.

def crea_ubicacion(request):

    listado_ubicaciones = ubicacion.objects.all().order_by('codigo')
    tipo_ubic = TipoUbicacion.objects.all()

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        referencia = request.POST.get("referencia", "").strip()
        tipo_ubi = request.POST.get("tipo_ubi", "").strip()
        tarifa_fria = request.POST.get("tarifa_fria", "").strip()
        tarifa_minima = request.POST.get("tarifa_minima", "").strip()

        tipo_ubicacion = TipoUbicacion.objects.get(pk = tipo_ubi)

        if ubicacion.objects.filter(codigo__iexact=codigo).exists():
            return JsonResponse({"error": "El código ya existe"}, status=400)
        
        crear_ubicacion = ubicacion.objects.create(
            codigo=codigo,
            direccion=direccion,
            referencia=referencia,
            tipo = tipo_ubicacion,
            tarifa_fria = tarifa_fria,
            tarifa_minima = tarifa_minima
        )

        return render(request, 'crear_ubicacion.html', {'listado_ubicaciones':listado_ubicaciones, 'tipo_ubi':tipo_ubic})
    
    return render(request, 'crear_ubicacion.html', {'listado_ubicaciones':listado_ubicaciones, 'tipo_ubi':tipo_ubic})

def verificar_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    existe = ubicacion.objects.filter(codigo__iexact=codigo).exists()
    return JsonResponse({'existe': existe})


def editar_ubicacion(request, ubicacion_id):
    ubi = get_object_or_404(ubicacion, id=ubicacion_id)
    tipo_ubi = TipoUbicacion.objects.all()

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()

        # ✅ Validar código duplicado (excepto el mismo registro)
        if ubicacion.objects.filter(codigo__iexact=codigo).exclude(id=ubi.id).exists():
            messages.error(request, "⚠️ Este código ya pertenece a otra ubicación.")
            return render(request, 'editar_ubicacion.html', {
                'ubicacion': ubi,
                'tipo_ubi': tipo_ubi
            })

        # 📝 Actualizar campos
        ubi.codigo = codigo
        ubi.direccion = request.POST.get('direccion', '').strip()
        ubi.referencia = request.POST.get('referencia', '').strip()
        tipo_id = request.POST.get('tipo_ubi')
        ubi.tarifa_fria = request.POST.get('tarifa_fria')
        ubi.tarifa_minima = request.POST.get('tarifa_minima')
        if tipo_id:
            ubi.tipo_id = tipo_id

        ubi.save()

        messages.success(request, "✅ Ubicación actualizada correctamente.")
        return redirect('crear_ubicacion')  # vuelve a la lista principal

    return render(request, 'editar_ubicacion.html', {
        'ubicacion': ubi,
        'tipo_ubi': tipo_ubi
    })