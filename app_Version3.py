from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

def fetch_data():
    output = {}

    # --- METAR Data ---
    current_local_time = datetime.now().isoformat()
    metar_url = 'https://aviationweather.gov/api/data/metar?ids=PHNG&format=json'
    try:
        metar_response = requests.get(metar_url, timeout=10)
        if metar_response.status_code == 200:
            data = metar_response.json()[0]
            wind_speed = data.get('wspd')
            wind_direction = data.get('wdir')
            wind_gusts = data.get('wgst')
            rain_now = data.get('precip')
            rain_6hr = data.get('pcp6hr')
            rain_3hr = data.get('pcp3hr')
            rain_24hr = data.get('pcp24hr')

            # Direction as text
            direction_text = ""
            if wind_direction is not None:
                if 0 <= wind_direction <= 45: direction_text = "NE"
                elif 45 < wind_direction <= 90: direction_text = "East"
                elif 90 < wind_direction <= 135: direction_text = "SE"
                elif 135 < wind_direction <= 180: direction_text = "South"
                elif 180 < wind_direction <= 225: direction_text = "SW"
                elif 225 < wind_direction <= 270: direction_text = "West"
                elif 270 < wind_direction <= 315: direction_text = "NW"
                elif 315 < wind_direction <= 360: direction_text = "North"

            output["North Beach Conditions are as follows \n"] = {
                "receipt_time": current_local_time \n,
                "report_time_zulu": data.get("reportTime") \n,
                "wind_speed_kts": wind_speed,
                "wind_direction_deg": wind_direction,
                "wind_direction_text": direction_text,
                "wind_gusts_kts": wind_gusts,
                "rain_now_in": rain_now,
                "rain_3hr_in": rain_3hr,
                "rain_6hr_in": rain_6hr,
                "rain_24hr_in": rain_24hr
            }
        else:
            output["metar_error"] = f"Request failed with status code: {metar_response.status_code}"
    except Exception as e:
        output["metar_error"] = str(e)

    # --- NOAA Buoy Data ---
    buoy_url = 'https://www.ndbc.noaa.gov/data/latest_obs/51207.txt'
    try:
        buoy_response = requests.get(buoy_url, timeout=10)
        if buoy_response.status_code == 200:
            lines = buoy_response.text.splitlines()
            if len(lines) >= 17:
                output["buoy"] = {
                    "observed_at": lines[3],
                    "summary": lines[5:10],
                    "details": lines[12:17]
                }
            else:
                output["buoy_error"] = "Buoy data incomplete"
        else:
            output["buoy_error"] = f"Request failed with status code: {buoy_response.status_code}"
    except Exception as e:
        output["buoy_error"] = str(e)

    return output

@app.route("/")
def index():
    return "<h1>Wind & Wave Data API</h1><p>Visit <a href='/wind_wave_data.json'>/wind_wave_data.json</a> for latest data.</p>"

@app.route("/wind_wave_data.json")
def wind_wave_data():
    data = fetch_data()
    return jsonify(data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
