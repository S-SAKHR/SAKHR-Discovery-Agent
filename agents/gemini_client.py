import requests

from config import GEMINI_API_KEY, GEMINI_MODEL


BASE_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
)


def generate_content(prompt, model=None, schema=None):

    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is missing.")

    selected_model = model or GEMINI_MODEL

    url = (
        f"{BASE_URL}{selected_model}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    if schema:
        payload["generationConfig"]["responseSchema"] = schema

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError(
            f"Gemini returned no candidates: {data}"
        )

    parts = candidates[0]["content"]["parts"]

    return "".join(
        part.get("text", "")
        for part in parts
    )
