"""Check task error details"""
import httpx
import json

ENDPOINT_HOST = "https://hnizvlracjskan.api.runpod.ai"
API_KEY = "YOUR_RUNPOD_API_KEY_HERE"
TASK_ID = "81426f3d-a488-4e59-ab92-9a698321e7c3"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

with httpx.Client(timeout=15.0) as client:
    response = client.get(
        f"{ENDPOINT_HOST}/get_results",
        headers=headers,
        params={"remove_task_id": TASK_ID}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("Task Status:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

