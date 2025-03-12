import re
from difflib import get_close_matches

def get_city_id(city_name, file_path='city_ids.dat') -> int:
    """
    Find the best match for a city name and return its ID from the city_id.dat file.
    
    Parameters:
    - city_name (str): The city name to search for.
    - file_path (str): The path to the file containing city names and IDs.
    
    Returns:
    - int: (city_id) if a match is found, else raise an error.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    city_data = {}
    for line in lines:
        match = re.match(r'(.+):\s*(\d+)', line.strip())
        if match:
            city, city_id = match.groups()
            city_data[city.strip()] = int(city_id.strip())
    city_names = list(city_data.keys())
    best_match = get_close_matches(city_name, city_names, n=1, cutoff=0.3)
    
    if best_match:
        matched_city = best_match[0]
        city_id = city_data[matched_city]
        return city_id
    raise KeyError(f"ERROR: No such city '{city_name}' in file {file_path}.\n"
        "Please look up the city name on bbc.com/weather and update your .dat file.")


def get_weather_emoji(description: str) -> str:
    description = description.lower()
    if re.search(r'\bsun\w*\b', description) and re.search(r'\bcloud\w*\b', description):
        return "🌤"
    elif re.search(r'\bcloud\w*\b', description) and re.search(r'\brain\w*\b', description):
        return "⛆"
    elif re.search(r'\bthunder\b|\blightning\b', description) and re.search(r'\brain\b|\bstorm\b', description):
        return "⛈"
    elif re.search(r'\bthunder\b|\blightning\b', description):
        return "🌩"
    elif re.search(r'\bsnow\b', description):
        return "❄"
    elif re.search(r'\bmist\b|\bfog\b', description):
        return "🌫"
    elif re.search(r'\bcloud\w*\b', description):
        return '☁'
    elif re.search(r'\brain\b', description) or re.search(r'\bdrizzle\b', description):
        return '⛆'
    elif re.search(r'\bsleet\b', description):
        return '❅'
    elif re.search(r'\bsun\w*\b|\bclear\b', description):
        return '☀'
    return "?"


