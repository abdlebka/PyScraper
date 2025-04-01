import json


def merge_activities_with_places():
    """Merges place data into each activity without grouping activities"""
    print("Merging place data into activities...")

    # Load files
    with open("activities.json", "r") as f:
        activities = json.load(f)

    with open("places.json", "r") as f:
        places = json.load(f)

    # Create a place lookup dictionary by coordinates
    place_lookup = {}
    for place in places:
        key = f"{place['latitude']},{place['longitude']}"
        place_lookup[key] = place

    # Merge place data into each activity
    enriched_activities = []
    for activity in activities:
        key = f"{activity['latitude']},{activity['longitude']}"

        # Found matching place
        if key in place_lookup:
            place = place_lookup[key]

            # Create a new enriched activity with both activity and place data
            enriched_activity = {
                # Place information
                "place_name": place["name"],
                "place_id": place.get("place_id"),
                "types": place.get("types", []),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "website": place.get("website"),
                # Activity information
                "activity_name": activity["name"],
                "description": activity["description"],
                # Common fields
                "latitude": activity["latitude"],
                "longitude": activity["longitude"]
            }
            enriched_activities.append(enriched_activity)
        else:
            # If no matching business found, keep original activity
            enriched_activities.append(activity)

    # Save merged data
    with open("activities.json", "w") as f:
        json.dump(enriched_activities, f, indent=4)

    print(f"Enhanced {len(enriched_activities)} activities saved to activities.json")


if __name__ == "__main__":
    merge_activities_with_places()