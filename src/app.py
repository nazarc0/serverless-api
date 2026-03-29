import json
import os
import pg8000
import base64

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")


def get_connection():
    host = DB_HOST
    port = 5432

    if DB_HOST and ":" in DB_HOST:
        parts = DB_HOST.split(":")
        host = parts[0]
        port = int(parts[1])

    return pg8000.connect(
        host=host,
        port=port,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        timeout=5
    )


def parse_body(event):
    body = event.get("body")

    if not body:
        return {}

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        return json.loads(body)
    except Exception:
        print("BAD BODY:", body)

    # fallback
    try:
        body = body.strip("{}")
        parts = body.split(",")

        result = {}
        for p in parts:
            if ":" not in p:
                continue
            k, v = p.split(":", 1)
            result[k.strip().strip('"')] = v.strip().strip('"')

        return result
    except Exception as e:
        print("FALLBACK FAILED:", body)
        raise e


def handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        # 🔥 СТАБІЛЬНИЙ ФІКС МЕТОДУ
        method = (
            event.get("requestContext", {}).get("http", {}).get("method")
            or event.get("httpMethod")
            or ""
        )

        conn = get_connection()
        cursor = conn.cursor()

        # таблиця
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id SERIAL PRIMARY KEY,
                name TEXT,
                status TEXT
            );
        """)
        conn.commit()

        # =====================
        # ➕ POST
        # =====================
        if method == "POST":
            body = parse_body(event)

            name = body.get("name", "Unknown")
            status = body.get("status", "working")

            cursor.execute(
                "INSERT INTO equipment (name, status) VALUES ($1, $2) RETURNING id;",
                (name, status)
            )

            new_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "message": "Created",
                    "id": new_id
                })
            }

        # =====================
        # 🔍 GET (З ФІЛЬТРОМ)
        # =====================
        elif method == "GET":
            params = event.get("queryStringParameters") or {}
            status = params.get("status")

            if status:
                cursor.execute(
                    "SELECT id, name, status FROM equipment WHERE status = $1;",
                    (status,)
                )
            else:
                cursor.execute(
                    "SELECT id, name, status FROM equipment;"
                )

            rows = cursor.fetchall()

            result = [
                {"id": r[0], "name": r[1], "status": r[2]}
                for r in rows
            ]

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }

        # =====================
        # 🔄 PUT (НОВЕ)
        # =====================
        elif method == "PUT":
            body = parse_body(event)
            params = event.get("queryStringParameters") or {}

            equipment_id = params.get("id")
            status = body.get("status", "working")

            if not equipment_id:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Missing id"})
                }

            cursor.execute(
                "UPDATE equipment SET status = $1 WHERE id = $2;",
                (status, equipment_id)
            )
            conn.commit()

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Updated"})
            }

        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method Not Allowed"})
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": str(e)
            })
        }