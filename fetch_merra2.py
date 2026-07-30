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

    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,WS10M,RHOA,AOD_55,DUSMASS25,OCSMASS,BCSMASS,SSSMASS25,SO4SMASS&community=AG&longitude={LON}&latitude={LAT}&start={min_str}&end={max_str}&format=JSON"
    
    print(f"Fetching NASA POWER MERRA-2 data for Jodhpur ({min_str} to {max_str})...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Request Failed: {response.status_code}")
        return

    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    
    t2m = parameters.get('T2M', {})
    ws10m = parameters.get('WS10M', {})
    rhoa = parameters.get('RHOA', {})
    aod55 = parameters.get('AOD_55', {})
    dust_tot = parameters.get('DUSMASS25', {})
    oc_tot = parameters.get('OCSMASS', {})
    bc_tot = parameters.get('BCSMASS', {})
    ss_tot = parameters.get('SSSMASS25', {})
    so4_tot = parameters.get('SO4SMASS', {})

    curr = start_date
    history = []
    
    while curr <= end_date:
        date_str = curr.strftime('%Y%m%d')
        formatted_date = curr.strftime('%Y-%m-%d')
        
        d_val = dust_tot.get(date_str, -999.0)
        oc_val = oc_tot.get(date_str, -999.0)
        bc_val = bc_tot.get(date_str, -999.0)
        ss_val = ss_tot.get(date_str, -999.0)
        so4_val = so4_tot.get(date_str, -999.0)
        t_val = t2m.get(date_str, -999.0)
        ws_val = ws10m.get(date_str, -999.0)
        rho_val = rhoa.get(date_str, -999.0)
        aod_val = aod55.get(date_str, -999.0)

        if d_val != -999.0:
            AIRDENS = rho_val if rho_val != -999.0 else 1.2
            
            SO4 = (so4_val if so4_val != -999.0 else 0.0) / AIRDENS
            BCPHOBIC = (bc_val if bc_val != -999.0 else 0.0) * 0.5 / AIRDENS
            BCPHILIC = (bc_val if bc_val != -999.0 else 0.0) * 0.5 / AIRDENS
            OCPHOBIC = (oc_val if oc_val != -999.0 else 0.0) * 0.5 / AIRDENS
            OCPHILIC = (oc_val if oc_val != -999.0 else 0.0) * 0.5 / AIRDENS
            
            d_tot = (d_val if d_val != -999.0 else 0.0) / AIRDENS
            DU001 = d_tot * 0.20
            DU002 = d_tot * 0.30
            DU003 = d_tot * 0.30
            DU004 = d_tot * 0.20
            
            s_tot = (ss_val if ss_val != -999.0 else 0.0) / AIRDENS
            SS001 = s_tot * 0.25
            SS002 = s_tot * 0.25
            SS003 = s_tot * 0.25
            SS004 = s_tot * 0.25
            
            # Exact formula calculations for PM1 and PM10
            PM1_calc = (1.375 * SO4 + BCPHOBIC + BCPHILIC + OCPHOBIC + OCPHILIC + 0.7 * DU001 + SS001 + SS002) * AIRDENS * 1e9
            PM10_calc = (1.375 * SO4 + BCPHOBIC + BCPHILIC + OCPHOBIC + OCPHILIC + DU001 + DU002 + DU003 + 0.74 * DU004 + SS001 + SS002 + SS003 + SS004) * AIRDENS * 1e9
            
            pm25_total = (d_val if d_val != -999.0 else 0.0) + (oc_val if oc_val != -999.0 else 0.0) + (bc_val if bc_val != -999.0 else 0.0) + (ss_val if ss_val != -999.0 else 0.0) + (so4_val if so4_val != -999.0 else 0.0) * 1.375
            pm25_ug = pm25_total * 1e9

            history.append({
                "date": formatted_date,
                "aod_55": round(aod_val, 2) if aod_val != -999.0 else 0.0,
                "pm1": round(PM1_calc, 2),
                "pm25_total": round(pm25_ug, 2),
                "pm10": round(PM10_calc, 2),
                "dust_pm25": round((d_val if d_val != -999.0 else 0.0) * 1e9, 2),
                "oc_mass": round((oc_val if oc_val != -999.0 else 0.0) * 1e9, 2),
                "bc_mass": round((bc_val if bc_val != -999.0 else 0.0) * 1e9, 2),
                "ss_pm25": round((ss_val if ss_val != -999.0 else 0.0) * 1e9, 2),
                "so4_mass": round((so4_val if so4_val != -999.0 else 0.0) * 1e9 * 1.375, 2),
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
    print(f"Successfully generated Jodhpur MERRA-2 dataset with {len(history)} records including PM1 and PM10.")

if __name__ == "__main__":
    main()
