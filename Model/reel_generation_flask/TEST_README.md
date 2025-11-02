# Reel Generation API Test Suite

This comprehensive test suite tests all endpoints of the Reel Generation API deployed on Google Cloud Run.

## Cloud Run URL
```
https://reels-editor-298842469563.asia-south1.run.app/
```

## Test Coverage

The test suite covers all available endpoints:

### 1. Health Check
- **Endpoint**: `GET /api/health`
- **Purpose**: Verify API is running and accessible
- **Expected**: Returns status, storage info, and configuration

### 2. Reel Ideas Workflow
- **Generate Ideas**: `POST /api/reel-generation/ideas`
- **Refine Idea**: `POST /api/reel-generation/refine-idea`
- **Regenerate Ideas**: `POST /api/reel-generation/regenerate-ideas`
- **Generate Video Script**: `POST /api/reel-generation/generate-video-script`
- **Generate Video from Script**: `POST /api/reel-generation/generate-video`

### 3. Video Generation
- **Text to Video**: `POST /api/generate-video/text`
- **Images to Video**: `POST /api/generate-video/images`

### 4. Video Management
- **List All Videos**: `GET /api/videos`
- **List Cloud Videos**: `GET /api/cloud-videos`

### 5. Error Handling
- Tests various error scenarios and edge cases

## Running the Tests

### Option 1: Using Batch Script (Windows)
```bash
run_tests.bat
```

### Option 2: Manual Installation and Run
```bash
# Install dependencies
pip install -r test_requirements.txt

# Run tests
python pratham_test.py
```

## Test Features

- **Comprehensive Coverage**: Tests all 12+ endpoints
- **Error Handling**: Validates proper error responses
- **Timeout Management**: Handles long-running video generation
- **File Upload Testing**: Tests image upload functionality
- **Cloud Integration**: Verifies cloud storage operations
- **Detailed Logging**: Color-coded output with progress indicators

## Expected Test Duration

- **Quick Tests**: Health check, ideas generation (~30 seconds)
- **Video Generation Tests**: May take 5-10 minutes each
- **Total Suite**: 15-30 minutes depending on video generation time

## Test Results

The test suite provides:
- ✅ **Passed**: Test completed successfully
- ❌ **Failed**: Test encountered an error
- ⚠️ **Skipped**: Test skipped due to missing dependencies

## Notes

- Video generation tests may timeout if the API is under heavy load
- Image-based tests require test images in the specified path
- All tests use the production Cloud Run URL
- Tests include proper error handling and timeout management

## Troubleshooting

1. **Connection Errors**: Check if the Cloud Run URL is accessible
2. **Timeout Errors**: Video generation may take longer during peak usage
3. **Missing Images**: Some tests require test images in the specified path
4. **API Errors**: Check Cloud Run logs for detailed error information


