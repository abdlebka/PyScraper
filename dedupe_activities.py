import json
import difflib
from collections import defaultdict


def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def save_json_data(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def compute_similarity(str1, str2):
    if not str1 or not str2:
        return 0
    return difflib.SequenceMatcher(None, str1, str2).ratio()


def is_similar(item1, item2, name_threshold=0.8, desc_threshold=0.7):
    name_similarity = compute_similarity(item1.get('name', ''), item2.get('name', ''))
    desc_similarity = compute_similarity(item1.get('description', ''), item2.get('description', ''))

    # Higher weight on name similarity
    if name_similarity > name_threshold:
        return True
    # If names are somewhat similar, check descriptions
    elif name_similarity > 0.6 and desc_similarity > desc_threshold:
        return True
    return False


def merge_items(items):
    # Start with the item that has the most fields filled
    items.sort(key=lambda x: sum(1 for v in x.values() if v is not None and v != ''), reverse=True)

    merged = {}
    sources = set()

    # Merge all items
    for item in items:
        for key, value in item.items():
            if key == 'source_url':
                if value:
                    sources.add(value)
            elif key not in merged or merged[key] is None or merged[key] == '':
                merged[key] = value

    # Add all source URLs
    merged['source_urls'] = list(sources)
    if 'source_url' in merged:
        del merged['source_url']

    return merged


def deduplicate_activities(data):
    # Group potentially similar items
    name_groups = defaultdict(list)
    for item in data:
        if 'name' in item and item['name']:
            key = item['name'].lower().split()[0]  # Group by first word of name
            name_groups[key].append(item)

    # Process each group to find and merge similar items
    merged_items = []
    processed_indices = set()

    for key, group in name_groups.items():
        for i, item1 in enumerate(group):
            if i in processed_indices:
                continue

            similar_items = [item1]
            processed_indices.add(i)

            for j, item2 in enumerate(group):
                if j != i and j not in processed_indices and is_similar(item1, item2):
                    similar_items.append(item2)
                    processed_indices.add(j)

            merged_items.append(merge_items(similar_items))

    # Add any remaining items that weren't processed
    for item in data:
        found = False
        for group_items in name_groups.values():
            for i, group_item in enumerate(group_items):
                if i in processed_indices and group_item == item:
                    found = True
                    break
            if found:
                break

        if not found:
            item_copy = item.copy()
            if 'source_url' in item_copy:
                item_copy['source_urls'] = [item_copy.pop('source_url')]
            merged_items.append(item_copy)

    return merged_items


def main():
    try:
        # Load the data
        data = load_json_data('activities.json')

        # Deduplicate activities
        deduplicated_data = deduplicate_activities(data)

        # Save deduplicated data
        save_json_data(deduplicated_data, 'deduplicated_activities.json')

        print(f"Successfully deduplicated {len(data)} activities into {len(deduplicated_data)} unique activities.")
    except Exception as e:
        print(f"Error processing data: {e}")


if __name__ == "__main__":
    main()