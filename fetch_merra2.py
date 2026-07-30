import requests
import json
import os
from datetime import datetime, timedelta

LAT = 26.2389
LON = 73.0243
DATA_FILE = 'data/jodhpur_merra2.json'

def main():
    # 1. Load existing data if available
    existing_history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = json.load(f)
                existing_history = content.get('history', [])
        except Exception as e:
            print(f"Could not parse existing file: {e}")

    # Create a set of already recorded dates ('YYYY-MM-DD')
    existing_dates = {item['date'] for item in existing_history}

    # 2. Determine target date range for 2026 up to current available reanalysis window
    start_date = datetime(2026, 1, 1)
    today = datetime.now()
    # Reanalysis datasets have a 3-4 week processing latency; cap recent requests safely
    end_date = min(today, datetime.now() - timedelta(days=5)) 

    # Generate all expected dates for 2026
    all_target_dates = []
    curr = start_date
    while curr <= end_date:
        all_target_dates.append(curr.strftime('%Y%m%d'))
        curr += timedelta(days=1)

    # Isolate missing dates that need to be fetched
    missing_dates = [d for d in all_target_dates if f"{d[0:4]}-{d[4:6]}-{d[6:8]}" not in existing_dates]

    if not missing_dates:
        print("No missing dates to fetch. Dataset is fully up to date.")
        return

    print(f"Found {len(missing_dates)} missing dates to backfill for 2026.")

    min_missing_str = min(missing_dates)
    max_missing_str = max(missing_dates)

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
    for date_str in missing_dates:
        aod_val = aod_series.get(date_str, -999.0)
        t2m_val = t2m_series.get(date_str, -999.0)
        ws_val = ws_series.get(date_str, -999.0)

        # Filter out NASA missing data fill values (-999.0)
        if aod_val != -999.0:
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            new_entries.append({
                "date": formatted_date,
                "aod_55": aod_val,
                "temperature_2m": t2m_val,
                "wind_speed_10m": ws_val
            })

    if not new_entries:
        print("No valid new data returned from API for the missing date range.")
        return

    # Combine existing history with new entries, eliminate duplicates, and sort chronologically
    combined = {item['date']: item for item in (existing_history + new_entries)}
    sorted_history = sorted(combined.values(), key=lambda x: x['date'])

    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": "Jodhpur (NASA POWER Reanalysis Grid)",
        "latest": sorted_history[-1],
        "history": sorted_history
    }

    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Successfully updated dataset. Total chronological records: {len(sorted_history)}")

if __name__ == "__main__":
    main()
