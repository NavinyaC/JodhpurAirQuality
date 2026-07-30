import requests
import json
import os
from datetime import datetime, timedelta

# Jodhpur Coordinates
LAT = 26.2389
LON = 73.0243

def fetch_merra2_data():
    # MERRA-2 has a latency of a few weeks. We fetch the last 60 days 
    # to ensure we capture the most recent processed data point.
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # NASA POWER API endpoint for MERRA-2 Agroclimatology parameters
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=AOD_55,T2M,WS10M&community=AG&longitude={LON}&latitude={LAT}&start={start_str}&end={end_str}&format=JSON"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract the time series dictionaries
        aod_series = data['properties']['parameter']['AOD_55']
        t2m_series = data['properties']['parameter']['T2M']
        ws_series = data['properties']['parameter']['WS10M']
        
        # NASA uses -999.0 as a fill value for missing/unprocessed data. 
        # Find the most recent date with valid AOD data.
        valid_dates = [date for date, val in aod_series.items() if val != -999.0]
        
        if valid_dates:
            latest_date = max(valid_dates) # Format is 'YYYYMMDD'
            
            output = {
                "last_automated_run": datetime.now().isoformat(),
                "merra2_date": latest_date,
                "aod_55": aod_series[latest_date],
                "temperature_2m": t2m_series[latest_date],
                "wind_speed_10m": ws_series[latest_date],
                "location": "Jodhpur (NASA POWER MERRA-2 Grid)"
            }
            
            # Save to the data folder
            os.makedirs('data', exist_ok=True)
            with open('data/jodhpur_merra2.json', 'w') as f:
                json.dump(output, f, indent=4)
            print(f"Successfully saved MERRA-2 data for {latest_date}.")
        else:
            print("No valid data found in the last 60 days.")
    else:
        print(f"API Request Failed: {response.status_code}")

if __name__ == "__main__":
    fetch_merra2_data()
