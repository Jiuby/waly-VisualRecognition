from django.urls import path
from . import views
from . import api
urlpatterns = [

    path('index/', views.index, name='login'),
    path("auth/", views.auth, name="auth"),
    path('usuarios_recientes/', views.usuarios_recientes, name='usuarios_recientes'),
    path('registrar_entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('login/', views.login_fake, name='login'),
    path("api/entradas-por-rol/", api.api_entradas_por_rol, name="api_entradas_rol"),


    # puedes añadir más rutas aquí
]
