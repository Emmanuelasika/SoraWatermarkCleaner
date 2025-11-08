# Quick Test for RunPod Endpoint

## Your Endpoint
- **URL**: `https://hnizvlracjskan.api.runpod.ai`
- **API Key**: `YOUR_RUNPOD_API_KEY_HERE`

## Quick Test Commands

### 1. Test Ping Endpoint (Health Check)

**Windows PowerShell:**
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_RUNPOD_API_KEY_HERE"
    "Content-Type" = "application/json"
}
Invoke-RestMethod -Uri "https://hnizvlracjskan.api.runpod.ai/ping" -Method GET -Headers $headers
```

**Windows CMD:**
```cmd
curl -X GET "https://hnizvlracjskan.api.runpod.ai/ping" -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" -H "Content-Type: application/json"
```

**Linux/Mac:**
```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/ping" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{"status": "healthy"}
```

### 2. Test Root Endpoint

**Windows PowerShell:**
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_RUNPOD_API_KEY_HERE"
    "Content-Type" = "application/json"
}
Invoke-RestMethod -Uri "https://hnizvlracjskan.api.runpod.ai/" -Method GET -Headers $headers
```

**Windows CMD / Linux / Mac:**
```bash
curl -X GET "https://hnizvlracjskan.api.runpod.ai/" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

### 3. Open API Documentation in Browser

Just open this URL in your browser:
```
https://hnizvlracjskan.api.runpod.ai/docs
```

## What to Check

1. **If you get `{"status": "healthy"}`** → ✅ Your endpoint is working!
2. **If you get `400 Bad Request`** → The server might still be starting up (wait a few minutes)
3. **If you get `401 Unauthorized`** → Check your API key
4. **If you get `404 Not Found`** → Check the endpoint URL
5. **If you get connection errors** → Check RunPod dashboard to ensure workers are running

## Next Steps

1. Run the ping test command above
2. Check the response
3. If it works, try the `/docs` endpoint in your browser
4. If it doesn't work, check RunPod logs for errors

## Security Reminder

⚠️ **Important**: Your API key was shared in this conversation. If this was exposed publicly, please regenerate it in your RunPod dashboard to prevent unauthorized access.

