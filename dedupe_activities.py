import json
from collections import defaultdict
from difflib import SequenceMatcher


def load_activities(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_activities(activities, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(activities, f, ensure_ascii=False, indent=2)


def text_similarity(a, b):
    """Calculate text similarity ratio between two strings."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()


def deduplicate_activities(activities):
    # First pass - group by name
    activities_by_name = defaultdict(list)
    for activity in activities:
        if "name" in activity and activity["name"]:
            # Skip entries with placeholder names
            if any(placeholder in activity["name"].lower() for placeholder in
                   ["extract missing info", "unknown activity", "not provided"]):
                continue
            activities_by_name[activity["name"]].append(activity)

    # Second pass - identify similar descriptions and merge groups
    merged_groups = []
    processed_names = set()

    for name, variants in activities_by_name.items():
        if name in processed_names:
            continue

        # Create a new group starting with this activity
        similar_group = variants
        processed_names.add(name)

        # Find other activities with similar descriptions
        for other_name, other_variants in activities_by_name.items():
            if other_name in processed_names or name == other_name:
                continue

            # Check similarity between descriptions
            desc1 = next((v.get("description") for v in variants if v.get("description")), "")
            desc2 = next((v.get("description") for v in other_variants if v.get("description")), "")

            if desc1 and desc2 and text_similarity(desc1, desc2) > 0.65:  # 85% similarity threshold
                similar_group.extend(other_variants)
                processed_names.add(other_name)

        merged_groups.append(similar_group)

    # Create final deduplication results
    deduplicated = []
    for group in merged_groups:
        # Use the most common name in the group
        name_counts = defaultdict(int)
        for item in group:
            name_counts[item["name"]] += 1
        best_name = max(name_counts.items(), key=lambda x: x[1])[0]

        merged = {
            "name": best_name,
            "latitude": group[0].get("latitude"),
            "longitude": group[0].get("longitude")
        }

        # Find the longest/most complete description
        descriptions = [v.get("description") for v in group if v.get("description")]
        if descriptions:
            merged["description"] = max(descriptions, key=lambda x: len(x) if x else 0)

        # Get most specific duration
        durations = [v.get("duration") for v in group if v.get("duration")]
        if durations:
            merged["duration"] = max(durations, key=lambda x: len(x) if x else 0)

        # Get the most detailed difficulty rating
        difficulties = [v.get("difficulty") for v in group if v.get("difficulty")]
        if difficulties:
            merged["difficulty"] = max(difficulties, key=lambda x: len(str(x)) if x else 0)

        # Get the most detailed location information
        locations = [v.get("location") for v in group if v.get("location")]
        if locations:
            merged["location"] = max(locations, key=lambda x: len(x) if x else 0)

        # Get price information if available
        prices = [v.get("price") for v in group if v.get("price")]
        if prices:
            merged["price"] = max(prices, key=lambda x: len(x) if x else 0)

        deduplicated.append(merged)

    return deduplicated


def main():
    activities = load_activities("activities.json")
    print(f"Loaded {len(activities)} activities")

    deduplicated = deduplicate_activities(activities)
    print(f"Deduplicated to {len(deduplicated)} activities")

    save_activities(deduplicated, "deduplicated_activities.json")
    print(f"Saved deduplicated activities to deduplicated_activities.json")


if __name__ == "__main__":
    main()