# 📺 Shared YouTube Channel Setup Guide

## Overview
All users on the platform now upload to the **SAME YouTube channel**. This means:
- ✅ One YouTube channel for the entire platform
- ✅ All users upload videos to this shared channel
- ✅ All users see the same channel statistics
- ✅ No need for individual YouTube authentication per user
- ✅ Simplified management and centralized content

## 🔧 How It Works

### Before (Old System)
- Each user had to authenticate with their own YouTube account
- Token stored per user: `youtube_tokens/user_{user_id}_token.pickle`
- Each user uploaded to their own channel
- Complex to manage multiple channels

### After (New System)
- **One shared token** for all users: `youtube_tokens/shared_channel_token.pickle`
- All users upload to the same YouTube channel
- No per-user authentication needed
- Simple centralized management

## 🚀 Setup Instructions

### Step 1: Set Up YouTube Channel
1. Create a dedicated YouTube channel for your platform
2. Or use an existing channel that you want all users to upload to
3. Make sure you have the login credentials for this YouTube account

### Step 2: Generate Shared Token

#### Option A: Using the Application (Recommended)
1. **Login to your backend** with any admin account
2. **Navigate to**: `/api/youtube/auth/start`
   - Local: `http://localhost:5000/api/youtube/auth/start`
   - Production: `https://backend-557742533869.asia-south1.run.app/api/youtube/auth/start`
3. **Login with the shared YouTube account** (the channel you want everyone to use)
4. **Grant permissions** when prompted
5. The token will be saved to: `backend/youtube_tokens/shared_channel_token.pickle`

#### Option B: Manual Token Creation (Advanced)
If you already have YouTube credentials, you can manually create the token file:

```python
# run_youtube_auth.py
import pickle
import os
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

CLIENT_SECRETS_FILE = "backend/client_secrets.json"
TOKEN_FILE = "backend/youtube_tokens/shared_channel_token.pickle"

# Create directory
os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)

# Run OAuth flow
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='http://localhost:8080'
)

auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
print(f'Please go to this URL: {auth_url}')

code = input('Enter the authorization code: ')
flow.fetch_token(code=code)
credentials = flow.credentials

# Save token
with open(TOKEN_FILE, 'wb') as token:
    pickle.dump(credentials, token)

print(f'✅ Token saved to: {TOKEN_FILE}')
```

### Step 3: Update Google OAuth Console (IMPORTANT!)

You need to add the redirect URIs to Google OAuth Console:

1. **Go to**: https://console.cloud.google.com/apis/credentials?project=karigar-475215
2. **Find your OAuth client**: `557742533869-lbcomd1qbekmg8jne7taigr747q7ifh6`
3. **Add these redirect URIs**:
   ```
   http://localhost:5000/api/youtube/auth/callback
   https://backend-557742533869.asia-south1.run.app/api/youtube/auth/callback
   ```
4. **Save changes**

### Step 4: Verify Setup

#### Check if token exists:
```powershell
# Windows
dir backend\youtube_tokens\shared_channel_token.pickle

# Linux/Mac
ls -la backend/youtube_tokens/shared_channel_token.pickle
```

#### Test the connection:
```bash
# Test auth status endpoint
curl http://localhost:5000/api/youtube/auth/status

# Should return:
{
  "success": true,
  "connected": true,
  "channel": {
    "id": "UCxxx...",
    "title": "Your Channel Name",
    "thumbnail": "https://...",
    "subscribers": 123,
    "videos": 45,
    "views": 12345,
    "shared": true
  }
}
```

## 📁 File Structure

```
backend/
├── youtube_tokens/
│   └── shared_channel_token.pickle  ← ALL users use this token
├── client_secrets.json              ← OAuth credentials
└── routes/
    └── youtube.py                   ← Updated to use shared token
```

## 🎯 Usage Flow

### For Users:
1. User logs into your platform
2. Goes to YouTube Shorts section
3. **No YouTube authentication needed!** ✨
4. User uploads video → Goes to shared channel
5. User sees all videos from shared channel

### For Admin:
1. Set up shared token once (one-time setup)
2. All users automatically use this token
3. Monitor the shared YouTube channel
4. Manage all videos in one place

