from flask import Flask, jsonify, render_template
import requests
from datetime import datetime, timezone, timedelta
import re

app = Flask(__name__)

def fetch_data():
    output = {}
    decider_value = 0

    # --- METAR Data ---
    tzinfo = timezone(timedelta(hours=-10))
    current_local_time = datetime.now(tzinfo).strftime("%Y-%m-%d %H:%M:%S")
    
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

            decider_value = decider_function(wind_speed, wind_direction)
            print(f"Decider value: {decider_value}")

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

            output["North Beach Conditions are as follows"] = {
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
            
            seas = lines[5]
            gswell = lines[12]
            wswell = lines[15]

            seasp = lines[6]
            gper = lines[13]
            wper = lines[16]

          
            pattern = r"\d+"

            seas_per_as_string = re.search(pattern, seasp)
            if seas_per_as_string:
                seasp_int = int(seas_per_as_string.group())

            decider_value = decider_value + decider_seasp(seasp_int)
                
            
            pattern = r"[-+]?\d*\.\d+"
            
            seas_num_as_string = re.search(pattern, seas)
            if seas_num_as_string:
                seas_float = float(seas_num_as_string.group())
            
            gswell_num_as_string = re.search(pattern, gswell)
            if gswell_num_as_string:
                gswell_float = float(gswell_num_as_string.group())
            
            gper_num_as_string = re.search(pattern, gper)
            if gper_num_as_string:
                gper_float = float(gper_num_as_string.group())
                

            wswell_num_as_string = re.search(pattern, wswell)
            if wswell_num_as_string:
                wswell_float = float(wswell_num_as_string.group())

            wper_num_as_string = re.search(pattern, wper)
            if wper_num_as_string:
                wper_float = float(wper_num_as_string.group())
                

            decider_value = decider_value + decider_wper(wper_float)
            decider_value = decider_value + decider_gper(gper_float)
            decider_value = decider_value + decider_seas(seas_float)
            decider_value = decider_value + decider_gswell(gswell_float)
            decider_value = decider_value + decider_wswell(wswell_float)

            swelld1 = lines[14]
            swelld2 = lines[17]

            decider_value = decider_value + decider_swelld(swelld1)
            decider_value = decider_value + decider_swelld2(swelld2)    
            print(f"Decider value after swell: {decider_value}")
           
            output["buoy"] = {
                    "observed_at": lines[3],
                    "summary": lines[5:8],
                    "details": lines[12:18]
                }
            
        else:
            output["buoy_error"] = f"Request failed with status code: {buoy_response.status_code}"
    except Exception as e:
        output["buoy_error"] = str(e)

    condtion_dec = condtion_decider(decider_value)

    print(f"{condtion_dec}")

    da_answer = what_is_it(condtion_dec)
    output["da_answer"] = da_answer
    print(f"Condition Decider: {da_answer}")



    return output




## Decider Function
## idea is pretty straight foward, decider will start at 0, and each condition will be out of 3. Add and average the total to get what the condtiions are like.
## max points if 3.

def decider_function(wind_speed, wind_direction):
    decider = 0

    if wind_speed is not None and wind_direction is not None:
        if wind_speed is None:
            decider =+ 3
        elif 1<= wind_speed <= 3:
            decider =+ 3
        ## offshore winds 
        elif 4<= wind_speed <= 7 and 120 <= wind_direction <= 250:
            decider =+3
        elif 8 <= wind_speed <= 12 and 120 <= wind_direction <= 250: 
            decider =+ 3
        elif 13 <= wind_speed <= 15 and 120 <= wind_direction <= 250:  
            decider =+ 2
        elif 16 <= wind_speed <= 20 and 120 <= wind_direction <= 250:
            decider =+ 2
        elif 21<= wind_speed and 120 <= wind_direction <= 250:
            decider =+ 2
        ## now for the onshore winds 
        elif 4 <= wind_speed <= 7 and (wind_direction < 120 or wind_direction > 250):
            decider =+ 2
        elif 8 <= wind_speed <= 12 and (wind_direction < 120 or wind_direction > 250):
            decider =+ 1
        elif 13 <= wind_speed <= 15 and (wind_direction < 120 or wind_direction > 250):
            decider =+ 1
        elif 16 <= wind_speed <= 20 and (wind_direction < 120 or wind_direction > 250):
            decider =+ 1
        elif wind_speed >= 21 and (wind_direction < 120 or wind_direction > 250):
            decider =+ 1
        else:
             pass
    
    return decider

## This one is for swell angle. Swell1 is the primary ground swell so it gets rated out of 3. Swell 2 is wind swell so it get rated out of 1 since it holds less weight.
## max points for the decier if 5.
def decider_swelld(swelld1):
    decider = 0
    if swelld1 is not None:
        if swelld1 == "Direction: NE" or "Direction: ENE" or "Direction: E" or "Direction: NNE":
            decider =+1
        elif swelld1 == "Direction: N" or "Direction: NNW":
            decider =+ 3
        elif swelld1 == "Direction: NNW":
            decider =+2
        elif swelld1 == "Direction WNW" or "Direction W":
            decider =+ 1
    else:
        pass
    
    return decider

## this is for wind swell angle
## max points is 2.

def decider_swelld2(swelld2):
    decider = 0
    if swelld2 is not None:        
        if swelld2 == "Direction: NE" or "Direction: ENE" or "Direction: E" or "Direction: NNE":
            decider =+ 1
        elif swelld2 == "Direction: N" or "Direction: NNW" or "Direction: NW":
            decider =+ 1
        elif swelld2 == "Direction: WNW" or "Direction: W":
            decider =+ 2
    else:
        pass
    return decider

##this decides for primary ground swell.
## max 4 points

def decider_gswell(gswell_float):
    decider = 0
    if gswell_float != 0.0:
        if 0.1 <= gswell_float <= 2.5:
            decider =+ 1
        elif 2.6 <= gswell_float <= 3.0:
            decider =+ 2
        elif 3.1 <= gswell_float <= 4.5:
            decider =+ 3
        elif gswell_float >= 4.6:
            decider =+4
    else:
        decider = 0
    
    return decider

## decider for wind swell. 
## max is 2 points.

def decider_wswell(wswell_float):
    decider = 0
    if wswell_float != 0.0:
        if 0.1 <= wswell_float <= 2.5:
            decider =+ 1
        elif 2.6 <= wswell_float <= 3.0:
            decider =+ 1
        elif 3.1 <= wswell_float <= 4.5:
            decider =+ 2
        elif wswell_float >= 4.6:
            decider =+2
    else:
        decider = 0
    
    return decider

## this is for the sea state (usually a overview for the whole picture)
## max 3 points

def decider_seas(seas_float):
    decider = 0
    if seas_float != 0.0:
        if 0.1 <= seas_float <= 2.0:
            decider =+ 1
        elif 2.6 <= seas_float <= 5.0:
            decider =+ 2
        elif seas_float >= 5.1:
            decider =+ 3
    else:
        decider = 0
    
    return decider

## this is for seas period
## max 3 points

def decider_seasp(seasp_int):
    decider = 0
    if seasp_int != 0:
        if 1 <= seasp_int <= 9:
            decider =+ 1
        elif 10 <= seasp_int <= 13:
            decider =+ 2
        elif seasp_int >= 14:
            decider =+ 3
    else:
        decider = 0
    
    return decider

## this for the ground period, important because it dictates how intense the waves are going to be.
## max 4 points

def decider_gper(gper_float):
    decider = 0
    if gper_float != 0.0:
        if 0.1 <= gper_float <= 9.9:
            decider =+ 1
        elif 9.9 <= gper_float <= 12.5:
            decider =+ 2
        elif 12.6 <= gper_float <= 14.0:
            decider =+ 3
        elif gper_float >= 14.1:
            decider =+ 4
    else:
        decider = 0
    
    return decider

## this is for wind period
## max 3 points

def decider_wper(wper_float):
    decider = 0
    if wper_float != 0.0:
        if 0.1 <= wper_float <= 12.5:
            decider =+ 1
        elif 12.6 <= wper_float <= 14.0:
            decider =+ 2
        elif wper_float >= 14.1:
            decider =+ 3
    else:
        decider = 0
    
    return decider

def condtion_decider(decider_value):
    if decider_value != 0:
        condition_dec = round((decider_value / 29) * 100)

    else:
        condtion = 0.0

    return condition_dec

def what_is_it(condition_dec):
    if condition_dec != 0:
        if condition_dec <= 20:
            return "either small and fun or just bad"
        elif 21 <= condition_dec <= 50:
            return "bad"
        elif 51 <= condition_dec <= 65:
            return "possibly surferable"
        elif 65 <= condition_dec <= 75:
            return "it would entertain the idea"
        elif 76 <= condition_dec <= 85:
            return "its probably 'fun out' conditions"
        elif 86 <= condition_dec <= 90:
            return "you need me to tell you to go?"
        elif 91 <= condition_dec <= 95:
            return "brah"
        else:
            return "it broke"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/wind_wave_data.json")
def wind_wave_data():
    data = fetch_data()
    return jsonify(data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
