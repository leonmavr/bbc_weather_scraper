import requests
import json
from collections import namedtuple, defaultdict

WeatherReport = namedtuple(
    "WeatherReport",
    [
        "localDate",
        "timeslot",
        "weatherTypeText",
        "temperatureC",
        "precipitationProbabilityInPercent",
        "humidity",
        "windSpeedKph",
    ]
)


def request_hourly(url='https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/2925533'):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        forecasts = data.get("forecasts", [])
        weather_data = defaultdict(list)

        for iday, forecast in enumerate(forecasts):
            reports = forecast.get("detailed", {}).get("reports", [])
            
            for ihour, report in enumerate(reports):
                try:
                    localDate = report["localDate"]
                    timeslot = report["timeslot"]
                    weatherTypeText = report["weatherTypeText"]
                    temperatureC = report["temperatureC"]
                    precipitationProbabilityInPercent = report["precipitationProbabilityInPercent"]
                    humidity = report["humidity"]
                    windSpeedKph = report["windSpeedKph"]

                    weather_report = WeatherReport(
                        localDate=localDate,
                        timeslot=timeslot,
                        weatherTypeText=weatherTypeText,
                        temperatureC=temperatureC,
                        precipitationProbabilityInPercent=precipitationProbabilityInPercent,
                        humidity=humidity,
                        windSpeedKph=windSpeedKph
                    )

                    weather_data[localDate].append(weather_report)
                except KeyError:
                    pass
    else:
        print(f"Failed to fetch data. HTTP status code: {response.status_code}")
    return weather_data

def draw_bar(from_, to_, value, bar_width=20):
    block = '\u2588'
    border = '|'
    value = min(max(from_, value), to_)
    if to_ != from_:
        blocks_to_fill = int((value - from_) / (to_ - from_) * (bar_width - 2))
    else:
        blocks_to_fill = 0
    bar = border + block * blocks_to_fill + ' ' * (bar_width - 2 - blocks_to_fill) + border
    return bar

def fmt_weather_data(data, from_, to_):
    hour = data.timeslot
    temp = data.temperatureC
    temp_bar = draw_bar(from_, to_, temp)
    humid = data.humidity
    wspeed = data.windSpeedKph
    text = data.weatherTypeText
    ret = ' '.join([str(d) for d in [hour, temp_bar, temp, humid, wspeed, text]])
    return ret

if __name__ == '__main__':
    from datetime import datetime, timedelta
    weather_data = request_hourly()

    for i in range(14):
        target_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')

        if target_date in weather_data:
            print(f"Hourly weather data for {target_date}:")
            temp_min, temp_max = -30, 45
            for report in weather_data[target_date]:
                if report.temperatureC > temp_min:
                    temp_min = report.temperatureC
                if report.temperatureC < temp_max:
                    temp_max = report.temperatureC
            temp_min, temp_max = temp_max, temp_min
            for report in weather_data[target_date]:
                print(fmt_weather_data(report, temp_min, temp_max))
        else:
            print(f"No weather data available for {target_date}.")
