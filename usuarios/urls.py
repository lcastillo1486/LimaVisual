from django.urls import path
from usuarios import views
from .views import MyPasswordChangeView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('registro/',views.registro),
    path('',views.logear, name='inicial'),
    path('inicio/',views.inicio),
    path('logout/',views.cerrarSesion, name='salir'),
    path('password/change/', MyPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/',auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),name='password_change_done'),
    path('home/',views.CargarFondo, name='cargar_fondo'),
]