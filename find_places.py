import requests
import json
import time


def get_place_details(api_key, place_id):
    """Gets detailed information for a place using Google Place Details API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website",
        "key": api_key
    }
    response = requests.get(url, params=params)
    details = response.json().get("result", {})
    return details.get("website")


def get_places(api_key, location, keyword, radius=10000, max_results=200):
    """Finds businesses offering activities using Google Places API."""
    print(f"Fetching places related to '{keyword}' from Google Places API...")
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,  # Format: "latitude,longitude"
        "radius": radius,
        "keyword": keyword,
        "key": api_key
    }

    businesses = []
    while len(businesses) < max_results:
        response = requests.get(url, params=params)
        places = response.json().get("results", [])
        print(f"Found {len(places)} places.")
        businesses.extend(places)

        next_page_token = response.json().get("next_page_token")
        if not next_page_token:
            break

        params["pagetoken"] = next_page_token
        time.sleep(2)  # Delay to ensure the next page token is valid

    businesses = businesses[:max_results]  # Limit to max_results

    detailed_businesses = []
    for place in businesses:
        business = {
            "name": place["name"],
            "place_id": place.get("place_id"),
            "latitude": place["geometry"]["location"]["lat"],
            "longitude": place["geometry"]["location"]["lng"],
            "types": place.get("types", []),
            "rating": place.get("rating"),
            "user_ratings_total": place.get("user_ratings_total")
        }

        # Get website via Place Details API
        if business["place_id"]:
            print(f"Fetching website for {business['name']}...")
            website = get_place_details(api_key, business["place_id"])
            if website:
                business["website"] = website

        detailed_businesses.append(business)

    # Check if places.json exists and load existing data
    existing_data = []
    try:
        with open("places.json", "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist or is invalid, starting with empty list
        pass

    # Check for duplicates and append new places
    existing_ids = {place.get("place_id") for place in existing_data}
    new_places = [place for place in detailed_businesses if place.get("place_id") not in existing_ids]

    # Combine existing and new data
    combined_data = existing_data + new_places

    with open("places.json", "w") as f:
        json.dump(combined_data, f, indent=4)

    print(f"Added {len(new_places)} new places to places.json (total: {len(combined_data)})")


if __name__ == "__main__":
    api_key = "AIzaSyDfq7YrYVk_M6NnLNeJd5QQOKYyQlhFTFI"
    location = "43.6532,-79.3832"  # Example: toronto
    keyword = input("Enter activity to search for (e.g., archery, escape room): ")
    get_places(api_key, location, keyword, 100000)