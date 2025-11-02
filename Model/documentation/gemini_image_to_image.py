from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="")

# Edit prompt - modify the existing diary image
prompt = (
    "add a mc donald logo to the image "
)

# Load the existing image to edit
print("Loading image for editing...")
image = Image.open(r"D:\projects\Anuj_Portfolio\portfolio_anuj_tadkase\src\assets\tom-riddle-diary-closed.png")
print(f"Original image size: {image.size}")

print("Editing image with Gemini...")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        max_output_tokens=1000
    )
)

print("Processing response...")
for part in response.candidates[0].content.parts:
    if part.text is not None:
        print("Text response:", part.text)
    elif part.inline_data is not None:
        print("Saving edited image...")
        edited_image = Image.open(BytesIO(part.inline_data.data))
        edited_image.save("edited_diary_magical.png")
        print("Edited image saved as edited_diary_magical.png")
        print(f"Edited image size: {edited_image.size}")
    else:
        print("No image data found in response")