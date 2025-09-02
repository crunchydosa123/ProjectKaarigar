import requests, os
API_KEY = os.getenv("ELEVENLABS_API_KEY") or "YOUR_ELEVENLABS_API_KEY"

resp = requests.get("https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": 'sk_e6ceead9d63aec1d4665dfac823b5160ce2240b3178bb080'})
voices = resp.json()
# voices is likely a list/dict containing voice objects
print(voices)
# pick a voice_id from voices['voices'][i]['voice_id'] or similar structure