## 🔐 Security Considerations

### Important Notes:
- ⚠️ **All users upload to the same channel** - make sure this is what you want
- ⚠️ **All users can see all videos** from the shared channel
- ⚠️ **Keep the token file secure** - it has full access to the YouTube channel
- ⚠️ **Add to .gitignore**: Never commit the token file to git

### Recommended .gitignore entry:
```gitignore
# YouTube tokens
backend/youtube_tokens/*.pickle
backend/youtube_tokens/shared_channel_token.pickle
```

### Token Security:
```powershell
# Set file permissions (Linux/Mac)
chmod 600 backend/youtube_tokens/shared_channel_token.pickle

# Or move to environment variable (advanced)
# Store token as base64 in environment variable
```

## 🔄 Token Refresh

The token will automatically refresh when it expires. The code handles this automatically:

```python
if credentials and credentials.expired and credentials.refresh_token:
    credentials.refresh(GoogleRequest())
    with open(token_file, "wb") as token:
        pickle.dump(credentials, token)
```

## 🚨 Troubleshooting

### Issue: "YouTube not connected"
**Solution**: 
1. Check if token file exists: `backend/youtube_tokens/shared_channel_token.pickle`
2. Re-run the authentication flow: `/api/youtube/auth/start`
3. Make sure you logged in with the correct YouTube account

### Issue: "redirect_uri_mismatch"
**Solution**:
1. Add redirect URIs to Google OAuth Console (see Step 3)
2. Make sure URIs are exactly correct (no trailing slashes)
3. Wait 5-10 minutes for changes to propagate

### Issue: Token expired or invalid
**Solution**:
1. Delete the old token: `del backend\youtube_tokens\shared_channel_token.pickle`
2. Re-authenticate: `/api/youtube/auth/start`
3. Login with the shared YouTube account

### Issue: Permission denied errors
**Solution**:
1. Make sure the YouTube account has granted all required permissions
2. Check that scopes in code match what was authorized
3. Re-authenticate with all permissions

## 📊 Monitoring

### Check token status:
```python
import pickle
import os

TOKEN_FILE = "backend/youtube_tokens/shared_channel_token.pickle"

if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)
        print(f"Token valid: {creds.valid}")
        print(f"Token expired: {creds.expired}")
        print(f"Has refresh token: {bool(creds.refresh_token)}")
else:
    print("Token file not found!")
```

### Monitor uploads:
- All uploads go to: `https://studio.youtube.com/channel/{channel_id}/videos`
- Check analytics: `/api/youtube/analytics/channel?days=30`
- List videos: `/api/youtube/videos`

## ✅ Deployment Checklist

- [ ] Created dedicated YouTube channel
- [ ] Generated shared token (`shared_channel_token.pickle`)
- [ ] Added redirect URIs to Google OAuth Console
- [ ] Verified token works locally
- [ ] Added token to `.gitignore`
- [ ] Deployed token to production server (copy file manually)
- [ ] Tested upload from production
- [ ] Set up monitoring for failed uploads

## 🎉 Benefits of Shared Channel

1. **Simplified Management**: One channel to manage, not hundreds
2. **No User Friction**: Users don't need to authenticate with YouTube
3. **Centralized Content**: All videos in one place for easy monitoring
4. **Brand Consistency**: All content under one YouTube channel/brand
5. **Analytics**: Easy to track all platform videos in one dashboard

## 📝 API Endpoints

All endpoints now use the shared token:

- `GET /api/youtube/auth/status` - Check if shared channel is connected
- `GET /api/youtube/auth/start` - Set up shared token (admin only)
- `POST /api/youtube/upload` - Upload to shared channel
- `GET /api/youtube/videos` - Get videos from shared channel
- `GET /api/youtube/analytics/channel` - Get shared channel analytics

## 🔮 Future Enhancements

Consider these if needed:
- Add video metadata to track which user uploaded which video
- Implement video approval workflow before publishing
- Add custom thumbnails with user watermarks
- Track per-user upload statistics in your database
- Implement upload quotas per user

---

**🎬 Your platform now uses a shared YouTube channel for all users!**

All users upload to the same channel, making management simple and centralized. Set up the shared token once, and you're done! 🚀
