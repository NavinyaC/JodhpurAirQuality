import requests
import json
import os
from datetime import datetime, timedelta

LAT = 26.2389
LON = 73.0243
DATA_FILE = 'data/jodhpur_merra2.json'

def main():
    existing_history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = json.load(f)
                existing_history = content.get('history', [])
        except Exception as e:
            print(f"Could not parse existing file: {e}")

    existing_dates = {item['date'] for item in existing_history}

    start_date = datetime(2026, 1, 1)
    today = datetime.now()
    end_date = min(today, datetime.now() - timedelta(days=5)) 

    all_target_dates = []
    curr = start_date
    while curr <= end_date:
        all_target_dates.append(curr.strftime('%Y%m%d'))
        curr += timedelta(days=1)

    missing_dates = [d for d in all_target_dates if f"{d[0:4]}-{d[4:6]}-{d[6:8]}" not in existing_dates]

    min_missing_str = min(missing_dates) if missing_dates else start_date.strftime('%Y%m%d')
    max_missing_str = max(missing_dates) if missing_dates else end_date.strftime('%Y%m%d')

    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=AOD_55,T2M,WS10M&community=AG&longitude={LON}&latitude={LAT}&start={min_missing_str}&end={max_missing_str}&format=JSON"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Request Failed: {response.status_code}")
        return

    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    aod_series = parameters.get('AOD_55', {})
    t2m_series = parameters.get('T2M', {})
    ws_series = parameters.get('WS10M', {})

    new_entries = []
    for date_str in all_target_dates:
        aod_val = aod_series.get(date_str, -999.0)
        t2m_val = t2m_series.get(date_str, -999.0)
        ws_val = ws_series.get(date_str, -999.0)

        if aod_val != -999.0:
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            # Conversion factor from kg/m³ to µg/m³ is 10⁹
            SCALE_KG_TO_UG = 1e9

            # Simulated / derived mass components using AOD proxy scaled to kg/m³ then converted to µg/m³
            dust_pm25 = max(0.0, (aod_val * 4.5e-8) * SCALE_KG_TO_UG)      # DUSMASS25
            oc_mass = max(0.0, (aod_val * 8.0e-9) * SCALE_KG_TO_UG)         # OCSMASS
            bc_mass = max(0.0, (aod_val * 3.5e-9) * SCALE_KG_TO_UG)         # BCSMASS
            ss_pm25 = max(0.0, (aod_val * 2.0e-9) * SCALE_KG_TO_UG)         # SSSMASS25
            so4_raw = max(0.0, (aod_val * 1.2e-8))                          # SO4SMASS in kg/m³
            so4_adjusted = so4_raw * (132.14 / 96.06) * SCALE_KG_TO_UG      # Converted to µg/m³
            
            pm25_total = dust_pm25 + oc_mass + bc_mass + ss_pm25 + so4_adjusted

            new_entries.append({
                "date": formatted_date,
                "aod_55": aod_val,
                "temperature_2m": t2m_val,
                "wind_speed_10m": ws_val,
                "dust_pm25": dust_pm25,
                "oc_mass": oc_mass,
                "bc_mass": bc_mass,
                "ss_pm25": ss_pm25,
                "so4_mass": so4_adjusted,
                "pm25_total": pm25_total
            })

    if not new_entries:
        print("No valid new data returned from API.")
        return

    sorted_history = sorted(new_entries, key=lambda x: x['date'])

    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": "Jodhpur (NASA MERRA-2 Collection Grid)",
        "latest": sorted_history[-1],
        "history": sorted_history
    }

    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Successfully updated dataset. Total records: {len(sorted_history)}")

if __name__ == "__main__":
    main()
