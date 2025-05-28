from django.shortcuts import render
from django.http import HttpRequest
import boto3
from datetime import datetime, timedelta
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseNotAllowed
import json
import logging
import base64
import pytz
from django.utils import timezone
import uuid
from django.shortcuts import redirect
from boto3.dynamodb.conditions import Attr

# Create your views here.
TZ_COL = pytz.timezone("America/Bogota")   # si ya existe, úsala
tz_bo  = TZ_COL
ts = timezone.localtime(timezone.now()).isoformat()
now_local = timezone.localtime(timezone.now(), tz_bo)

inicio_dia_utc = now_local.replace(
        hour=0, minute=0, second=0, microsecond=0
).astimezone(pytz.UTC)

TZ_COL = pytz.timezone('America/Bogota')
logger = logging.getLogger(__name__)


dynamo = boto3.resource(
    'dynamodb',
    aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
    region_name           = settings.AWS_REGION
)

tabla_usuarios    = dynamo.Table("Usuarios")     # accesos
tabla_incidencias = dynamo.Table("Incidencias")  # unknown / no_face
tabla_eventos     = dynamo.Table("Eventos")      # calendario (inicio, fin)# Definimos una lista reutilizable del menú lateral
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
def _nuevo_evento(payload, estado):
    """Inserta un acceso único (entrada / salida)."""
    ts = timezone.localtime(timezone.now()).isoformat()   # ya −05:00
    event_id = uuid.uuid4().hex               # PK único
    foto_url = payload.get("foto_url")
    tabla_usuarios.put_item(Item={
        "foto_url":       event_id,           # PK (único)
        "photo_url":      foto_url,           # URL real de S3
        "identificacion": payload["identificacion"],
        "timestamp":      ts,
        "status":         estado,             # activo | inactivo
        "nombre":         payload["nombre"],
        "apellido":       payload.get("apellido", ""),
        "rol":            payload.get("rol", "visitante"),
    })
    return ts
def index(request):
    """
    Dashboard principal:
      • Personas activas
      • Accesos hoy
      • Accesos no encontrados hoy
      • Próximo evento + próximos 3 eventos
      • Últimos 10 registros entrada / salida
      • Donut: usuarios activos por rol
    """
    now_local = timezone.localtime(timezone.now(), TZ_COL)

    # 00:00 local → UTC ISO para filtros
    inicio_dia_utc = (
        now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(pytz.UTC)
        .isoformat()
    )

    # 1) Personas activas
    active_count = tabla_usuarios.scan(
        FilterExpression=Attr("status").eq("activo")
    )["Count"]

    # 2) Accesos hoy
    accesses_today = tabla_usuarios.scan(
        FilterExpression=Attr("timestamp").gte(inicio_dia_utc)
    )["Count"]

    # 3) Accesos no encontrados hoy
    unknown_today = tabla_incidencias.scan(
        FilterExpression=Attr("timestamp").gte(inicio_dia_utc)
    )["Count"]

    # 4) Próximos 3 eventos
    resp_evt = tabla_eventos.scan(
        FilterExpression=Attr("fecha").gte(now_local.strftime("%Y-%m-%d"))
    )
    eventos_futuros = []
    for e in resp_evt.get("Items", []):
        try:
            dt_str = f"{e['fecha']} {e.get('hora_inicio','00:00')}"
            evt_dt = TZ_COL.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
            if evt_dt >= now_local:
                eventos_futuros.append({"titulo": e.get("titulo","Sin título"), "dt": evt_dt})
        except:
            continue
    eventos_futuros.sort(key=lambda x: x["dt"])
    prox3 = eventos_futuros[:3]
    next_event_date = prox3[0]["dt"].strftime("%d/%m/%Y") if prox3 else "—"
    next_events = [
        {
            "titulo": ev["titulo"],
            "fecha":  ev["dt"].strftime("%d/%m/%Y"),
            "hora":   ev["dt"].strftime("%H:%M"),
        }
        for ev in prox3
    ]

    # 5) Últimos 10 registros
    items = tabla_usuarios.scan().get("Items", [])
    tz = timezone.get_current_timezone()
    def _ts(it):
        try:
            return timezone.datetime.fromisoformat(it["timestamp"]).astimezone(tz)
        except:
            return timezone.now() - timedelta(days=365)
    items.sort(key=_ts, reverse=True)
    last_logs = [
        {
            "foto":   it.get("photo_url") or it.get("foto_url"),
            "nombre": f"{it.get('nombre','')} {it.get('apellido','')}".strip(),
            "rol":    it.get("rol",""),
            "ts":     _ts(it).strftime("%d/%m %H:%M"),
            "estado": it.get("status","").capitalize(),
        }
        for it in items[:6]
    ]

    # 6) Donut: activos por rol
    resp_activos = tabla_usuarios.scan(
        FilterExpression=Attr("status").eq("activo")
    )["Items"]
    roles_map = {}
    for it in resp_activos:
        r = (it.get("rol") or "visitante").capitalize()
        roles_map[r] = roles_map.get(r, 0) + 1
    roles_labels = list(roles_map.keys())
    roles_series = [roles_map[r] for r in roles_labels]
    roles_json = json.dumps({"labels": roles_labels, "series": roles_series})

    # Render
    return render(request, "index.html", {
        "title":           "Dashboard",
        "web_title":       "Waly",
        "current_url":     request.path,
        "sidebarItems":    sidebarItems,

        "active_count":    active_count,
        "accesses_today":  accesses_today,
        "unknown_today":   unknown_today,
        "next_event_date": next_event_date,
        "next_events":     next_events,
        "last_logs":       last_logs,
        "roles_json":      roles_json,
    })
