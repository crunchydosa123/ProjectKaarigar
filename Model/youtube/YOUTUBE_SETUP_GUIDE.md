# 📺 YouTube API Setup Guide for GCP

## Overview
This guide will help you set up YouTube Data API v3 and YouTube Analytics API in Google Cloud Platform for the Karigar project.

## 🎯 What You'll Get
- ✅ Upload videos and YouTube Shorts programmatically
- ✅ Fetch channel analytics (views, watch time, subscribers)
- ✅ Get video statistics and performance metrics
- ✅ List all your uploaded videos
- ✅ Track engagement (likes, comments, shares)

---

## 📋 Step 1: Enable YouTube APIs in GCP

### 1.1 Go to Google Cloud Console
```
https://console.cloud.google.com/
```

### 1.2 Select Your Project
- Project: **karigar-475215**
- If you don't see it, click the project dropdown at the top

### 1.3 Enable YouTube Data API v3
1. Navigate to **APIs & Services** → **Library**
2. Search for: `YouTube Data API v3`
3. Click on it
4. Click **ENABLE** button
5. Wait for it to enable (takes a few seconds)

### 1.4 Enable YouTube Analytics API
1. Still in **APIs & Services** → **Library**
2. Search for: `YouTube Analytics API`
3. Click on it
4. Click **ENABLE** button

---

## 🔐 Step 2: Create OAuth 2.0 Credentials

### 2.1 Configure OAuth Consent Screen (First Time Only)

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Click **CREATE**

**Fill in the form:**
- **App name**: `Karigar YouTube Manager`
- **User support email**: Your email address
- **App logo**: (Optional, skip for now)
- **App domain**: Leave blank for testing
- **Authorized domains**: Leave blank
- **Developer contact**: Your email address
- Click **SAVE AND CONTINUE**

**Scopes Screen:**
1. Click **ADD OR REMOVE SCOPES**
2. Search and select these scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - `https://www.googleapis.com/auth/youtube.readonly`
3. Click **UPDATE**
4. Click **SAVE AND CONTINUE**

**Test Users (Important!):**
1. Click **+ ADD USERS**
2. Add your Google account email (the one with YouTube channel)
3. Click **ADD**
4. Click **SAVE AND CONTINUE**
5. Click **BACK TO DASHBOARD**

### 2.2 Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** (top of page)
3. Select **OAuth client ID**

**Configure the client:**
- **Application type**: Desktop app
- **Name**: `YouTube Desktop Client`
- Click **CREATE**

### 2.3 Download Credentials

1. A popup will show your Client ID and Secret
2. Click **DOWNLOAD JSON** (or click the download icon on the credentials list)
3. Save the file
4. **Rename it to**: `client_secrets.json`
5. **Move it to**: `D:\Barclays\ProjectKaarigar\Model\youtube\`

---

## 🚀 Step 3: Install Required Python Packages

Open PowerShell in your project directory and run:

```powershell
cd D:\Barclays\ProjectKaarigar\Model\youtube
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

## 🧪 Step 4: Test the Setup

### 4.1 Test YouTube Analytics

```powershell
cd D:\Barclays\ProjectKaarigar\Model\youtube
python yt_analytics.py
```

**What happens:**
1. A browser window will open
2. You'll be asked to log in to your Google account
3. Select the account that has your YouTube channel
4. Click **Continue** when it says "Google hasn't verified this app"
5. Click **Continue** again
6. Allow all permissions requested
7. The script will fetch your channel analytics

### 4.2 Test YouTube Upload

```powershell
python yt_short.py
```

