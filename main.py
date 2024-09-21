from google.cloud import storage
import json
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask is running on Cloud Run!"

@app.route('/run_geojson')
def run_geojson():
    try:
        reflesh_stations_geojson()
        return jsonify({"status": "success", "message": "GeoJSON processed successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def reflesh_stations_geojson():
    # GCSからファイルを取得
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('your-bucket-name')  # GCSバケット名
    blob = bucket.blob('stations/stations.geojson')  # ファイルパス
    content = blob.download_as_text()

    # GeoJSONを解析
    stations_data = json.loads(content)

    # PostgreSQLデータベースへの接続
    conn = psycopg2.connect(
        dbname='your_db_name',
        user='your_db_user',
        password='your_password',
        host='your_db_host',
        port='your_db_port'
    )
    cur = conn.cursor()

    # データベースにstationsのデータを挿入
    insert_query = """
    INSERT INTO Stations (area_code, area_name, city_code, city_name, station_code, station_name, station_furigana, pref_name, pref_code, affiliation, latitude, longitude)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (station_code) DO UPDATE
    SET area_code = EXCLUDED.area_code,
        area_name = EXCLUDED.area_name,
        city_code = EXCLUDED.city_code,
        city_name = EXCLUDED.city_name,
        station_name = EXCLUDED.station_name,
        station_furigana = EXCLUDED.station_furigana,
        pref_name = EXCLUDED.pref_name,
        pref_code = EXCLUDED.pref_code,
        affiliation = EXCLUDED.affiliation,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude;
    """

    # GeoJSONのデータをデータベースに挿入
    for feature in stations_data['features']:
        properties = feature['properties']
        geometry = feature['geometry']
        cur.execute(insert_query, (
            properties['area_code'],
            properties['area_name'],
            properties['city_code'],
            properties['city_name'],
            properties['station_code'],
            properties['station_name'],
            properties['station_furigana'],
            properties['pref_name'],
            properties['pref_code'],
            properties['affiliation'],
            geometry['coordinates'][1],  # latitude
            geometry['coordinates'][0]   # longitude
        ))

    conn.commit()
    cur.close()
    conn.close()

# メイン処理
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
