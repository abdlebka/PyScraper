import json
import ollama  # Assumes Mistral 7B is set up locally


def chunk_text(text, max_tokens=3000):
    """Splits text into smaller chunks within the token limit."""
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_tokens:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def extract_with_llm(text):
    """Uses a local LLM (Mistral 7B) to extract structured activity data."""
    print("Extracting structured activities with LLM...")
    prompt = f"""
    Extract ONLY genuine participatory activities that customers can book and engage in at this specific business location.

    ONLY include:
    - Real bookable experiences like escape rooms, adventure games, team challenges
    - Activities with clear game/experience names (e.g., "The Tomb: Raiders of the Sword")

    DO NOT include:
    - Business policies (like phone policies, booking requirements)
    - General service descriptions 
    - Duplicate activities with minor phrasing differences
    - Activities clearly located in other cities (not at this business location)
    - Business hours, deposits, or procedural information

    For each valid activity, extract:
    - name: The specific activity name without duration info (e.g., "The Tomb: Raiders" not "The Tomb: Raiders (60-min)")
    - description: Brief description of what participants actually do
    - duration: Time required (if mentioned)
    - difficulty: Difficulty level (if mentioned)

    Return a valid JSON array with this format:
    [
      {{
        "name": "Activity Name", 
        "description": "What participants actually do during this activity",
        "duration": "Duration if specified",
        "difficulty": "Difficulty if specified"
      }}
    ]

    Format your response as valid JSON only with no additional text or explanation.

    {text}
    """
    response = ollama.chat(model='mistral:latest', messages=[{"role": "user", "content": prompt}])
    print("LLM extraction completed.")

    content = response['message']['content']
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        json_pattern = r'\[.*\]'
        json_match = re.search(json_pattern, content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        print("Warning: Could not extract valid JSON from LLM response.")
        return []

def get_activity_key(activity):
    """Create a normalized key for activity deduplication that's more effective."""
    # Get the name and normalize it
    name = activity.get("name", "").lower().strip()

    # Many duplicates have the same name but slightly different descriptions
    # For activities like "The Tomb: Raiders of the Sword", we should just use the name
    # since these are clearly the same activity with different descriptions

    # Extract the main activity name (before any colon)
    main_name = name.split(':')[0].strip() if ':' in name else name

    # For activities with more specific names (after colon), use the full name
    if len(main_name) < 10 and ':' in name:
        return name

    # For general activities, just use the main part of the name
    # This handles cases where "The lab: Lockdown" and "The lab: Lockdown Bunker: AI's Martyrdom"
    # are variations of the same activity
    return main_name

def initialize_output_file(output_file):
    """Initialize the output file with an empty JSON array."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n]')


def append_activity_to_file(activity, output_file, is_first=False):
    """Append an activity to the JSON file while maintaining valid JSON structure."""
    with open(output_file, 'r+', encoding='utf-8') as f:
        # Move to right before the closing bracket
        f.seek(0, 2)  # Go to end of file
        pos = f.tell() - 2  # Position right before the closing bracket
        if pos < 0:  # If file is too small, start at beginning
            pos = 0
        f.seek(pos)

        # Add comma if not the first item
        if not is_first:
            f.write(',\n')
        else:
            f.write('\n')

        # Add the new activity and close the array
        json_activity = json.dumps(activity, ensure_ascii=False, indent=2)
        f.write(json_activity)
        f.write('\n]')


if __name__ == "__main__":
    with open("raw_text.json", "r", encoding="utf-8") as f:
        businesses = json.load(f)

    output_file = "activities.json"
    initialize_output_file(output_file)

    seen_activities = set()  # Track unique activities
    is_first_activity = True  # Track if this is the first activity to write

    for business in businesses:
        if not business or "text" not in business:
            continue  # Skip invalid or missing entries

        print(f"Processing business: {business.get('name', 'Unknown')}")

        chunks = chunk_text(business["text"])

        for chunk in chunks:
            activities = extract_with_llm(chunk)
            for activity in activities:
                activity["latitude"] = business.get("latitude")
                activity["longitude"] = business.get("longitude")

                # Check for duplicates before adding
                activity_key = get_activity_key(activity)
                if activity_key not in seen_activities:
                    seen_activities.add(activity_key)
                    append_activity_to_file(activity, output_file, is_first_activity)
                    is_first_activity = False
                    print(f"Added new activity: {activity['name']}")
                else:
                    print(f"Skipped duplicate activity: {activity['name']}")

    print(f"Extracted {len(seen_activities)} unique activities saved to {output_file}")