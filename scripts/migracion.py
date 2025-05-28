import boto3
from datetime import datetime
from botocore.config import Config
from django.conf import settings

# — Configuración AWS —
AWS_REGION = 'us-east-1'
TABLE_NAME = 'Usuarios'

# Cliente DynamoDB con reintentos
aws_config = Config(retries={'max_attempts': 5, 'mode': 'standard'})



dynamo = boto3.resource(
    'dynamodb',
    aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
    region_name           = settings.AWS_REGION,
    config                = aws_config
)
tabla_usuarios = dynamo.Table('Usuarios')

tabla = dynamo.Table(TABLE_NAME)

# 1) Escanear todos los items de la tabla
response = tabla.scan()
items = response.get('Items', [])

# 2) Revisar y actualizar cada item que no tenga timestamp o status
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
        print(f"Actualizado {key}: {update_expr}")

print("Migración completada.")
