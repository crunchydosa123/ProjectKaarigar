import json
import base64

# Load JSON from a file
with open("edited_video_response.json", "r") as f:
    response = json.load(f)

# Extract base64 video
b64_video = response["edited_video"]

# Decode base64 to bytes
video_bytes = base64.b64decode(b64_video)

# Save to file
with open("edited_video.mp4", "wb") as f:
    f.write(video_bytes)

print("Video saved as edited_video.mp4")
