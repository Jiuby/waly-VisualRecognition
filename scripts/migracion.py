#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from botocore.config import Config
import boto3
import environ

# ——— 1) Encuentra y carga el .env de la raíz (junto a manage.py) ———
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

# ——— 2) Leer variables necesarias ———
try:
    AWS_ACCESS_KEY_ID     = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_REGION            = env('AWS_REGION')
except Exception as e:
    print(f"❌ Falta variable en .env: {e}")
    sys.exit(1)

# ——— 3) Inicializa DynamoDB con reintentos ———
aws_config = Config(retries={'max_attempts': 5, 'mode': 'standard'})
session = boto3.Session(
    aws_access_key_id     = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name           = AWS_REGION
)
dynamo = session.resource('dynamodb', config=aws_config)
tabla = dynamo.Table('Usuarios')  # Asegúrate de que la tabla existe

# ——— 4) Escanea y migra ———
def migrate_table():
    # 1) Escanear todos los items de la tabla
    response = tabla.scan()
    items = response.get('Items', [])

    # 2) Para cada item, añade timestamp y status si faltan
    for item in items:
        key = {'foto_url': item['foto_url']}
        updates = []
        expr_names = {}
        expr_values = {}

        if 'timestamp' not in item:
            updates.append('#ts = :t')
            expr_names['#ts'] = 'timestamp'
            expr_values[':t'] = datetime.utcnow().isoformat()

        if 'status' not in item:
            updates.append('#st = :s')
            expr_names['#st'] = 'status'
            expr_values[':s'] = 'inactivo'

        if updates:
            update_expr = 'SET ' + ', '.join(updates)
            tabla.update_item(
                Key=key,
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            print(f"[MIGRATED] {key} → {update_expr}")

    print("Migración completada.")

if __name__ == '__main__':
    migrate_table()
