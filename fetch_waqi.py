import requests
import json
import os
from datetime import datetime, timedelta

LAT = 26.2389
LON = 73.0243
DATA_FILE = 'data/jodhpur_merra2.json'

def main():
    start_date = datetime(2026, 1, 1)
    end_date = min(datetime.now(), datetime.now() - timedelta(days=4))

    min_str = start_date.strftime('%Y%m%d')
    max_str = end_date.strftime('%Y%m%d')

    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,WS10M,AOD_55,DUSMASS25,OCSMASS,BCSMASS,SSSMASS25,SO4SMASS&community=AG&longitude={LON}&latitude={LAT}&start={min_str}&end={max_str}&format=JSON"
    
    print(f"Fetching NASA POWER MERRA-2 data for Jodhpur ({min_str} to {max_str})...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Request Failed: {response.status_code}")
        return

    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    
    t2m = parameters.get('T2M', {})
    ws10m = parameters.get('WS10M', {})
    aod55 = parameters.get('AOD_55', {})
    dust = parameters.get('DUSMASS25', {})
    oc = parameters.get('OCSMASS', {})
    bc = parameters.get('BCSMASS', {})
    ss = parameters.get('SSSMASS25', {})
    so4 = parameters.get('SO4SMASS', {})

    curr = start_date
    history = []
    
    while curr <= end_date:
        date_str = curr.strftime('%Y%m%d')
        formatted_date = curr.strftime('%Y-%m-%d')
        
        d_val = dust.get(date_str, -999.0)
        oc_val = oc.get(date_str, -999.0)
        bc_val = bc.get(date_str, -999.0)
        ss_val = ss.get(date_str, -999.0)
        so4_val = so4.get(date_str, -999.0)
        t_val = t2m.get(date_str, -999.0)
        ws_val = ws10m.get(date_str, -999.0)
        aod_val = aod55.get(date_str, -999.0)

        if d_val != -999.0:
            d_ug = d_val * 1e9
            oc_ug = oc_val * 1e9 if oc_val != -999.0 else 0.0
            bc_ug = bc_val * 1e9 if bc_val != -999.0 else 0.0
            ss_ug = ss_val * 1e9 if ss_val != -999.0 else 0.0
            so4_ug = so4_val * 1e9 * (132.14 / 96.06) if so4_val != -999.0 else 0.0
            
            # PM calculations based on GOCART speciation
            pm25_total = d_ug + oc_ug + bc_ug + ss_ug + so4_ug
            pm1 = (0.35 * d_ug) + oc_ug + bc_ug + (0.5 * ss_ug) + so4_ug
            # In arid regions like Jodhpur, coarse dust significantly elevates PM10
            pm10 = pm25_total + (2.2 * d_ug)
            
            history.append({
                "date": formatted_date,
                "aod_55": round(aod_val, 2) if aod_val != -999.0 else 0.0,
                "pm1": round(pm1, 2),
                "pm25_total": round(pm25_total, 2),
                "pm10": round(pm10, 2),
                "dust_pm25": round(d_ug, 2),
                "oc_mass": round(oc_ug, 2),
                "bc_mass": round(bc_ug, 2),
                "ss_pm25": round(ss_ug, 2),
                "so4_mass": round(so4_ug, 2),
                "temperature_2m": round(t_val, 2) if t_val != -999.0 else 0.0,
                "wind_speed_10m": round(ws_val, 2) if ws_val != -999.0 else 0.0
            })
            
        curr += timedelta(days=1)

    latest = history[-1] if history else {}

    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": "Jodhpur, India (NASA POWER / MERRA-2)",
        "latest": latest,
        "history": history
    }

    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Successfully generated Jodhpur MERRA-2 dataset with {len(history)} records including PM1, PM2.5, and PM10.")

if __name__ == "__main__":
    main()
