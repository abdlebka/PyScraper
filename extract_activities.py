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
        Extract structured escape room activity information from the text below.

        # Input Text
        {text}

        # Output Format
        Provide a JSON array of objects. Each object should represent one escape room activity, and contain ONLY the following fields (include a field ONLY if the information is explicitly present in the text):

        -   **name**: The exact name of the activity.
        -   **description**: The FULL description of the activity, copied VERBATIM from the text. Do not summarize or rephrase.
        -   **duration**: The duration of the activity (e.g., "60 minutes").
        -   **difficulty**: The difficulty level of the activity.
        -   **location**: Location information, if available.
        -   **price**: Price information, if available.

        # Instructions

        1.  **EXTRACT EXACTLY**: Extract the information exactly as it appears in the text. Do not add any information that is not explicitly provided.
        2.  **VERBATIM DESCRIPTIONS**: For the "description" field, copy the ENTIRE description exactly as it is written in the text. Do not summarize, interpret, or add details. If there is no description, omit the field.
        3.  **OMIT MISSING FIELDS**: If a piece of information (e.g., price, difficulty) is not present in the text, do not include that field in the JSON object for that activity.
        4.  **NO INFERENCE**: Do not infer or assume any information. Only use information that is directly stated.
        5.  **AVOID HALLUCINATION**: Do not make up descriptions or details. If the description is not present, leave out the description field.
        6.  **JSON ONLY**: Your output MUST be valid JSON and contain ONLY the JSON array. Do not include any introductory phrases, explanations, or other text outside of the JSON.
        7.  **NO HASHTAGS**: Do not include records where the name or description starts with or contains hashtags (#).
        8.  **ACTUAL ACTIVITIES ONLY**: Only extract actual escape room activities. Do not include information about:
            - Event planning services 
            - Corporate events
            - Birthday parties
            - General description of escape games
            - Phone numbers or contact information
            - Job postings or recruitment
        9.  **STRICT EXTRACTION ONLY**: Only extract information that is explicitly stated in the input text. Do not fabricate or generate any descriptions or details.
        10. **HIGH CONFIDENCE MATCHES ONLY**: Only include an activity if you are highly confident that all information is directly from the text.

        # Example of INVALID records (DO NOT INCLUDE)

        - Names with hashtags:
        "name": "#Hacker, #SciFi, #Infiltration, #BeginnerFriendly, #HighTech Z Express",

        - Descriptions with hashtags:
        "description": "#Adventure, #Fantasy, #SpellCast, #Battle, #90mins, #MagesInTraining",

        - Event planning services:
        "name": "Birthday Parties",
        "description": "Our escape rooms are made for all ages. There are no special skills needed to have a great time."

        - Corporate events:
        "name": "Corporate Events",
        "description": "Choose Us for Unforgettable Team Building Adventures..."

        - General escape game descriptions:
        "name": "Escape Games",
        "description": "An escape game is a real-life experience where participants are locked in a room and must..."

        - Job-related activities:
        "name": "Bubble Tea Barista",
        "name": "Game Mastering",
        "name": "Escape Room Maintenance"

        # Example

        If the text contains:

        "The Lost Treasure Difficulty ★ ★ ★ ★ ★ 3/5 Max 9 players 60 min Outsmart rivals, find the hidden objects and claim the ruby skull treasure within 60 minutes."

        The JSON output should be:

        ```json
        [
          {{
            "name": "The Lost Treasure",
            "description": "Outsmart rivals, find the hidden objects and claim the ruby skull treasure within 60 minutes.",
            "duration": "60 min",
            "difficulty": "3/5"
          }}
        ]
        ```

        # WARNING: DO NOT HALLUCINATE
        If you're uncertain about any information, exclude it entirely. Never invent descriptions.
        Only extract activities that are clearly actual escape room experiences.
        If there's insufficient information to determine if something is an escape room activity, exclude it.
    """
    response = ollama.chat(model='mistral:7b-instruct', messages=[{"role": "user", "content": prompt}])
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

    is_first_activity = True  # Initialize the flag

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

                # Add all activities without checking for duplicates
                append_activity_to_file(activity, output_file, is_first_activity)
                is_first_activity = False
                print(f"Added activity: {activity.get('name', 'Unnamed activity')}")
    print(f"Extraction complete. Results saved to {output_file}")
