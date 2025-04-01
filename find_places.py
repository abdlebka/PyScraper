import requests
import json


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


def get_places(api_key, location, keyword, radius=10000):
    """Finds businesses offering activities using Google Places API."""
    print(f"Fetching places related to '{keyword}' from Google Places API...")
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,  # Format: "latitude,longitude"
        "radius": radius,
        "keyword": keyword,
        # "type": "amusement_park|tourist_attraction|establishment",
        "key": api_key
    }
    response = requests.get(url, params=params)
    places = response.json().get("results", [])
    print(f"Found {len(places)} places.")

    businesses = []
    for place in places:
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

        businesses.append(business)

    with open("places.json", "w") as f:
        json.dump(businesses, f, indent=4)
    print(f"Saved {len(businesses)} places to places.json")


if __name__ == "__main__":
    api_key = "AIzaSyDfq7YrYVk_M6NnLNeJd5QQOKYyQlhFTFI"
    location = "43.6532,-79.3832"  # Example: toronto
    keyword = input("Enter activity to search for (e.g., archery, escape room): ")
    get_places(api_key, location, keyword, 10000)