from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from typing import Tuple, List

def get_current_location() -> Tuple[int, int]:
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        loc = data['loc']
        latitude, longitude = map(float, loc.split(','))
        return (latitude, longitude)
    except Exception as e:
        return None

def get_city_coordinates(city_name):
    geolocator = Nominatim(user_agent="city_locator")
    location = geolocator.geocode(city_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None
            

def find_closest_city(cities: List[str]) -> Tuple[str, float]:
    current_location = get_current_location()
    print("Finding your closest city... this will take a several seconds")
    closest_city, min_distance = sorted(
        ((city, geodesic(current_location, get_city_coordinates(city)).kilometers) for city in cities),
        key=lambda x: x[1]
    )[0]
    print(f"Found {closest_city}")
    return closest_city, min_distance
