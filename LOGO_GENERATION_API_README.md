# Logo Generation API for Project Kaarigar

This document explains the new Logo Generation API that creates AI-powered logos based on user conversation data and stores them in both Google Cloud Storage and Firestore.

## 🎯 Overview

The Logo Generation API provides endpoints to:
- Generate logos using Google's Imagen model
- Store logos in Google Cloud Storage
- Update user profiles with logo information in Firestore
- Retrieve existing logos for users

## 🚀 API Endpoints

### 1. Generate Logo
**POST** `/api/logo/generate`

Generates a logo based on conversation data and brand information.

**Request Body:**
```json
{
  "conversation_data": "User conversation transcript or interview data",
  "brand_name": "Optional brand name (will be extracted if not provided)",
  "language": "en" // Language code (en, hi, etc.)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Logo generated successfully",
  "logo_url": "https://storage.googleapis.com/bucket/path/to/logo.png",
  "brand_name": "Extracted or provided brand name",
  "logo_prompt": "AI-generated prompt used for logo creation",
  "logo_spec": {
    "brand_name": "Brand name",
    "final_prompt": "Logo generation prompt",
    "descriptors": ["list", "of", "descriptors"],
    "style_adjectives": ["minimal", "modern", "vector"],
    "color_palette": ["colors", "used"]
  }
}
```

### 2. Get User Logo
**GET** `/api/logo/get-logo`

Retrieves the current logo information for the authenticated user.

**Response:**
```json
{
  "success": true,
  "logo_info": {
    "logo_url": "https://storage.googleapis.com/bucket/path/to/logo.png",
    "brand_name": "Brand name",
    "logo_prompt": "Prompt used for generation",
    "logo_generated_at": "2025-01-22T16:30:00Z",
    "has_logo": true
  }
}
```

### 3. Health Check
**GET** `/api/logo/health`

Checks the health status of the logo generation service.

**Response:**
```json
{
  "status": "healthy",
  "service": "Logo Generation Service",
  "firestore_available": true,
  "storage_available": true,
  "gemini_available": true,
  "timestamp": "2025-01-22T16:30:00Z"
}
```

## 🔧 How It Works

### 1. Logo Generation Process
1. **Input Processing**: Takes conversation data and optional brand name
2. **Prompt Generation**: Uses Gemini AI to create an optimized logo prompt
3. **Image Generation**: Uses Google's Imagen model to generate the logo
4. **Storage**: Uploads logo to Google Cloud Storage
5. **Database Update**: Updates user profile in Firestore with logo information

### 2. Storage Structure
Logos are stored in Google Cloud Storage with the following structure:
```
all_in_one_bucket/
└── kaarigar/
    └── KR_USER1/
        └── logos/
            └── custom_logo_user1_1640995200.png
```

### 3. Database Updates
The API updates two collections in Firestore:

**Profiles Collection:**
```json
{
  "userId": "user1",
  "brandLogo": "https://storage.googleapis.com/.../logo.png",
  "brandName": "Brand Name",
  "logoPrompt": "Generated prompt",
  "logoGeneratedAt": "2025-01-22T16:30:00Z",
  "lastUpdated": "2025-01-22T16:30:00Z"
}
```

**Kaarigars Collection:**
```json
{
  "kaarigar_id": "KR_USER1",
  "user_id": "user1",
  "brandLogo": "https://storage.googleapis.com/.../logo.png",
  "brandName": "Brand Name",
  "logoPrompt": "Generated prompt",
  "logoGeneratedAt": "2025-01-22T16:30:00Z"
}
```

## 🛠️ Setup and Configuration

### Prerequisites
1. **Google Cloud Credentials**: Set up authentication
2. **Gemini API Key**: Configure for prompt generation
3. **Vertex AI Access**: For Imagen model usage
4. **Firestore Database**: For storing logo metadata
5. **Cloud Storage Bucket**: For storing logo images

### Environment Variables
```bash
# Required
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
GEMINI_API_KEY="your-gemini-api-key"

# Optional (with defaults)
GEMINI_MODEL_NAME="gemini-2.0-flash"
VERTEX_PROJECT="useful-figure-475210-g7"
VERTEX_LOCATION="us-central1"
IMAGEN_MODEL="imagen-4.0-generate-001"
```

### Dependencies
```bash
pip install google-cloud-firestore google-cloud-storage google-generativeai google-genai
```

## 📝 Usage Examples

### Frontend Integration
```javascript
// Generate logo
const generateLogo = async (conversationData, brandName) => {
  try {
    const response = await fetch('/api/logo/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
      body: JSON.stringify({
        conversation_data: conversationData,
        brand_name: brandName,
        language: 'en'
      })
    });
    
    const data = await response.json();
    if (data.success) {
      console.log('Logo generated:', data.logo_url);
      return data;
    }
  } catch (error) {
    console.error('Logo generation failed:', error);
  }
};

// Get existing logo
const getLogo = async () => {
  try {
    const response = await fetch('/api/logo/get-logo', {
      credentials: 'include'
    });
    
    const data = await response.json();
    if (data.success) {
      return data.logo_info;
    }
  } catch (error) {
    console.error('Failed to get logo:', error);
  }
};
```

### Python Client Example
```python
import requests

# Create session for authentication
session = requests.Session()

# Login first
login_data = {
    "email": "user@example.com",
    "password": "password"
}
session.post("http://localhost:5000/api/auth/login", json=login_data)

# Generate logo
logo_data = {
    "conversation_data": "I am a potter from Jaipur...",
    "brand_name": "Mitti Crafts",
    "language": "en"
}

response = session.post("http://localhost:5000/api/logo/generate", json=logo_data)
if response.status_code == 200:
    result = response.json()
    print(f"Logo URL: {result['logo_url']}")
```

## 🧪 Testing

Use the provided test script to verify the API:

```bash
python test_logo_generation.py
```

This will test:
- Health check endpoint
- Authentication
- Logo generation
- Logo retrieval

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure user is logged in
   - Check session cookies are being sent
   - Verify backend session configuration

2. **Logo Generation Fails**
   - Check Gemini API key is valid
   - Verify Vertex AI access for Imagen
   - Ensure conversation data is provided

3. **Storage Issues**
   - Verify Google Cloud Storage permissions
   - Check bucket exists and is accessible
   - Ensure service account has storage permissions

4. **Database Issues**
   - Check Firestore permissions
   - Verify user profile exists
   - Ensure proper user ID format

### Debug Mode
Enable debug logging by setting:
```python
app.config['DEBUG'] = True
```

## 📊 Performance Considerations

- **Logo Generation**: Typically takes 10-30 seconds
- **Storage Upload**: Usually completes in 1-3 seconds
- **Database Updates**: Near-instantaneous
- **Rate Limits**: Respect Google API rate limits

## 🔒 Security

- **Authentication**: Required for all endpoints
- **Session-based**: Uses Flask sessions for user identification
- **Input Validation**: Validates conversation data and parameters
- **Error Handling**: Graceful error responses without exposing internals

## 🚀 Future Enhancements

- **Multiple Logo Variants**: Generate multiple logo options
- **Logo Customization**: Allow users to request specific styles
- **Batch Processing**: Generate logos for multiple users
- **Logo History**: Track logo generation history
- **Integration**: Direct integration with frontend components

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all prerequisites are met
3. Test with the provided test script
4. Check backend logs for detailed error messages
