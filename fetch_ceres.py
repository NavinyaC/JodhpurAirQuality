import requests
import json
import os
from datetime import datetime, timedelta

LAT = 26.2389
LON = 73.0243
DATA_FILE = 'data/jodhpur_ceres.json'

def main():
    start_date = datetime(2026, 1, 1)
    today = datetime.now()
    end_date = min(today, datetime.now() - timedelta(days=5)) 

    all_target_dates = []
    curr = start_date
    while curr <= end_date:
        all_target_dates.append(curr.strftime('%Y%m%d'))
        curr += timedelta(days=1)

    min_str = start_date.strftime('%Y%m%d')
    max_str = end_date.strftime('%Y%m%d')

    # Querying CERES-backed parameters: AOD at 550nm, Cloud Amount (CLOUD_AMT), and All-Sky Surface Shortwave Downward Irradiance
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=AOD_55,CLOUD_AMT,ALLSKY_SFC_SW_DWN&community=AG&longitude={LON}&latitude={LAT}&start={min_str}&end={max_str}&format=JSON"
    
    print(f"Fetching NASA CERES data for Jodhpur ({min_str} to {max_str})...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Request Failed: {response.status_code}")
        return

    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    aod_series = parameters.get('AOD_55', {})
    cloud_series = parameters.get('CLOUD_AMT', {})
    sw_series = parameters.get('ALLSKY_SFC_SW_DWN', {})

    new_entries = []
    for date_str in all_target_dates:
        aod_val = aod_series.get(date_str, -999.0)
        cloud_val = cloud_series.get(date_str, -999.0)
        sw_val = sw_series.get(date_str, -999.0)

        if aod_val != -999.0:
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            new_entries.append({
                "date": formatted_date,
                "ceres_aod_55": aod_val,
                "cloud_fraction": cloud_val if cloud_val != -999.0 else 0.0,
                "solar_radiation": sw_val if sw_val != -999.0 else 0.0
            })

    if not new_entries:
        print("No valid data returned from API.")
        return

    sorted_history = sorted(new_entries, key=lambda x: x['date'])

    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": "Jodhpur (NASA CERES / POWER Grid)",
        "latest": sorted_history[-1],
        "history": sorted_history
    }

    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Successfully generated CERES dataset. Total records: {len(sorted_history)}")

if __name__ == "__main__":
    main()
