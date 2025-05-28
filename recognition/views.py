import os
import pickle
import boto3
import traceback
from datetime import datetime
import cv2
import numpy as np
import insightface
import base64
import json, uuid, logging
from boto3.dynamodb.conditions import Attr            # si no lo tienes

from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from sklearn.preprocessing import normalize
from django.utils import timezone
# ——————————————————————————————————————————————————————
#  Configuración S3 + Carga global de embeddings
# ——————————————————————————————————————————————————————

logger = logging.getLogger(__name__)



# Cliente S3
s3 = boto3.client(
    's3',
    region_name        = settings.AWS_REGION,
    aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
)

# Descarga y carga de embeddings (una sola vez al iniciar)
try:
    # Usa las constantes desde settings
    resp = s3.get_object(
        Bucket=settings.S3_BUCKET,
        Key=settings.S3_KEY
    )
    raw   = resp['Body'].read()
    state = pickle.loads(raw)
    known_embs   = normalize(state['embeddings'])
    known_labels = state['labels']
    print(f"✔️  Embeddings cargados desde s3://{settings.S3_BUCKET}/{settings.S3_KEY}")
except Exception as e:
    # Si falla, vuelca el traceback y levanta un error claro
    traceback.print_exc()
    raise RuntimeError(
        f"No fue posible cargar los embeddings desde s3://{settings.S3_BUCKET}/{settings.S3_KEY}"
    ) from e

dynamo = boto3.resource(
    'dynamodb',
    aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
    region_name           = settings.AWS_REGION
)
tabla_usuarios = dynamo.Table('Usuarios')  # Ase
tabla_incidencias = dynamo.Table("Incidencias")

# ——————————————————————————————————————————————————————
#  Inicialización del modelo ArcFace
# ——————————————————————————————————————————————————————
model = insightface.app.FaceAnalysis(allowed_modules=['detection', 'recognition'])
model.prepare(ctx_id=-1)

# ——————————————————————————————————————————————————————
#  Sidebar común para las vistas
# ——————————————————————————————————————————————————————
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

# ——————————————————————————————————————————————————————
#  Vistas de renderizado
# ——————————————————————————————————————————————————————

# ---------- función auxiliar ----------
def _nuevo_evento(payload, estado):
    ts = timezone.localtime(timezone.now()).isoformat()   # ya −05:00
    evento_id = uuid.uuid4().hex
    tabla_usuarios.put_item(Item={
        "foto_url":       evento_id,
        "photo_url":      payload["foto_url"],
        "identificacion": payload["identificacion"],
        "timestamp":      ts,           # hora local
        "status":         estado,
        "nombre":         payload["nombre"],
        "apellido":       payload.get("apellido",""),
        "rol":            payload.get("rol","visitante"),
    })
    return ts

# ---------- entrada ----------
@csrf_exempt
def registrar_entrada(request):
    """
    GET  → muestra la página con la cámara en modo ENTRADA
    POST → guarda un nuevo evento con status='activo'
    """
    if request.method == "GET":
        return render(request, "RegistrarEntrada.html", {
            "title":        "Registrar Entrada",
            "web_title":    "Waly",
            "current_url":  request.path,
            "sidebarItems": sidebarItems,
            "modo":         "entrada",          # para el data-mode en la plantilla
        })

    if request.method == "POST":
        payload = json.loads(request.body)
        ts = _nuevo_evento(payload, "activo")
        return JsonResponse({"status": "ok", "timestamp": ts})

    return HttpResponseNotAllowed(["GET", "POST"])

def pantalla_salida(request):
    """
    Muestra la página con la cámara lista para registrar SALIDA.
    La lógica de guardado seguirá en registrar_salida (POST).
    """
    return render(request, "RegistrarEntrada.html", {        # reutilizamos
        "title":        "Registrar Salida",
        "web_title":    "Waly",
        "current_url":  request.path,
        "sidebarItems": sidebarItems,
        "modo":         "salida",                            # ← pasa modo
    })

