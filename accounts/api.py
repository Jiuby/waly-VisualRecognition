# accounts/api.py
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from boto3.dynamodb.conditions import Attr
import boto3
from django.conf import settings




dynamo = boto3.resource(
    'dynamodb',
    region_name            = settings.AWS_REGION,
    aws_access_key_id      = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key  = settings.AWS_SECRET_ACCESS_KEY,
)
tabla = dynamo.Table('Usuarios')
# ── Lista de roles que pintas en el dashboard ──────
ROLES = ["estudiante", "docente", "administrativo",
         "visitante", "operativo"]

def api_entradas_por_rol(request):
    ahora   = timezone.now()
    inicio  = ahora - timedelta(hours=12)     # últimas 12 h

    resp = tabla.scan(
        FilterExpression=Attr("timestamp").gte(inicio.isoformat())
    ).get("Items", [])

    # agrupar por bloques de 30 min
    buckets, labels = {}, []
    tz = timezone.get_current_timezone()

    for item in resp:
        try:
            ts = timezone.datetime.fromisoformat(item["timestamp"]).astimezone(tz)
        except (KeyError, ValueError):
            continue

        bloque = ts.replace(minute=(0 if ts.minute < 30 else 30),
                            second=0, microsecond=0)
        label  = bloque.strftime("%H:%M")
        if label not in labels:
            labels.append(label)

        rol = item.get("rol", "visitante")
        key = (rol, label)
        buckets[key] = buckets.get(key, 0) + 1

    # ordenar etiquetas cronológicamente
    labels.sort()

    # construir series por rol
    series = {
        rol: [buckets.get((rol, lbl), 0) for lbl in labels]
        for rol in ROLES
    }

    return JsonResponse({"labels": labels, "series": series})