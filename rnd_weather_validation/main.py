import os

from app.config import get_database_url, load_environment
from app.database import get_connection
from rnd_weather_validation.comparison_formatter import build_template_parameters
from rnd_weather_validation.comparison_service import build_weather_comparison
from rnd_weather_validation.database import create_rnd_tables
from rnd_weather_validation.repository import insert_weather_snapshots
from rnd_weather_validation.wati_service import send_template_message

LOCATION_CONFIGS = [
    {
        "name": "RnD",
        "latitude": 17.02818,
        "longitude": 78.14797,
        "recipients": [
            "918605102018",
            "919966970290",
        ],
    },
    {
        "name": "Patna",
        "latitude": 25.609695,
        "longitude": 85.194362,
        "recipients": [
            "918709737257",
        ],
    },
]


def main():

    load_environment()

    RND_WATI_API_URL = os.getenv("RND_WATI_API_URL")

    RND_WATI_API_KEY = os.getenv("RND_WATI_API_KEY")

    RND_WATI_TEMPLATE_NAME = os.getenv("RND_WATI_TEMPLATE_NAME")

    database_url = get_database_url()

    connection = get_connection(database_url)

    try:

        create_rnd_tables(connection)

        for location in LOCATION_CONFIGS:

            latitude = location["latitude"]

            longitude = location["longitude"]

            comparison_data = build_weather_comparison(
                latitude=latitude,
                longitude=longitude,
            )

            insert_weather_snapshots(
                connection=connection,
                latitude=latitude,
                longitude=longitude,
                comparison_data=comparison_data,
            )

            template_parameters = build_template_parameters(comparison_data)

            print(f"\nSending messages for " f"{location['name']}\n")

            for recipient in location["recipients"]:

                send_template_message(
                    base_url=RND_WATI_API_URL,
                    api_key=RND_WATI_API_KEY,
                    template_name=(RND_WATI_TEMPLATE_NAME),
                    phone_number=recipient,
                    parameters=template_parameters,
                )

                print(f"Message sent to " f"{recipient}")

    finally:

        connection.close()


if __name__ == "__main__":

    main()
