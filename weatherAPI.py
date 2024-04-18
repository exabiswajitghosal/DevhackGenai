from datetime import datetime, timedelta
import requests


def get_weather_alerts():
    zone_code = 'CAC073'
    # Use current date
    today_date = datetime.now().strftime('%Y-%m-%d')
    iso_start_date = f"{today_date}T00:00:00Z"
    iso_end_date = f"{today_date}T23:59:59Z"
    url = f"https://api.weather.gov/alerts?zone={zone_code}&start={iso_start_date}&end={iso_end_date}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        alerts = data.get('features', [])
        if alerts:
            # Sort alerts based on effective time and get the latest one
            latest_alert = max(alerts, key=lambda x: x['properties']['effective'])
            return [latest_alert]
        else:
            return None
    else:
        return None


