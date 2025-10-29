import requests
import base64
import json


# Apply edit
response = requests.post('https://ffmpeg-service-557742533869.asia-south1.run.app/edit', json={
    'video_url': 'https://storage.googleapis.com/all_in_one_bucket1/media/BRAND_123/processed/videos/generated/20251029_063551/script_video_9735d72f2a2793ca.mp4',
    'edit_prompt': 'make it black and white',
    'topic': 'my_project',
    'save_name': 'bw_video234'
})

result = response.json()
print(result)

# Save response to a JSON file
with open('edited_video_response2.json', 'w') as json_file:
    json.dump(result, json_file, indent=4)
