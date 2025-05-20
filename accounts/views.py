from django.shortcuts import render
from django.http import HttpRequest

# Create your views here.

# Definimos una lista reutilizable del menú lateral
sidebarItems = [
    {"name": "Menú Principal", "isTitle": True},
    {
        "name": "Dashboard",
        "url": "/accounts/index/",
        "icon": "grid-fill",
        "key": "dashboard",
        "submenu": []
    },
    {
        "name": "Registro",
        "url": None,
        "icon": "people-fill",
        "key": "users",
        "submenu": [
            {"name": "Registrar Entrada", "url": "/recognition/RegistrarEntrada/"},
            {"name": "Registrar salida", "url": "/recognition/RegistrarSalida/"}
        ]
    }
]

def index(request: HttpRequest):
    return render(request, 'index.html', {
        "title": "Dashboard",
        "web_title": "Mazer",
        "current_url": request.path,
        "sidebarItems": sidebarItems
    })

def user_list(request: HttpRequest):
    return render(request, 'user_list.html', {
        "title": "Lista de usuarios",
        "web_title": "Mazer",
        "current_url": request.path,
        "sidebarItems": sidebarItems
    })