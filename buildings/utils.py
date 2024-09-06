import environ
import requests


def get_weather_data(city_id):
    env = environ.Env()
    environ.Env.read_env()
    ow_api_key = env("OPENWEATHER_API_KEY")

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "id": city_id,
        "appid": ow_api_key,
        "units": "metric",  # For temperature in Celsius
        "lang": "az",  # Set language to Azerbaijani
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    return data
