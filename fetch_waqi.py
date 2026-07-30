import requests
import json
import os
from datetime import datetime

TOKEN = '9c4f3048d9329490e2ecf04181ff705d071ada14'
CITY = 'jodhpur'
DATA_FILE = 'data/jodhpur_waqi.json'

def main():
    url = f"https://api.waqi.info/feed/{CITY}/?token={TOKEN}"
    print(f"Fetching WAQI data for {CITY}...")
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
    
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    
    entry = {
        "date": current_date_str,
        "aqi": data.get('aqi', 0),
        "pm25": iaqi.get('pm25', {}).get('v', 0),
        "pm10": iaqi.get('pm10', {}).get('v', 0),
        "temperature": iaqi.get('t', {}).get('v', 0),
        "humidity": iaqi.get('h', {}).get('v', 0),
        "wind_speed": iaqi.get('w', {}).get('v', 0)
    }

    history = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            existing = json.load(f)
            history = existing.get('history', [])

    # Update today's entry if it already exists, otherwise append
    existing_entry = next((item for item in history if item['date'].startswith(current_date_str)), None)
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
    print(f"Successfully updated WAQI dataset. Total history records: {len(history)}")

if __name__ == "__main__":
    main()
