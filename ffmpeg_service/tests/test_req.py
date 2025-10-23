import requests
import base64
import json

# Read video file and encode to base64
with open('Ghibli_Art_Style_Video_Generated (1).mp4', 'rb') as f:
    video_data = base64.b64encode(f.read()).decode('utf-8')

# Apply edit
response = requests.post('https://video-editor-298842469563.asia-south1.run.app/edit', json={
    'file': video_data,
    'edit_prompt': 'make the video vertical',
    'topic': 'my_project',
    'save_name': 'bw_video234'
})

result = response.json()
print(result)

# Save response to a JSON file
with open('edited_video_response2.json', 'w') as json_file:
    json.dump(result, json_file, indent=4)
