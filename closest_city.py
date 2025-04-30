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

def get_city_coordinates(city_name, city_ids_file='city_ids.dat'):
    # try fetching coordinates from file (offline)
    with open(city_ids_file) as f:
        for line in f.readlines():
            if city_name.lower() == line.split(':')[0].lower():
                return float(line.split(':')[2].split(',')[0]),\
                       float(line.split(':')[2].split(',')[1])
    # else look them up
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
