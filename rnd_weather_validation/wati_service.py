import requests


def send_template_message(
    base_url: str,
    api_key: str,
    template_name: str,
    phone_number: str,
    parameters: list,
):
    """
    Send WhatsApp template message via WATI.
    """

    url = f"{base_url}" f"/api/v1/sendTemplateMessage" f"?whatsappNumber={phone_number}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "template_name": template_name,
        "broadcast_name": ("rnd_weather_validation"),
        "parameters": [
            {
                "name": str(index),
                "value": str(value),
            }
            for index, value in enumerate(
                parameters,
                start=1,
            )
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
    )

    response.raise_for_status()

    return response.json()
