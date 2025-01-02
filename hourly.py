import requests
import json
from collections import namedtuple, defaultdict

# Define the namedtuple structure
WeatherReport = namedtuple(
    "WeatherReport",
    [
        "localDate",
        "timeslot",
        "weatherTypeText",
        "temperatureC",
        "precipitationProbabilityInPercent",
        "windSpeedKph",
    ]
)

url = "https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/2925533"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

# response.json()['forecasts'][iday]['detailed']['reports'][ihour]
for iday in range(14):
    for ihour in range(24):
        try:
            print(response.json()['forecasts'][iday]['detailed']['reports'][ihour]['localDate'],response.json()['forecasts'][iday]['detailed']['reports'][ihour]['weatherTypeText'])
        except:
            print('non existing key')

   
