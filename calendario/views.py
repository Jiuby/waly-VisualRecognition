from django.shortcuts import render, redirect
from django.urls import reverse
from calendar import HTMLCalendar
from datetime import date
from .aws_utils import put_evento, get_eventos_mes, get_dynamo_table

# Sidebar configuration
sidebarItems = [
    {"name": "Menú Principal"},
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
            {"name": "Registrar Entrada", "isTitle": True, "url": "/recognition/RegistrarEntrada/"},
            {"name": "Registrar Salida", "url": "/recognition/RegistrarSalida/"}
        ]
    },
    {
        "name": "Administrar usuarios",
        "url": None,
        "icon": "person-badge-fill",
        "key": "users",
        "submenu": [
            {"name": "Registrar usuario", "isTitle": True, "url": "/recognition/RegistrarUsuario/"},
            {"name": "Administrar entradas", "url": "/accounts/usuarios_recientes/"}
        ]
    },
    {
        "name": "Calendario",
        "url": None,
        "icon": "calendar-fill",
        "key": "calendar",
        "submenu": [
            {"name": "Registrar evento", "url": "/calendario/nuevo/"},
            {"name": "Ver calendario", "url": "/calendario/"}
        ]
    }
]

class EventoCalendar(HTMLCalendar):
    """
    Genera un calendario HTML destacando los días con eventos.
    """
    def __init__(self, dias_con_evento):
        super().__init__()
        self.dias = set(dias_con_evento)

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="empty"></td>'
        css = 'event-day' if day in self.dias else ''
        return f'<td class="{css}"><div>{day}</div></td>'


def calendario_view(request, year=None, month=None):
    """
    Vista principal del calendario con pestañas y días señalados.
    """
    hoy = date.today()
    year = int(year) if year else hoy.year
    month = int(month) if month else hoy.month

    eventos = get_eventos_mes(year, month)
    dias_con_evento = [int(ev['fecha'].split('-')[2]) for ev in eventos]
    cal_html = EventoCalendar(dias_con_evento).formatmonth(year, month)

    context = {
        "title": "Calendario",
        "web_title": "Waly",
        "current_url": request.path,
        "sidebarItems": sidebarItems,
        "calendar": cal_html,
        "eventos": eventos,
        "year": year,
        "month": month,
    }
    return render(request, 'calendario/calendar.html', context)


def evento_crear(request):
    """
    Formulario para crear un nuevo evento y guardarlo en DynamoDB.
    """
    if request.method == 'POST':
        item = {
            'fecha': request.POST.get('fecha'),
            'hora_inicio': request.POST.get('hora_inicio'),
            'hora_fin': request.POST.get('hora_fin'),
            'titulo': request.POST.get('titulo'),
            'descripcion': request.POST.get('descripcion'),
        }
        put_evento(item)
        return redirect(reverse('calendario:calendario'))

    context = {
        "title": "Registrar evento",
        "web_title": "Waly",
        "current_url": request.path,
        "sidebarItems": sidebarItems,
    }
    return render(request, 'calendario/event_form.html', context)


def evento_editar(request, fecha, hora_inicio):
    """
    Edita un evento existente identificado por fecha y hora de inicio.
    """
    table = get_dynamo_table()
    key = {'fecha': fecha, 'hora_inicio': hora_inicio}
    item = table.get_item(Key=key).get('Item')
    if not item:
        return redirect(reverse('calendario:calendario'))

    if request.method == 'POST':
        # Actualizar campos
        updated = {
            'fecha': request.POST.get('fecha'),
            'hora_inicio': request.POST.get('hora_inicio'),
            'hora_fin': request.POST.get('hora_fin'),
            'titulo': request.POST.get('titulo'),
            'descripcion': request.POST.get('descripcion'),
        }
        put_evento(updated)
        # Si cambió la clave, borrar la antigua
        if updated['hora_inicio'] != hora_inicio or updated['fecha'] != fecha:
            table.delete_item(Key=key)
        return redirect(reverse('calendario:calendario'))

    # GET: mostrar formulario con datos
    context = {
        "title": "Editar evento",
        "web_title": "Waly",
        "current_url": request.path,
        "sidebarItems": sidebarItems,
        "evento": item,
    }
    return render(request, 'calendario/event_form.html', context)


def evento_borrar(request, fecha, hora_inicio):
    """
    Elimina un evento existente.
    """
    table = get_dynamo_table()
    table.delete_item(Key={'fecha': fecha, 'hora_inicio': hora_inicio})
    return redirect(reverse('calendario:calendario'))
