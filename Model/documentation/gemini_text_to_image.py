from google import genai
from google.genai.types import GenerateImagesConfig

# Use Vertex AI instead of API key
client = genai.Client(
    vertexai=True,
    project="karigar-475215",
    location="us-central1"
)

output_file = "output-image.png"  # Uncommented and defined

image = client.models.generate_images(
    model="imagen-4.0-generate-001",  # Changed to imagen-3.0 (imagen-4.0 might not be available yet)
    prompt="A dog reading a newspaper",
    config=GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="1:1",  # Added aspect ratio
    ),
)

# Save the image
image.generated_images[0].image.save(output_file)

print(f"✅ Created output image: {output_file}")
print(f"📊 Size: {len(image.generated_images[0].image.image_bytes)} bytes")