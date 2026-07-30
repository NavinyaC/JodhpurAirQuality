import requests
import json
import os
from datetime import datetime

TOKEN = '9c4f3048d9329490e2ecf04181ff705d071ada14'
CITY = 'jodhpur'
DATA_FILE = 'data/jodhpur_waqi.json'

def main():
    url = f"https://api.waqi.info/feed/{CITY}/?token={TOKEN}"
    print(f"Fetching live WAQI data for {CITY}...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Request Failed: {response.status_code}")
        return

    result = response.json()
    if result.get('status') != 'ok':
        print("WAQI API error:", result)
        return

    data = result.get('data', {})
    iaqi = data.get('iaqi', {})
    
    current_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    entry = {
        "date": current_date_str,
        "aqi": data.get('aqi', 0),
        "pm25": iaqi.get('pm25', {}).get('v', 0),
        "pm10": iaqi.get('pm10', {}).get('v', 0),
        "temperature": iaqi.get('t', {}).get('v', 0),
        "humidity": iaqi.get('h', {}).get('v', 0),
        "wind_speed": iaqi.get('w', {}).get('v', 0)
    }

    # Load existing history and purge legacy entries prior to 2026
    history = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            existing = json.load(f)
            raw_history = existing.get('history', [])
            history = [item for item in raw_history if item.get('date', '').startswith('2026')]

    # Prevent duplicate entries for the same day, updating with the latest fetch
    today_prefix = current_date_str[:10]
    existing_entry = next((item for item in history if item['date'].startswith(today_prefix)), None)
    
    if existing_entry:
        existing_entry.update(entry)
    else:
        history.append(entry)

    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": data.get('city', {}).get('name', 'Jodhpur, India'),
        "latest": entry,
        "history": history
    }

    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print("Successfully updated WAQI dataset with live 2026 data.")

if __name__ == "__main__":
    main()
