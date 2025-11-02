import os
from google import genai
from google.genai import types

with open(r'D:\projects\Anuj_Portfolio\portfolio_anuj_tadkase\src\assets\empty_marauders_map.jpg', 'rb') as f:
    image_bytes = f.read()

client = genai.Client(api_key=os.environ.get("GENAI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        ),
        'Caption this image.'
    ],
    config=types.GenerateContentConfig(
        max_output_tokens=1000,
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)

if response.candidates and response.candidates[0].content.parts:
    caption = response.candidates[0].content.parts[0].text
    print("Generated Caption:", caption)
else:
    print("No caption generated.")
    print(f"Finish reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")