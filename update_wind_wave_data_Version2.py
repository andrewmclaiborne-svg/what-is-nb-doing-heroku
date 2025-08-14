from datetime import datetime
import requests
import json

output = {}

# --- METAR Data ---
current_local_time = datetime.now().isoformat()
metar_url = 'https://aviationweather.gov/api/data/metar?ids=PHNG&format=json'
metar_response = requests.get(metar_url)

if metar_response.status_code == 200:
    try:
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
        if 0 <= wind_direction <= 45: direction_text = "NE"
        elif 45 < wind_direction <= 90: direction_text = "East"
        elif 90 < wind_direction <= 135: direction_text = "SE"
        elif 135 < wind_direction <= 180: direction_text = "South"
        elif 180 < wind_direction <= 225: direction_text = "SW"
        elif 225 < wind_direction <= 270: direction_text = "West"
        elif 270 < wind_direction <= 315: direction_text = "NW"
        elif 315 < wind_direction <= 360: direction_text = "North"

        output["metar"] = {
            "receipt_time": current_local_time,
            "report_time_zulu": data.get("reportTime"),
            "wind_speed_kts": wind_speed,
            "wind_direction_deg": wind_direction,
            "wind_direction_text": direction_text,
            "wind_gusts_kts": wind_gusts,
            "rain_now_in": rain_now,
            "rain_3hr_in": rain_3hr,
            "rain_6hr_in": rain_6hr,
            "rain_24hr_in": rain_24hr
        }
    except Exception as e:
        output["metar_error"] = str(e)
else:
    output["metar_error"] = f"Request failed with status code: {metar_response.status_code}"

# --- NOAA Buoy Data ---
buoy_url = 'https://www.ndbc.noaa.gov/data/latest_obs/51207.txt'
buoy_response = requests.get(buoy_url)
if buoy_response.status_code == 200:
    lines = buoy_response.text.splitlines()
    # Defensive: check if enough lines
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

# --- Write to JSON ---
with open("/var/www/html/wind_wave_data.json", "w") as f:
    json.dump(output, f, indent=2)