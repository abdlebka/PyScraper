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
    Extract activities ONLY from businesses that are activity providers (like archery, cooking classes, pottery, ziplining, VR arcades, game centers, tourism activities).
    IGNORE restaurants, retail stores, repair shops, or any business that doesn't offer participatory activities.

    For each activity provider, identify the specific activities they offer.
    Return a valid JSON array with fields: name, description.

    Format your entire response as valid JSON only, with no additional text or explanation.
    Use this exact format: [{{"name": "Activity Name", "description": "Activity description"}}, ...]

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


if __name__ == "__main__":
    with open("raw_text.json", "r", encoding="utf-8") as f:
        businesses = json.load(f)

    output_file = "activities.json"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[")  # Start JSON array

    first_entry = True  # To handle commas properly

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

                with open(output_file, "a", encoding="utf-8") as f:
                    if not first_entry:
                        f.write(",\n")  # Add a comma between entries
                    json.dump(activity, f, indent=4)
                    first_entry = False

    with open(output_file, "a", encoding="utf-8") as f:
        f.write("\n]")  # Close JSON array

    print("Extracted activities saved to activities.json")
