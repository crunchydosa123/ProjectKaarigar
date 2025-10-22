import requests
import base64

# Read video file and encode to base64
with open('Ghibli_Art_Style_Video_Generated (1).mp4', 'rb') as f:
    video_data = base64.b64encode(f.read()).decode('utf-8')

# Apply edit
response = requests.post('https://video-editor-298842469563.asia-south1.run.app/edit', json={
    'file': video_data,
    'edit_prompt': 'make it black and white',
    'topic': 'my_project',
    'save_name': 'bw_video'
})

result = response.json()
print(result)