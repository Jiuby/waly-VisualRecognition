import re
import random
import boto3
from botocore.config import Config
from django.conf import settings

# ————— Configuración —————
BUCKET_NAME = "hackathon-facesiupb"
PREFIX      = "faces/"
TABLE_NAME  = "Usuarios"

ROLES = [
    "estudiante",
    "docente",
    "administrativo",
    "visitante",
    "personal operativo"
]

# Opcional: tiempo de espera/reintentos para AWS
aws_config = Config(
    retries = {
        'max_attempts': 5,
        'mode': 'standard'
    }
)


# Cliente S3
s3 = boto3.client(
    's3',
    region_name            = settings.AWS_REGION,
    aws_access_key_id      = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key  = settings.AWS_SECRET_ACCESS_KEY,
)

dynamo = boto3.resource(
    'dynamodb',
    region_name            = settings.AWS_REGION,
    aws_access_key_id      = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key  = settings.AWS_SECRET_ACCESS_KEY,
)
tabla = dynamo.Table('Usuarios')  # Ase


def listar_keys_s3(bucket: str, prefix: str):
    """Lista todos los objetos bajo un prefijo."""
    continuation_token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            yield obj["Key"]
        if resp.get("IsTruncated"):  # más páginas
            continuation_token = resp["NextContinuationToken"]
        else:
            break


def parse_filename(key: str):
    """
    De 'faces/nombre_apellido_cedula.jpg' extrae:
      nombre, apellido, cedula
    """
    filename = key.rsplit("/", 1)[-1]
    # eliminamos extensión
    namepart = filename.rsplit(".", 1)[0]
    parts = namepart.split("_")
    if len(parts) != 3:
        raise ValueError(f"Nombre de archivo inesperado: {filename}")
    return parts  # [nombre, apellido, cedula]


def construir_url(bucket: str, key: str) -> str:
    """Construye la URL pública en S3."""
    domain = f"{bucket}.s3.amazonaws.com"
    return f"https://{domain}/{key}"


def main():
    for key in listar_keys_s3(BUCKET_NAME, PREFIX):
        try:
            nombre, apellido, cedula = parse_filename(key)
        except ValueError as e:
            print(f"[SKIP] {e}")
            continue

        foto_url = construir_url(BUCKET_NAME, key)
        rol = random.choice(ROLES)

        item = {
            "foto_url":      foto_url,    # PK de tu tabla
            "identificacion": cedula,
            "nombre":         nombre.capitalize(),
            "apellido":       apellido.capitalize(),
            "rol":            rol
        }

        # Inserción a DynamoDB
        tabla.put_item(Item=item)
        print(f"[OK] Insertado: {item}")

    print("¡Proceso completado!")


if __name__ == "__main__":
    main()