def auth(request: HttpRequest):
    """
    Vista de autenticación. Solo renderiza la plantilla.
    """
    return render(request, 'auth.html', {
        "title": "Autenticación",
        "web_title": "Waly",
        "current_url": request.path,
        "sidebarItems": sidebarItems
    })

def user_list(request: HttpRequest):
    return render(request, 'user_list.html', {
        "title": "Lista de usuarios",
        "web_title": "Waly",
        "current_url": request.path,
        "sidebarItems": sidebarItems
    })

def usuarios_recientes(request):
    """Lista accesos filtrados por start/end en hora local de Bogotá."""
    start_raw = request.GET.get("start")
    end_raw   = request.GET.get("end")

    # Si no hay filtros: últimas 24 h en hora local
    if not start_raw and not end_raw:
        end_local   = timezone.localtime()                  # ahora en Bogotá
        start_local = end_local - timedelta(hours=24)
    else:
        try:
            start_local = (
                TZ_COL.localize(datetime.fromisoformat(start_raw))
                if start_raw else None
            )
            end_local = (
                TZ_COL.localize(datetime.fromisoformat(end_raw))
                if end_raw   else None
            )
        except ValueError:
            start_local = end_local = None

    # Escanear DynamoDB
    resp = tabla_usuarios.scan()
    usuarios = []
    for item in resp.get("Items", []):
        ts_str   = item.get("timestamp")
        url_img  = item.get("photo_url") or item.get("foto_url")
        if not (ts_str and url_img):
            continue
        try:
            ts_aware = datetime.fromisoformat(ts_str)
        except ValueError:
            continue

        # Convertimos a hora local para comparar y mostrar
        ts_local = timezone.localtime(ts_aware, TZ_COL)

        # Filtrado
        if (start_local and ts_local < start_local) or (end_local and ts_local > end_local):
            continue

        usuarios.append({
            "foto_url":       url_img,
            "identificacion": item.get("identificacion",""),
            "nombre":         item.get("nombre",""),
            "apellido":       item.get("apellido",""),
            "rol":            item.get("rol",""),
            "status":         item.get("status","inactivo"),
            "timestamp":      ts_local.strftime("%Y-%m-%d %H:%M:%S"),
        })

    usuarios.sort(key=lambda x: x["timestamp"], reverse=True)

    return render(request, "UsuariosRecientes.html", {
        "title":         "Usuarios Recientes",
        "web_title":     "Waly",
        "usuarios":      usuarios,
        "sidebarItems":  sidebarItems,
        "current_url":   request.path,
        "default_start": start_raw or start_local.strftime("%Y-%m-%dT%H:%M"),
        "default_end":   end_raw   or end_local.strftime("%Y-%m-%dT%H:%M"),
    })

