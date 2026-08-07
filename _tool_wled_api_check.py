import requests

WLED_URL = "http://192.168.178.160/json/state"  # Replace with your WLED IP

def check_wled():
    payload = {
        "on": True,
        "bri": 32,
        "seg": {"id": 0, "i": [[0, 255, 0]] * 60}  # Set all LEDs to green
    }
    try:
        response = requests.post(WLED_URL, json=payload)
        response.raise_for_status()
        print("WLED API call successful.")
        print("Response:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error communicating with WLED:", e)

check_wled()
