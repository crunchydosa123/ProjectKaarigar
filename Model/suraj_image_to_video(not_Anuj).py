import time
from google import genai
from google.genai.types import GenerateVideosConfig, Image
import sys # Import sys for better error logging

# Use Vertex AI instead of API key
client = genai.Client(
    vertexai=True,
    project="useful-figure-475210-g7",  # Your Google Cloud project ID
    location="us-central1"
)

# Define output location in your GCS bucket
output_gcs_uri = "gs://all_in_one_bucket/videos/"

print("🚀 Initializing video generation...")

try:
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt="dog runing on the rain in the forest",
        image=Image(
            gcs_uri="gs://all_in_one_bucket/images/pexels-photo-1108099.jpeg",
            mime_type="image/jpeg",
        ),
        config=GenerateVideosConfig(
            aspect_ratio="16:9",
            output_gcs_uri=output_gcs_uri,
        ),
    )

    print("🎬 Video generation started.")
    print(f"📋 Operation: {operation.name}")
    
    # --- THIS IS THE CORRECTED POLLING LOOP ---
    print("⏳ Waiting for operation to complete... (This may take a minute)")
    while not operation.done:
        print(f"⏳ Polling... Status: In progress")
        time.sleep(15)
        
        # Pass the entire 'operation' object to the get() method.
        # This will refresh the object with the latest status.
        operation = client.operations.get(operation)

    print("\n" + "="*70)
    
    # Check for errors on the completed operation
    if operation.error:
        print("❌ Video generation failed")
        print(f"❌ Error: {operation.error}")
    else:
        # Success! Access the result.
        video_uri = operation.result.generated_videos[0].video.uri
        print(f"✅ Video generated successfully!")
        print(f"🔗 Video URI: {video_uri}")
    
    print("="*70)

except Exception as e:
    # Print errors to stderr
    print(f"An unexpected error occurred: {e}", file=sys.stderr)
    print("="*70)