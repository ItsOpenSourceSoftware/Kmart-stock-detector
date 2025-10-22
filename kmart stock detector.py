import requests
import json
import time

# === Settings ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Referer": "https://www.kmart.com.au/",
}

URL = "https://api.kmart.com.au/gateway/graphql"

# === Ask for postcode ===
POSTCODE = input("Enter postcode: ").strip()

# === Read SKUs from text file ===
# Example file content (skus.txt):
# 65463499
# 73143895
# S168428
try:
    with open("skus.txt", "r") as f:
        skus = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("❌ Error: 'skus.txt' not found.")
    exit()

print(f"\nTracking {len(skus)} SKUs for postcode {POSTCODE}...\n")

# === Loop through SKUs ===
for SKU in skus:
    PAYLOAD = {
        "operationName": "getProductAvailability",
        "variables": {
            "input": {
                "country": "AU",
                "postcode": POSTCODE,
                "products": [
                    {
                        "keycode": SKU,
                        "quantity": 1,
                        "isNationalInventory": False,
                        "isClickAndCollectOnly": False,
                    }
                ],
                "fulfilmentMethods": ["HOME_DELIVERY", "CLICK_AND_COLLECT"],
                "amendNearestInStockCnc": True,
                "limit": 3,
            }
        },
        "query": """query getProductAvailability($input: ProductAvailabilityQueryInput!) {
          getProductAvailability(input: $input) {
            postcode
            country
            region
            availability {
              HOME_DELIVERY {
                keycode
                poolName
                stock { available }
              }
              CLICK_AND_COLLECT {
                keycode
                stock { totalAvailable }
                locations {
                  fulfilment {
                    locationId
                    stock { available }
                  }
                  location { locationId }
                }
              }
            }
          }
        }""",
    }

    print(f"=== Checking SKU {SKU} ===")

    try:
        response = requests.post(URL, headers=HEADERS, json=PAYLOAD)
        response.raise_for_status()
        json_data = response.json()
        availability = json_data["data"]["getProductAvailability"]["availability"]

        print(f"\nStock info for SKU {SKU} at postcode {POSTCODE}:\n")

        # Home Delivery
        print("=== Home Delivery ===")
        for hd in availability["HOME_DELIVERY"]:
            store = hd.get("poolName", "Unknown")
            available = hd["stock"]["available"]
            print(f"Store: {store} | Available: {available}")

        # Click & Collect
        print("\n=== Click & Collect ===")
        for cc in availability["CLICK_AND_COLLECT"]:
            total_available = cc["stock"]["totalAvailable"]
            print(f"Total available across locations: {total_available}")
            for loc in cc["locations"]:
                loc_id = loc["location"]["locationId"]
                available = loc["fulfilment"]["stock"]["available"]
                print(f"Location ID: {loc_id} | Available: {available}")

        print("\n------------------------------------------\n")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network/API error for SKU {SKU}: {e}\n")
        continue
    except Exception as e:
        print(f"⚠️ Unexpected error for SKU {SKU}: {e}\n")
        continue

    # optional: wait a bit between requests
    time.sleep(1)
