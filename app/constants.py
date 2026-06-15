"""
Central constants used across the application.

Includes:
- Field mappings for Zoho CRM data
- Allowed greenhouse status values
"""

ZOHO_FIELDS = {
    "id": "id",
    "name": "Name",
    "farmer": "Farmer",
    "phone_fields": ["Mobile", "Farmer_Mobile_No", "Alternate_Number_1"],
    "status": "Current_GH_Status",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "village": "Village",
    "taluk": "Taluk_Block_Mandal",
    "district": "District",
    "state": "State_UT1",
    "region": "Region",
    "cluster": "Clusterss",
}


ALLOWED_STATUSES = {
    "2. FS taken over and being used",
    "3. FS taken over and not being used",
    "4. Given up / don't know",
}


# =====================================================
# IMD WARNING CONSTANTS
# =====================================================

IMD_WARNING_CODE_DESCRIPTIONS = {
    1: "No Warning",
    2: "Heavy Rain",
    3: "Heavy Snow",
    4: "Thunderstorm & Lightning",
    5: "Hailstorm",
    6: "Dust Storm",
    7: "Dust Raising Winds",
    8: "Strong Surface Winds",
    9: "Heat Wave",
    10: "Hot Day",
    11: "Warm Night",
    12: "Cold Wave",
    13: "Cold Day",
    14: "Ground Frost",
    15: "Fog",
    16: "Very Heavy Rain",
    17: "Extremely Heavy Rain",
}


# Actual verified API mapping
# (NOT the mapping documented by IMD)
IMD_COLOR_MAPPING = {
    1: "Red",
    2: "Orange",
    3: "Yellow",
    4: "Green",
}


IMD_ALERT_EMOJIS = {
    "Red": "🔴",
    "Orange": "🟠",
    "Yellow": "🟡",
}


# Only these alert levels will be appended
# Yellow can be enabled later by adding it here
IMD_ENABLED_ALERT_LEVELS = {
    "Red",
    "Orange",
}


IMD_DAY_MAPPING = {
    "today": "Day_1",
    "tomorrow": "Day_2",
    "day3": "Day_3",
}
