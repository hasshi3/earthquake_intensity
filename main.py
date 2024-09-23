import os
import json
import base64
from flask import Flask, request
from google.cloud import storage
import psycopg2

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_pubsub_message():
    """Pub/SubからのHTTP Pushメッセージを処理"""
    envelope = request.get_json()

    if not envelope:
        return ("Bad Request: No Pub/Sub message received", 400)

    # Pub/Sub メッセージのデコード
    pubsub_message = envelope.get("message", {})
    if "data" in pubsub_message:
        message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        message_json = json.loads(message_data)

        # GCS バケット名とファイル名を取得
        bucket_name = message_json['bucket']
        file_name = message_json['name']

        # ファイルが "results/" フォルダ内の ".geojson" ファイルか確認
        if file_name.startswith('results/') and file_name.endswith('.geojson'):
            process_geojson_file(bucket_name, file_name)

    return ("", 204)


def process_geojson_file(bucket_name, file_name):
    """GCSのGeoJSONファイルを取得し、PostgreSQLに登録"""
    # GCS クライアントを作成
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    # GeoJSONファイルをダウンロード
    geojson_data = blob.download_as_string()
    geojson_dict = json.loads(geojson_data)

    # PostgreSQLに接続
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port="5432"
    )
    cur = conn.cursor()

    # データを挿入するクエリ
    insert_query = """
        INSERT INTO earthquakes (event_time, magnitude, depth, latitude, longitude, location_description, geom)
        VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    """
    
    # GeoJSONデータの各フィーチャを処理し、PostgreSQLに挿入
    for feature in geojson_dict['features']:
        properties = feature['properties']
        geometry = feature['geometry']['coordinates']
        
        event_time = properties['time']
        magnitude = properties['mag']
        depth = properties['depth']
        latitude = geometry[1]
        longitude = geometry[0]
        location_description = properties['place']
        
        data = (event_time, magnitude, depth, latitude, longitude, location_description, longitude, latitude)
        cur.execute(insert_query, data)
    
    # トランザクションのコミットと接続のクローズ
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    # Flaskアプリケーションを起動
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

