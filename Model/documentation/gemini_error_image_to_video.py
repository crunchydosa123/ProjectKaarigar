import time
from google import genai
from google.genai import types

client = genai.Client(api_key="")

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

print("Step 1: Generating image with Gemini...")
# Step 1: Generate an image with Gemini
image_response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
    config=types.GenerateContentConfig(
        max_output_tokens=1000
    )
)

print("Step 2: Processing image response...")
# Extract the generated image
generated_image = None
for part in image_response.candidates[0].content.parts:
    if part.inline_data is not None:
        # Create a proper image object for video generation
        generated_image = part.inline_data
        break

if generated_image is None:
    print("Error: No image generated")
    exit(1)

print("Step 3: Generating video with Veo 3.1...")
# Step 2: Generate video with Veo 3.1 using the image
try:
    # Use the exact format from the documentation
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        image=generated_image,
    )

    # Poll the operation status until the video is ready
    print("Step 4: Waiting for video generation...")
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video
    print("Step 5: Downloading video...")
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save("veo3_with_image_input.mp4")
    print("Generated video saved to veo3_with_image_input.mp4")
    
except Exception as e:
    print(f"Error generating video: {str(e)}")
    print("Note: Video generation may not be available in your region or with your API key")