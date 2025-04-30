## About

This is a quick and script to generate [BBC weather](bbc.com/weather) reports on the command
as weather cards. It uses web scraping for the daily forecasts and intercepts
the API calls for the hourly ones. You can navigate and explore each forecast with the keyboard.
Yes, the code is bad because I just wanted to quickly whip up something that works.

## Usage

### The script

Some minimal changes are required to calibrate it for you location. If you don't live in one of the 
existing cities at `city_ids.dat`, search your city at [BBC's page](bbc.com/weather) and append the name
and city ID from the URL, e.g. `https://www.bbc.com/weather/3169070 -> ID 3169070`  in the file, such as:

```
Rome: 3169070
```

If you run `scraper.py` without arguments, it will autodetect your location and geneerate the forecast of
closest city in `city_ids.dat`:

```bash
python scraper.py # <- auto detect city
```

This will take a few seconds to query the location of each city in `city_ids.dat` against the location 
of your city and return the closest one. You can also manually enter a city. This is faster as is skip 
quering geolocations and uses fuzzy matches so spelling mistakes are tolerated, e.g.:

```bash
python scraper London
python scraper.py nw yrk # <- New York
```

### City entries

Cities are listen in file `city_ids.dat`. Each line contains an entry consisting of:

```
city name: BBC ID: latitude, longitude
```
Latitude and longitude are optional but save time - otherwise the script looks them up.

## Features

- [x] 14-day forecast with terminal graphics and keyvoard controls
- [x] Daily weather including caching
- [x] Hourly weather including caching
- [x] Seamlessly switch between daily and hourly 
- [x] Fuzzy matching of input city
- [x] Closest city to your input 
- [x] Some predefined cities to find best match
- [x] ~~Caching of city geolocations in `city_ids.dat`~~ -> Replaced by listing coordinates
- [ ] Imperial units
- [ ] Automatically find each city's ID from BBC's API if possible

Any pull requests to implement the missing features are welcome!

## FAQs

**Q**: Why does the temperature range between the daily forecast and hourly forecast differ?

**A**: Because BBC measures the daily range from 6am current day to 6am next day. The API request
for the hourly weather measures exactly that day.


## Demo

<img src="https://github.com/leonmavr/bbc_weather_scraper/blob/master/assets/demo.gif" width="400"/>

## Donations

If you liked the project, feel free to buy me a coffe!

<a href="https://ko-fi.com/leomav">
  <img src="https://raw.githubusercontent.com/leonmavr/bbc_weather_scraper/refs/heads/master/assets/kofi_logo.png" alt="" style="width:300px; height:auto;">
</a>
