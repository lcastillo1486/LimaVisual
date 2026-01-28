from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from user_agents import parse # type: ignore
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from pedidos.models import ControlUsuario, NotaPedido, DetalleUbicacion
from ubicaciones.models import ReservaSlot
from datetime import date, timedelta


def registro(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente. Ahora puedes iniciar sesión.")
            return redirect("inicial")  # tu vista de login
        else:
            messages.error(request, "Corrige los errores para continuar.")
    else:
        form = CustomUserCreationForm()

    return render(request, "registro.html", {"registro_form": form})

def logear(request):

    if request.method == 'POST':
        fecha = date.today()
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data.get("username")
            contra = form.cleaned_data.get("password")
            usuario = authenticate(username=nombre_usuario, password=contra)
            user_agent_string = request.META['HTTP_USER_AGENT']
            user_agent = parse(user_agent_string)

            if usuario is not None:
                login(request, usuario)
                ### crear el registro de control
                if not ControlUsuario.objects.filter(fecha=fecha, name_user = nombre_usuario).exists():
                    ControlUsuario.objects.create(
                        name_user = nombre_usuario,
                        fecha = fecha,
                        primer_login = True
                    )

                    notas_list = NotaPedido.objects.filter(usuario__username = nombre_usuario, estado_id = 1)
                    dias = 2
                    for n in notas_list:
                        fecha_nota = n.fecha
                        if ya_pasaron_dias_habiles(fecha_nota,dias):
                            n.estado_id = 7
                            ## difeenciar 
                            n.save()
                            ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE ESTATICAS
                            DetalleUbicacion.objects.filter(nota_id=n.pk).update(estado_id=1)
                            ### BUSCAR SI EXISTE LA NOTA EN DETALLE DE DIGITALES
                            ReservaSlot.objects.filter(nota_pedido_id = n.pk).update(estado_id = 1)

                return redirect('home/')
            else:
                for msg in form.error_messages:
                    messages.error(request,form.error_messages[msg])
                    return render(request, 'home.html', {"form": form})
        else:
            for msg in form.error_messages:
                    messages.error(request,form.error_messages[msg])
                    return render(request, 'home.html', {"form": form})

    form = AuthenticationForm()
    return render(request, 'home.html', {"form": form})

def inicio(request):
    return render(request, 'inicio.html')

def cerrarSesion(request):
    logout(request)
    return redirect('inicial')

class TailwindPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = "mt-1 block w-full rounded-xl border border-gray-300 p-2 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
        for name, field in self.fields.items():
            field.widget.attrs.update({
                "class": base,
                "placeholder": field.label
            })

class MyPasswordChangeView(PasswordChangeView):
    form_class = TailwindPasswordChangeForm
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("inicial")

def CargarFondo(request):
    return render(request, 'fondo.html')

def sumar_dias_habiles(fecha, dias):
    dias_sumados = 0
    actual = fecha

    while dias_sumados < dias:
        actual += timedelta(days=1)
        if actual.weekday() < 5:  # lunes a viernes
            dias_sumados += 1
    
    return actual

def ya_pasaron_dias_habiles(fecha, dias):
    fecha_limite = sumar_dias_habiles(fecha, dias)
    return date.today() >= fecha_limite