import json
import spacy
import ollama  # Assumes Mistral 7B is set up locally


def filter_activity_text(text):
    """Uses NLP and keyword matching to extract activity-related sentences."""
    print("Filtering activity-related sentences...")
    keywords = ["activities", "things to do", "experience", "book now", "adventure"]
    sentences = text.split('.')
    filtered = [s for s in sentences if any(k in s.lower() for k in keywords)]
    print(f"Extracted {len(filtered)} relevant sentences.")
    return ' '.join(filtered)


def extract_with_llm(filtered_text):
    """Uses a local LLM (like Mistral 7B) to structure activity data."""
    print("Extracting structured activities with LLM...")
    prompt = f"""
    Extract all activities from the following text and return them as a valid JSON array with fields: name, description.
    Format your entire response as valid JSON only, with no additional text or explanation.
    Use this exact format: [{{"name": "Activity Name", "description": "Activity description"}}, ...]
    {filtered_text}
    """
    response = ollama.chat(model='mistral:latest', messages=[{"role": "user", "content": prompt}])
    print("LLM extraction completed.")

    content = response['message']['content']

    # Try to find JSON in the response
    try:
        # First try to parse the whole response
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from the response using pattern matching
        import re
        json_pattern = r'\[.*\]'
        json_match = re.search(json_pattern, content, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If all else fails, return a fallback empty list
        print("Warning: Could not extract valid JSON from LLM response. Returning empty list.")
        print(f"Raw response: {content[:100]}...")  # Print first 100 chars for debugging
        return []

if __name__ == "__main__":
    with open("raw_text.json", "r") as f:
        businesses = json.load(f)

    all_activities = []
    for business in businesses:
        print(f"Processing business: {business['name']}")
        filtered_text = filter_activity_text(business["text"])
        activities = extract_with_llm(filtered_text)
        for activity in activities:
            activity["latitude"] = business["latitude"]
            activity["longitude"] = business["longitude"]
        all_activities.extend(activities)

    with open("activities.json", "w") as f:
        json.dump(all_activities, f, indent=4)
    print("Extracted activities saved to activities.json")
