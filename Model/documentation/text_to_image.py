from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyB39LHQGrzzwQPu2_ZpG7VENd-zLyQV7m4")

response = client.models.generate_images(
    model='imagen-4.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images= 4,
    )
)
for generated_image in response.generated_images:
  generated_image.image.show()