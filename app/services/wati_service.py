import requests

from app.config import (
    get_wati_api_token,
    get_wati_base_url,
    get_wati_template_name,
    is_debug_mode,
)


def normalize_phone(phone: str) -> str:
    """
    Convert Indian mobile numbers to WATI format.

    Examples
    --------
    9876543210 -> 919876543210
    919876543210 -> 919876543210
    +919876543210 -> 919876543210
    """
    phone = phone.strip().replace(" ", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if len(phone) == 10:
        return f"91{phone}"

    return phone


def send_whatsapp_message(phone: str, farmer_name: str, sections: dict) -> bool:
    """
    Send WhatsApp template message via WATI.

    This function handles:
    - Debug mode (prints instead of sending)
    - API request construction
    - Error handling and response validation

    Parameters
    ----------
    phone : str
        Farmer phone number (must include country code, e.g., 91XXXXXXXXXX)
    farmer_name : str
        Name of the farmer (mapped to template variable {{1}})
    sections : dict
        Advisory sections mapped to WhatsApp template variables.
        {
            "greenhouse": str,
            "current": str,
            "today": str,
            "tomorrow": str,
            "day3": str,
        }
    Returns
    -------
    bool
        True if message sent successfully, False otherwise.
    """
    phone = normalize_phone(phone)

    # -------- DEBUG MODE --------
    if is_debug_mode():
        print("\n[DEBUG MODE] Message NOT sent")
        print(f"Phone: {phone}")
        print(f"Farmer: {farmer_name}")
        print("Message:")
        print(sections)
        print("-" * 50)
        return False  # Important: treat as NOT sent

    # -------- BUILD REQUEST --------
    base_url = get_wati_base_url()
    token = get_wati_api_token()
    template_name = get_wati_template_name()

    url = f"{base_url}/api/v1/sendTemplateMessage?whatsappNumber={phone}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "template_name": template_name,
        "broadcast_name": "weather_alert",
        "parameters": [
            {"name": "1", "value": farmer_name},
            {"name": "2", "value": sections["greenhouse"]},
            {"name": "3", "value": sections["current"]},
            {"name": "4", "value": sections["today"]},
            {"name": "5", "value": sections["tomorrow"]},
            {"name": "6", "value": sections["day3"]},
        ],
    }

    print("\n=== WATI PAYLOAD ===")
    print(payload)
    print("====================\n")

    # -------- API CALL --------
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("\n--- WATI DEBUG ---")
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        print("------------------\n")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"WATI API request failed for {phone}: {e}")
        return False

    # -------- RESPONSE CHECK --------
    try:
        data = response.json()
    except ValueError:
        print(f"Invalid JSON response from WATI for {phone}")
        return False

    if not data.get("result"):
        print(f"WATI send failed for {phone}: {data}")
        return False

    return True