@csrf_exempt
def registrar_salida(request):
    """
    GET  → muestra la página con la cámara en modo SALIDA
    POST → guarda un nuevo evento con status='inactivo'
    """
    if request.method == "GET":
        return render(request, "RegistrarEntrada.html", {   # misma plantilla
            "title":        "Registrar Salida",
            "web_title":    "Waly",
            "current_url":  request.path,
            "sidebarItems": sidebarItems,
            "modo":         "salida",        # <div data-mode="salida">
        })

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Formato inválido"}, status=400)

        ts = _nuevo_evento(payload, "inactivo")             # ← guarda
        return JsonResponse({"status": "ok", "timestamp": ts})

    return HttpResponseNotAllowed(["GET", "POST"])
def registrar_usuario(request):
    """
    Vista para crear un nuevo usuario (almacena foto en S3 y metadata en DynamoDB).
    """
    if request.method == "POST":
        nombre   = request.POST['nombre'].strip()
        apellido = request.POST['apellido'].strip()
        cedula   = request.POST['identificacion'].strip()
        rol      = request.POST['rol']
        foto_b64 = request.POST['foto_camara']  # base64

        # Preparar archivo y subir a S3
        filename = f"{nombre}_{apellido}_{cedula}.jpg".replace(" ", "_").lower()
        key = f"faces/{filename}"
        header, encoded = foto_b64.split(",", 1)
        data = base64.b64decode(encoded)
        s3.put_object(
            Bucket="hackathon-facesiupb",
            Key=key,
            Body=data,
            ContentType='image/jpeg',
            ACL='public-read'
        )
        bucket = "hackathon-facesiupb"
        foto_url = f"https://{bucket}.s3.amazonaws.com/{key}"

        # Guardar metadatos en DynamoDB
        tabla_usuarios.put_item(
            Item={
                'foto_url':      foto_url,
                'identificacion':cedula,
                'nombre':        nombre,
                'apellido':      apellido,
                'rol':           rol,
                'timestamp':     datetime.utcnow().isoformat(),
                'status':        'inactivo',  # por defecto
            }
        )
        return redirect('dashboard')

    return render(request, 'RegistrarUsuario.html', {
        "title":        "Registrar Usuario",
        "web_title":    "Waly",
        "current_url":  request.path,
        "sidebarItems": sidebarItems,
    })
# ——————————————————————————————————————————————————————
#  Endpoint de verificación facial
# ——————————————————————————————————————————————————————
@csrf_exempt
def verify_face(request):
    try:
        # 1) Leer la imagen
        img_bytes = request.FILES["snapshot"].read()
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            # ⇢ registrar incidencia no_face
            tabla_incidencias.put_item(Item={
                "id":        str(uuid.uuid4()),
                "timestamp": timezone.now().isoformat(),
                "motivo":    "no_face",
            })
            return JsonResponse({"status": "no_face"})

        # 2) Detección y embedding
        faces = model.get(img)
        if not faces:
            tabla_incidencias.put_item(Item={
                "id":        str(uuid.uuid4()),
                "timestamp": timezone.now().isoformat(),
                "motivo":    "no_face",
            })
            return JsonResponse({"status": "no_face"})

        emb = normalize(faces[0].embedding.reshape(1, -1))[0]

        # 3) Similaridad
        sims     = known_embs.dot(emb)
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])

        if best_sim < 0.7:
            tabla_incidencias.put_item(Item={
                "id":        str(uuid.uuid4()),
                "timestamp": timezone.now().isoformat(),
                "motivo":    "unknown",
            })
            return JsonResponse({"status": "unknown"})

        # 4) Datos de la persona reconocida
        ext        = known_labels[best_idx]            # juan_velez_1017
        name, uid  = ext.rsplit("_", 1)
        name       = name.replace("_", " ")
        foto_url   = f"{S3_PREFIX}/{ext}.jpg"

        # 5) Marcar “activo” en Usuarios
        ts = timezone.now().isoformat()
        tabla_usuarios.update_item(
            Key={"foto_url": foto_url},
            UpdateExpression="SET #st=:s, #ts=:t",
            ExpressionAttributeNames={"#st": "status", "#ts": "timestamp"},
            ExpressionAttributeValues={":s": "activo", ":t": ts},
        )

        # 6) Respuesta
        return JsonResponse({
            "status": "ok",
            "name":   name,
            "id":     uid,
            "score":  round(best_sim, 2),
            "foto_url": foto_url,
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)