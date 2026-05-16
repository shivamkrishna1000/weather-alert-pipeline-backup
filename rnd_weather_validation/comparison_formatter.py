from datetime import datetime


def build_template_parameters(
    comparison_data,
):

    now = datetime.now()

    date = now.strftime("%d %B %Y")

    time = now.strftime("%I:%M %p").lstrip("0")

    weatherapi = comparison_data["weatherapi"]

    openweather = comparison_data["openweather"]

    def build_forecast_line(
        label,
        value,
        time,
        unit,
    ):

        return f"{value}{unit} at {time}"

    def build_rain_window(
        rain_window,
    ):

        if not rain_window:

            return "No significant rain expected"

        return f'{rain_window["start"]} - ' f'{rain_window["end"]}'

    return [
        date,
        time,
        # WeatherAPI Current
        weatherapi["current"]["temp"],
        weatherapi["current"]["feels_like"],
        weatherapi["current"]["humidity"],
        weatherapi["current"]["wind"],
        weatherapi["current"]["rain"],
        weatherapi["current"]["rain_probability"],
        # OpenWeather Current
        openweather["current"]["temp"],
        openweather["current"]["feels_like"],
        openweather["current"]["humidity"],
        openweather["current"]["wind"],
        openweather["current"]["rain"],
        openweather["current"]["rain_probability"],
        # WeatherAPI Forecast
        build_forecast_line(
            "Max Temp",
            weatherapi["forecast"]["max_temp"]["value"],
            weatherapi["forecast"]["max_temp"]["time"],
            "°C",
        ),
        build_forecast_line(
            "Min Temp",
            weatherapi["forecast"]["min_temp"]["value"],
            weatherapi["forecast"]["min_temp"]["time"],
            "°C",
        ),
        build_forecast_line(
            "Max Humidity",
            weatherapi["forecast"]["max_humidity"]["value"],
            weatherapi["forecast"]["max_humidity"]["time"],
            "%",
        ),
        build_forecast_line(
            "Max Wind",
            weatherapi["forecast"]["max_wind"]["value"],
            weatherapi["forecast"]["max_wind"]["time"],
            " km/h",
        ),
        build_forecast_line(
            "Highest Rain Probability",
            weatherapi["forecast"]["max_rain_probability"]["value"],
            weatherapi["forecast"]["max_rain_probability"]["time"],
            "%",
        ),
        build_rain_window(weatherapi["forecast"]["rain_window"]),
        # OpenWeather Forecast
        build_forecast_line(
            "Max Temp",
            openweather["forecast"]["max_temp"]["value"],
            openweather["forecast"]["max_temp"]["time"],
            "°C",
        ),
        build_forecast_line(
            "Min Temp",
            openweather["forecast"]["min_temp"]["value"],
            openweather["forecast"]["min_temp"]["time"],
            "°C",
        ),
        build_forecast_line(
            "Max Humidity",
            openweather["forecast"]["max_humidity"]["value"],
            openweather["forecast"]["max_humidity"]["time"],
            "%",
        ),
        build_forecast_line(
            "Max Wind",
            openweather["forecast"]["max_wind"]["value"],
            openweather["forecast"]["max_wind"]["time"],
            " km/h",
        ),
        build_forecast_line(
            "Highest Rain Probability",
            openweather["forecast"]["max_rain_probability"]["value"],
            openweather["forecast"]["max_rain_probability"]["time"],
            "%",
        ),
        build_rain_window(openweather["forecast"]["rain_window"]),
    ]
