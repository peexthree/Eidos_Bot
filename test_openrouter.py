import os
import requests
import json

OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": OPENROUTER_MODEL,
    "messages": [
        {"role": "user", "content": "Hello"}
    ]
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
