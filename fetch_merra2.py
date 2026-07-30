import requests
import json
import os
from datetime import datetime, timedelta

LAT = 26.2389
LON = 73.0243

def fetch_merra2_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=AOD_55,T2M,WS10M&community=AG&longitude={LON}&latitude={LAT}&start={start_str}&end={end_str}&format=JSON"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        aod_series = data['properties']['parameter']['AOD_55']
        t2m_series = data['properties']['parameter']['T2M']
        ws_series = data['properties']['parameter']['WS10M']
        
        # Filter out missing data (-999.0) and sort dates chronologically
        valid_dates = sorted([d for d, val in aod_series.items() if val != -999.0])
        
        # Take the last 30 available valid days for the time-series visualization
        chart_dates = valid_dates[-30:]
        
        timeline = []
        for date_str in chart_dates:
            # Convert 'YYYYMMDD' to 'YYYY-MM-DD' for cleaner parsing in JS
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            timeline.append({
                "date": formatted_date,
                "aod_55": aod_series[date_str],
                "temperature_2m": t2m_series[date_str],
                "wind_speed_10m": ws_series[date_str]
            })
            
        if timeline:
            output = {
                "last_automated_run": datetime.now().isoformat(),
                "location": "Jodhpur (NASA POWER MERRA-2 Grid)",
                "latest": timeline[-1],  # The most recent day's data
                "history": timeline      # The 30-day array for our charts
            }
            
            os.makedirs('data', exist_ok=True)
            with open('data/jodhpur_merra2.json', 'w') as f:
                json.dump(output, f, indent=4)
            print("Successfully updated 30-day MERRA-2 time-series data.")
        else:
            print("No valid data found.")
    else:
        print(f"API Request Failed: {response.status_code}")

if __name__ == "__main__":
    fetch_merra2_data()
