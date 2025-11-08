"""Check the status of the failed task"""
import httpx
import json

ENDPOINT_HOST = "https://hnizvlracjskan.api.runpod.ai"
API_KEY = "YOUR_RUNPOD_API_KEY_HERE"
TASK_ID = "3df8ec23-d4c1-4492-868a-d73d88440cd4"

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
        print()
        if result.get("error_message"):
            print(f"Error Message: {result['error_message']}")
        if result.get("retry_count") is not None:
            print(f"Retry Count: {result['retry_count']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

