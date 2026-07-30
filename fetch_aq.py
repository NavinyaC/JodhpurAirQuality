import requests
import json
import os
from datetime import datetime
import pandas as pd

LAT = 26.2389
LON = 73.0243
DATA_FILE = 'data/jodhpur_aq.json'

def main():
    start_date = "2026-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch hourly PM2.5 from Open-Meteo Air Quality API
    aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={LAT}&longitude={LON}&start_date={start_date}&end_date={end_date}&hourly=pm25&timezone=auto"
    print("Fetching historical PM2.5 data from Open-Meteo...")
    aq_res = requests.get(aq_url).json()
    
    # Fetch hourly Temperature and Wind Speed from Open-Meteo Weather API
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&past_days=180&hourly=temperature_2m,wind_speed_10m&timezone=auto"
    print("Fetching historical weather data from Open-Meteo...")
    weather_res = requests.get(weather_url).json()
    
    hourly_times = aq_res.get('hourly', {}).get('time', [])
    pm25_vals = aq_res.get('hourly', {}).get('pm25', [])
    
    w_times = weather_res.get('hourly', {}).get('time', [])
    temp_vals = weather_res.get('hourly', {}).get('temperature_2m', [])
    ws_vals = weather_res.get('hourly', {}).get('wind_speed_10m', [])
    
    if not hourly_times:
        print("Error fetching data from API.")
        return
        
    df_aq = pd.DataFrame({'time': pd.to_datetime(hourly_times), 'pm25': pm25_vals})
    df_w = pd.DataFrame({'time': pd.to_datetime(w_times), 'temperature': temp_vals, 'wind_speed': ws_vals})
    
    # Merge and resample to daily averages
    df = pd.merge(df_aq, df_w, on='time', how='inner')
    df['date'] = df['time'].dt.strftime('%Y-%m-%d')
    
    daily_df = df.groupby('date')[['pm25', 'temperature', 'wind_speed']].mean().reset_index()
    daily_df = daily_df[daily_df['date'] >= start_date].sort_values('date')
    
    # Round values for clean JSON output
    daily_df = daily_df.round(2)
    
    history = daily_df.to_dict(orient='records')
    latest = history[-1] if history else {}
    
    output = {
        "last_automated_run": datetime.now().isoformat(),
        "location": "Jodhpur, India",
        "latest": latest,
        "history": history
    }
    
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"Successfully generated daily AQ dataset with {len(history)} records starting from 2026-01-01.")

if __name__ == "__main__":
    main()
