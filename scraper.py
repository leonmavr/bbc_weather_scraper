from bs4 import BeautifulSoup
import wcwidth

from collections import namedtuple
import sys
import time
from difflib import get_close_matches
import re
import os
from datetime import datetime, timedelta
import requests
from typing import List

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

def print_weather_cards(weather_data, card_width=30, cards_per_row=4):
    """
    Print weather data as cards with box-drawing characters.
    ChatGPT wrote this function so fingers crossed everything works!
    """
    def pad_string(s, target_width):
        """Pad the string to the target display width."""
        current_width = sum(wcwidth.wcwidth(c) for c in s)
        padding_needed = target_width - current_width
        return s + " " * max(0, padding_needed)

    def truncate_and_pad(s, target_width):
        """Truncate the string and pad to the target display width."""
        def string_display_width(s):
            """Calculate the display width of a string, accounting for emojis and Unicode."""
            return sum(wcwidth.wcwidth(c) for c in s)
        current_width = 0
        result = []
        for c in s:
            char_width = wcwidth.wcwidth(c)
            if current_width + char_width > target_width:
                break
            result.append(c)
            current_width += char_width
        truncated = "".join(result)
        return pad_string(truncated, target_width)

    def create_card(weather):
        """Generate a single card as a string."""
        description = weather.descr
        #print(string_display_width(weather.description))
        temp_range = f"{weather.temp_low} to {weather.temp_high} °C".center(card_width - 2)

        card = (
            f"\u250c{'\u2500' * (card_width - 2)}\u2510\n"  # Top border
            f"\u2502{weather.date.center(card_width - 2)}\u2502\n"  # Date
            f"\u2502{description[:card_width-4].center(card_width - 2)}\u2502\n"  # Description
            f"\u2502{description[card_width-4:].center(card_width - 2)}\u2502\n"  # Description
            f"\u2502{temp_range}\u2502\n"  # Temp range
            f"\u2514{'\u2500' * (card_width - 2)}\u2518"  # Bottom border
        )
        return card

    rows = []
    for i in range(0, len(weather_data), cards_per_row):
        row = weather_data[i:i + cards_per_row]
        rows.append(row)

    for row in rows:
        card_lines = [create_card(weather).splitlines() for weather in row]
        for line_idx in range(len(card_lines[0])):
            print(" ".join(card[line_idx] for card in card_lines))
        print()  # Add spacing between rows

def is_file_outdated(file_path, max_age_hours=3) -> bool:
    if os.path.exists(file_path):
        file_age = time.time() - os.path.getmtime(file_path)
        return file_age > max_age_hours * 3600
    return True

def scrape(url='https://www.bbc.com/weather/2925533', use_emojis=True, verbose=False) -> List:
    ### Make a GET request and capture response, or use a cached file
    # Encapsulate the data in each day
    Weather = namedtuple('Weather', ['descr', 'date', 'temp_low', 'temp_high'])
    # Fetch or read HTML content
    location_id = url.split("/")[-1]  # Extract last part of the URL
    output_file = f"/tmp/{location_id}.html"
    if is_file_outdated(output_file):
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            if verbose:
                print(f"HTML content saved to {output_file}")
    elif verbose:
        print(f"Using cached file: {output_file}")
    with open(output_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    ### Parse the relevant tags for the next 2 weeks
    soup = BeautifulSoup(html_content, 'html.parser')
    daily_data = []
    ndays = 14 # that's how much BBC typically forecasts for
    for day in range(ndays):
        day_id = f"daylink-{day}"
        extract_numbers = lambda x: [int(xx) for xx in re.findall(r'\d+', x)]
        try:
            date = datetime.now() + timedelta(days=day)
            descr, temp_low, temp_high = 'N/A', 'N/A', 'N/A'
            # Everything is under the <a> with `day_id`
            a_tag = soup.find('a', id=day_id)
            if not a_tag:
                continue
            # There will be one short weather description
            weather_descriptions = a_tag.find('div', class_="wr-day__details__weather-type-description")
            if weather_descriptions:
                descr = weather_descriptions.text.strip()
            # Extract the temperatures - there will always be two spans (low and high)
            temperature_spans = a_tag.find_all('span', class_="wr-value--temperature--c")
            if temperature_spans:
                temp_high = extract_numbers(temperature_spans[0].text.strip())[0]
                temp_low = extract_numbers(temperature_spans[1].text.strip())[0]
                if temp_high < temp_low:
                    temp_low, temp_high = temp_high, temp_low
        except Exception as e:
            if verbose:
                print(f"Error processing '{day_id}': {e}")
            descr, temp_low, temp_high = 'N/A', 'N/A', 'N/A'
            descr = a_tag.find('div', class_='wr-day__details__weather-type-description').text.strip()
            # When it's late in the evening the <a> with id=dailink-0 is skipped
            temps = a_tag.find_all('span', class_='wr-value--temperature--c')
            if not temps:
                continue
            elif len(temps) == 1:
                temp_low = extract_numbers(temps[0].text.strip())[0]
            elif len(temps) == 2:
                temp_low = extract_numbers(temps[0].text.strip())[0]
                temp_high = extract_numbers(temps[1].text.strip())[1]
        if use_emojis:
            descr = f"{get_weather_emoji(descr)} {descr}"
        daily_data.append(Weather(descr, f"{date.strftime('%a, %d %b %Y')}", temp_low, temp_high))
    return daily_data


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

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("Usage: python <this_script.py> <your_city_name>")
    city_name = " ".join(sys.argv[1:])
    print(city_name)
    data = scrape(f"https://www.bbc.com/weather/{get_city_id(city_name)}")
    print_weather_cards(data)
