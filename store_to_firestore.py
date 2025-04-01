import json
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("your-firebase-key.json")  # Replace with actual Firebase key
firebase_admin.initialize_app(cred)
db = firestore.client()


def store_activities():
    """Reads activities.json and stores the data in Firestore."""
    print("Storing activities in Firestore...")
    with open("activities.json", "r") as f:
        activities = json.load(f)

    for activity in activities:
        db.collection("activities").add(activity)
        print(f"Stored activity: {activity['name']}")
    print("All activities saved to Firestore!")


if __name__ == "__main__":
    store_activities()
