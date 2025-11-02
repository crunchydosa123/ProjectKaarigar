import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GENAI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents="Explain how AI works ",
    config=types.GenerateContentConfig(
        max_output_tokens=400,
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)
print(response.text)