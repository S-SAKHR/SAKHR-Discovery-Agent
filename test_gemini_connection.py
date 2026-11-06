import requests

from config import GEMINI_API_KEY, GEMINI_MODEL


url = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": GEMINI_API_KEY
}

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": 'Return exactly this JSON: {"status": "OK"}'
                }
            ]
        }
    ],
    "generationConfig": {
        "responseMimeType": "application/json",
        "maxOutputTokens": 32,
        "temperature": 0.1
    }
}

print("Connecting to Gemini...")
print("Model:", GEMINI_MODEL)

try:

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(20, 300)
    )

    print("HTTP status:", response.status_code)

    response.raise_for_status()

    print("\nGemini response:")
    print(response.json())

except requests.exceptions.Timeout:
    print("Gemini request timed out.")

except requests.exceptions.HTTPError as error:
    print("HTTP error:", error)
    print(response.text[:1000])

except requests.exceptions.RequestException as error:
    print("Connection error:", error)

