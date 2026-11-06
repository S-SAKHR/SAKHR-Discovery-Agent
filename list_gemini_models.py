import requests

from config import GEMINI_API_KEY

url = "https://generativelanguage.googleapis.com/v1beta/models"

headers = {
    "x-goog-api-key": GEMINI_API_KEY
}

response = requests.get(
    url,
    headers=headers,
    timeout=(20, 60)
)

response.raise_for_status()

data = response.json()

print("\nAvailable Gemini models:\n")

for model in data.get("models", []):

    methods = model.get(
        "supportedGenerationMethods", []
    )

    if "generateContent" in methods:

        print("Model:", model["name"])
        print("Display name:", model.get("displayName"))
        print("-" * 40)