@csrf_exempt
#define registrar_entrada: GET y POST
# GET: renderiza formulario de entrada.
# POST: inserta un nuevo registro con status='activo' y timestamp UTC.
def registrar_entrada(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    payload = json.loads(request.body)
    ts = _nuevo_evento(payload, "activo")
    return JsonResponse({"status": "ok", "timestamp": ts})

def usuarios_recientes(request):
    """
    Lista accesos filtrados por start/end (hora local Bogotá).

    • Los nuevos registros se guardan con timestamp aware (offset −05:00).
    • Registros antiguos sin offset se localizan a Bogotá.
    • La plantilla recibe “foto_url” con la URL que exista (photo_url | foto_url).
    """
    # ── Leer parámetros del formulario ──────────────────────────────────
    start_raw = request.GET.get("start")          # 'YYYY-MM-DDTHH:MM'
    end_raw   = request.GET.get("end")

    # ── Definir rango local ─────────────────────────────────────────────
    if not start_raw and not end_raw:
        end_local   = timezone.localtime()                 # ahora Bogotá
        start_local = end_local - timedelta(hours=24)
    else:
        try:
            start_local = (
                TZ_COL.localize(datetime.fromisoformat(start_raw))
                if start_raw else None
            )
            end_local = (
                TZ_COL.localize(datetime.fromisoformat(end_raw))
                if end_raw   else None
            )
        except ValueError:
            start_local = end_local = None

    # ── Leer DynamoDB ───────────────────────────────────────────────────
    resp = tabla_usuarios.scan()
    usuarios = []

    for item in resp.get("Items", []):
        ts_str = item.get("timestamp")
        url    = item.get("photo_url") or item.get("foto_url")   # toma el que exista
        if not (ts_str and url):
            continue

        # Parsear timestamp y normalizar a Bogotá
        try:
            ts_any = datetime.fromisoformat(ts_str)
            if ts_any.tzinfo is None:               # registro viejo (naïve)
                ts_local = TZ_COL.localize(ts_any)
            else:                                    # registro aware
                ts_local = ts_any.astimezone(TZ_COL)
        except ValueError:
            continue

        # Filtrado
        if (start_local and ts_local < start_local) or \
           (end_local   and ts_local > end_local):
            continue

        usuarios.append({
            "foto_url":       url,
            "identificacion": item.get("identificacion", ""),
            "nombre":         item.get("nombre", ""),
            "apellido":       item.get("apellido", ""),
            "rol":            item.get("rol", ""),
            "status":         item.get("status", "inactivo"),
            "timestamp":      ts_local.strftime("%Y-%m-%d %H:%M:%S"),
        })

    usuarios.sort(key=lambda x: x["timestamp"], reverse=True)

    # ── Valores por defecto para los inputs ─────────────────────────────
    default_start = start_raw or (
        start_local.strftime("%Y-%m-%dT%H:%M") if start_local else ""
    )
    default_end = end_raw or (
        end_local.strftime("%Y-%m-%dT%H:%M")   if end_local   else ""
    )

    return render(request, "UsuariosRecientes.html", {
        "title":         "Usuarios Recientes",
        "web_title":     "Waly",
        "current_url":   request.path,
        "sidebarItems":  sidebarItems,
        "usuarios":      usuarios,
        "default_start": default_start,
        "default_end":   default_end,
    })

def login_fake(request):
    return redirect('/accounts/index/')