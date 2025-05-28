# calendario/urls.py
from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    # Vista principal del calendario (mes actual por defecto)
    path('', views.calendario_view, name='calendario'),

    # Para navegar a un mes/año concreto: /calendario/2025/05/
    path('<int:year>/<int:month>/', views.calendario_view, name='calendario_mes'),

    # Formulario para crear un nuevo evento
    path('nuevo/', views.evento_crear, name='evento_crear'),
    path('editar/<str:fecha>/<str:hora_inicio>/', views.evento_editar, name='evento_editar'),
    path('borrar/<str:fecha>/<str:hora_inicio>/', views.evento_borrar, name='evento_borrar'),

]