**What happens:**
1. Same authentication flow (if you didn't do it in 4.1)
2. Interactive prompts to upload a video
3. Choose Short or regular video
4. Provide video file path, title, description, etc.

---

## 📊 Available Scripts

### `yt_analytics.py` - Analytics Dashboard
**Features:**
- Channel info (subscribers, views, video count)
- Channel analytics (views, watch time, engagement)
- Recent videos list with statistics
- Individual video performance metrics
- Customizable date ranges (7, 30, 90 days)

**Usage:**
```powershell
python yt_analytics.py
```

### `yt_short.py` - Video Uploader
**Features:**
- Upload YouTube Shorts (vertical, <60s)
- Upload regular videos
- Set title, description, tags
- Choose category and privacy status
- Progress tracking
- Auto-adds #Shorts for Shorts

**Usage:**
```powershell
python yt_short.py
```

---

## 🔧 Troubleshooting

### Problem: "client_secrets.json not found"
**Solution:**
- Make sure you downloaded the OAuth client JSON
- Renamed it to exactly `client_secrets.json`
- Placed it in `D:\Barclays\ProjectKaarigar\Model\youtube\`

### Problem: "Access blocked: This app hasn't been verified"
**Solution:**
- Click **Advanced** (bottom left)
- Click **Go to Karigar YouTube Manager (unsafe)**
- This is safe - it's your own app in testing mode

### Problem: "No channel found for this account"
**Solution:**
- Make sure you're logging in with the Google account that has a YouTube channel
- Create a YouTube channel if you don't have one

### Problem: "quotaExceeded" error
**Solution:**
- YouTube Data API has daily quotas
- Default quota: 10,000 units/day
- Each video upload costs ~1,600 units
- Each analytics request costs ~200 units
- Wait until next day or request quota increase

### Problem: "insufficient permissions" in analytics
**Solution:**
- Delete `token_analytics.pickle` file
- Run the script again
- Make sure to approve ALL permissions when logging in

### Problem: Authentication window doesn't open
**Solution:**
- Check if a browser window opened in the background
- The script prints a URL - copy and paste it in your browser manually
- Make sure port 0 (random port) isn't blocked by firewall

---

## 📈 API Quotas & Limits

### YouTube Data API v3 Quota
- **Default**: 10,000 units/day
- **Video upload**: ~1,600 units
- **Video list**: ~100 units
- **Channel info**: ~3 units

### YouTube Analytics API Quota
- **Default**: 50,000 requests/day
- Much more generous than Data API
- Rarely hit limits unless making thousands of requests

### Request Quota Increase
If you need more quota:
1. Go to **APIs & Services** → **YouTube Data API v3**
2. Click **QUOTAS** tab
3. Click **ALL QUOTAS**
4. Select the quota you want to increase
5. Click **EDIT QUOTAS** (top right)
6. Fill out the form explaining your use case
7. Submit and wait for approval (1-3 business days)

---

## 🔒 Security Best Practices

### ✅ DO:
- Keep `client_secrets.json` private (already in .gitignore)
- Keep `token.pickle` and `token_analytics.pickle` private
- Use OAuth 2.0 (not API keys) for user-specific actions
- Add only necessary scopes

### ❌ DON'T:
- Commit `client_secrets.json` to GitHub
- Share your OAuth client secret publicly
- Request more scopes than needed
- Use API keys for upload/analytics (they don't work)

---

## 🎓 Next Steps

### For Production Deployment:
1. **Verify your app** in OAuth consent screen (required after 100 users)
2. **Request quota increase** if uploading many videos daily
3. **Implement error handling** for quota limits
4. **Add logging** for upload/analytics operations
5. **Consider service account** for server-side operations (limited features)

### For Analytics Integration:
- Save analytics data to Firestore for historical tracking
- Create API endpoint in Flask backend to serve analytics
- Build dashboard in React frontend to display metrics
- Schedule daily analytics fetch with cron/Cloud Scheduler

### For Automated Uploads:
- Integrate with reel_generator.py to auto-upload generated reels
- Add to backend API as `/api/youtube/upload` endpoint
- Store video IDs in Firestore for tracking
- Implement retry logic for failed uploads

---

## 📚 Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [YouTube Analytics API Documentation](https://developers.google.com/youtube/analytics)
- [OAuth 2.0 Setup Guide](https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps)
- [API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [YouTube API Support](https://support.google.com/youtube/answer/7365267)

---

## 📞 Support

If you run into issues:
1. Check the Troubleshooting section above
2. Verify all APIs are enabled in GCP
3. Check that test user is added in OAuth consent screen
4. Review Cloud Console Logs for API errors
5. Check YouTube API quotas in GCP console

---

**Last Updated**: January 2024
**Project**: Karigar
**GCP Project**: karigar-475215
