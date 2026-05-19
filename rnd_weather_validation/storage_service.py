def serialize_weather_data(data):

    if isinstance(data, dict):
        return {key: serialize_weather_data(value) for key, value in data.items()}

    if isinstance(data, list):
        return [serialize_weather_data(item) for item in data]

    if hasattr(data, "isoformat"):

        return data.isoformat()

    return data
