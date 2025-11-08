# Testing RunPod Endpoint

## Your Endpoint Details

- **Endpoint URL**: `https://hnizvlracjskan.api.runpod.ai`
- **API Key**: `YOUR_RUNPOD_API_KEY_HERE`

⚠️ **SECURITY WARNING**: Your API key has been exposed. Please regenerate it in your RunPod dashboard if this was shared publicly.

## Quick Test with curl

### Test 1: Ping Endpoint (Health Check)

```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/ping" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{"status": "healthy"}
```

### Test 2: Root Endpoint

```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "running",
  "service": "SoraWatermarkCleaner",
  "endpoints": {
    "ping": "/ping",
    "submit_task": "/submit_remove_task",
    "get_results": "/get_results",
    "download": "/download/{task_id}",
    "docs": "/docs"
  }
}
```

### Test 3: API Documentation

Open in browser:
```
https://hnizvlracjskan.api.runpod.ai/docs
```

## Using the Test Script

### Python Test Script

1. Install dependencies:
```bash
pip install requests
```

2. Run the test script:
```bash
python test_runpod_endpoint.py
```

### Bash Test Script

1. Make it executable:
```bash
chmod +x test_runpod_simple.sh
```

2. Run it:
```bash
./test_runpod_simple.sh
```

## Testing Task Submission

### Submit a Video Task

```bash
curl -X POST "https://hnizvlracjskan.api.runpod.ai/submit_remove_task" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -F "video=@/path/to/your/video.mp4"
```

**Expected Response:**
```json
{
  "task_id": "uuid-here",
  "message": "Task submitted."
}
```

### Check Task Status

```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/get_results?remove_task_id=YOUR_TASK_ID" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "percentage": 50,
  "status": "PROCESSING",
  "download_url": "/download/YOUR_TASK_ID"
}
```

### Download Processed Video

```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/download/YOUR_TASK_ID" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -o output_video.mp4
```

## Troubleshooting

### Issue: 400 Bad Request

**Possible causes:**
- Server not fully started (models still loading)
- Incorrect endpoint URL
- Missing or invalid API key

**Solution:**
1. Check RunPod logs to see if server has started
2. Wait a few minutes for models to download on first startup
3. Verify the endpoint URL is correct

### Issue: 401 Unauthorized

**Possible causes:**
- Invalid or expired API key
- Missing Authorization header
- Incorrect Bearer token format

**Solution:**
1. Verify API key is correct in RunPod dashboard
2. Check that Authorization header is properly formatted: `Bearer YOUR_API_KEY`
3. Regenerate API key if necessary

### Issue: 404 Not Found

**Possible causes:**
- Incorrect endpoint path
- Server not running
- Worker not deployed

**Solution:**
1. Verify the endpoint URL is correct
2. Check RunPod dashboard to ensure worker is running
3. Check logs for server startup errors

### Issue: 500 Internal Server Error

**Possible causes:**
- Server error during processing
- Model loading failure
- Database connection issue

**Solution:**
1. Check RunPod logs for detailed error messages
2. Verify models are downloaded correctly
3. Check database initialization logs

## Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication failed
- **404 Not Found**: Endpoint or resource not found
- **500 Internal Server Error**: Server error

## Next Steps

1. **Test the /ping endpoint** to verify the server is running
2. **Check the /docs endpoint** to see the API documentation
3. **Submit a test video** to verify full functionality
4. **Monitor RunPod logs** for any errors

If you encounter any issues, check the RunPod dashboard logs for detailed error messages.

