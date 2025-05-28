#!/usr/bin/env python3
import os
import sys
import random
import boto3
from botocore.config import Config
import environ

# ——— 1) Localiza y carga tu .env de la raíz (junto a manage.py) ———
def find_project_env():
    path = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(path, 'manage.py')):
            candidate = os.path.join(path, '.env')
            return candidate if os.path.isfile(candidate) else None
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent

dotenv_path = find_project_env()
if not dotenv_path:
    print("ERROR: no se encontró .env junto a manage.py")
    sys.exit(1)

env = environ.Env()
env.read_env(dotenv_path)

# ——— 2) Lee las variables necesarias ———
try:
    AWS_ACCESS_KEY_ID     = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_REGION            = env('AWS_REGION')
    S3_BUCKET             = env('S3_BUCKET')
    S3_PREFIX             = env('S3_PREFIX', default='faces/')       # opcional
    DYNAMO_TABLE_NAME     = env('DYNAMO_TABLE_NAME', default='Usuarios')
except Exception as e:
    print(f"❌ Falta variable en .env: {e}")
    sys.exit(1)

# ——— 3) Inicializa clientes de AWS ———
aws_config = Config(retries={'max_attempts': 5, 'mode': 'standard'})
session = boto3.Session(
    aws_access_key_id     = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name           = AWS_REGION
)
s3 = session.client('s3', config=aws_config)
dynamo = session.resource('dynamodb', config=aws_config)
tabla = dynamo.Table(DYNAMO_TABLE_NAME)

# ——— 4) Lógica para poblar usuarios ———
ROLES = [
    "estudiante",
    "docente",
    "administrativo",
    "visitante",
    "personal operativo"
]

def listar_keys_s3(bucket: str, prefix: str):
    """Generador de todas las keys bajo un prefijo en el bucket."""
    cont_token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if cont_token:
            kwargs["ContinuationToken"] = cont_token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            yield obj["Key"]
        if resp.get("IsTruncated"):
            cont_token = resp["NextContinuationToken"]
        else:
            break

def parse_filename(key: str):
    """
    De 'faces/nombre_apellido_cedula.jpg' extrae:
      nombre, apellido, cedula
    """
    filename = key.rsplit("/", 1)[-1]
    namepart = filename.rsplit(".", 1)[0]
    parts = namepart.split("_")
    if len(parts) != 3:
        raise ValueError(f"Nombre de archivo inesperado: {filename}")
    return parts  # [nombre, apellido, cedula]

def construir_url(bucket: str, key: str) -> str:
    """Construye la URL pública en S3."""
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def main():
    for key in listar_keys_s3(S3_BUCKET, S3_PREFIX):
        try:
            nombre, apellido, cedula = parse_filename(key)
        except ValueError as e:
            print(f"[SKIP] {e}")
            continue

        foto_url = construir_url(S3_BUCKET, key)
        rol = random.choice(ROLES)

        item = {
            "foto_url":      foto_url,
            "identificacion": cedula,
            "nombre":         nombre.capitalize(),
            "apellido":       apellido.capitalize(),
            "rol":            rol
        }

        tabla.put_item(Item=item)
        print(f"[OK] Insertado: {item}")

    print("¡Proceso completado!")

if __name__ == "__main__":
    main()
