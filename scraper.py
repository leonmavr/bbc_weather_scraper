from bs4 import BeautifulSoup
import wcwidth
from pynput import keyboard
from hourly import fmt_day_hourly

from collections import namedtuple
import sys
import time
from difflib import get_close_matches
import re
import os
from datetime import datetime, timedelta
import requests
from typing import List
import threading
import time
import sys

# select which weather card is highlighted
icard=0
# whether to print the daily or hourly report
print_hourly = False
city_id = ''

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
    ChatGPT wrote some of this function so fingers crossed everything works!
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

    def create_card(weather, icard_current):
        """Generate a single card as a string."""
        #print(icard_current)
        description = weather.descr
        #print(string_display_width(weather.description))
        temp_range = f"{weather.temp_low} to {weather.temp_high} °C".center(card_width - 2)
        if icard_current != icard:
            card = (
                f"\u250c{'\u2500' * (card_width - 2)}\u2510\n"  # Top border
                f"\u2502{weather.date.center(card_width - 2)}\u2502\n"  # Date
                f"\u2502{description[:card_width-4].center(card_width - 2)}\u2502\n"  # Description
                f"\u2502{description[card_width-4:].center(card_width - 2)}\u2502\n"  # Description
                f"\u2502{temp_range}\u2502\n"  # Temp range
                f"\u2514{'\u2500' * (card_width - 2)}\u2518"  # Bottom border
            )
        else:
            card = (
                f"\u259B{'\u2580' * (card_width - 2)}\u259C\n"  # Top border
                f"\u258C{weather.date.center(card_width - 2)}\u2590\n"  # Date
                f"\u258C{description[:card_width-4].center(card_width - 2)}\u2590\n"  # Description
                f"\u258C{description[card_width-4:].center(card_width - 2)}\u2590\n"  # Description
                f"\u258C{temp_range}\u2590\n"  # Temp range
                f"\u2599{'\u2584'   * (card_width - 2)}\u259F"  # Bottom border
            )
        return card

    if not print_hourly:
        os.system("cls" if os.name == "nt" else "clear")  # Clear screen
    rows = []
    for i in range(0, len(weather_data), cards_per_row):
        row = weather_data[i:i + cards_per_row]
        rows.append(row)

    for irow, row in enumerate(rows):
        card_lines = [create_card(weather, irow*cards_per_row + icol).splitlines() for icol ,weather in enumerate(row)]
        for line_idx in range(len(card_lines[0])):
            if not print_hourly:
                print(" ".join(card[line_idx] for card in card_lines))
        if not print_hourly:
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
    for day in range(1,ndays):
        day_id = f"daylink-{day}"
        extract_numbers = lambda x: [int(xx) for xx in re.findall(r'\d+', x)]
        try:
            date = datetime.now() + timedelta(days=day-1)
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

def on_press(key):
    global icard
    global print_hourly
    try:
        if key.char == 'a':  # previous day 
            icard = (icard - 1) % 13
        elif key.char == 'd':  # next day 
            icard = (icard + 1) % 13
        elif key.char == 's':
            # TODO: cards per row instead of 4
            icard = (icard + 4) % 13 # next week
        elif key.char == 'w':
            # TODO: cards per row instead of 4
            icard = (icard - 4) % 13 # previous week
        elif key.char == 'f':
            print_hourly = not print_hourly
            if print_hourly:
                os.system("cls" if os.name == "nt" else "clear")
                print(fmt_day_hourly(city_id, days_from_now=icard))
    except AttributeError:
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("Usage: python <this_script.py> <your_city_name>")
    listener = keyboard.Listener(on_press=on_press)
    listener_thread = threading.Thread(target=listener.start, daemon=True)
    listener_thread.start()

    city_name = " ".join(sys.argv[1:])
    city_id = get_city_id(city_name)
    data = scrape(f"https://www.bbc.com/weather/{city_id}")
    while True:
        print_weather_cards(data)
        time.sleep(0.25)
