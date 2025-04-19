import json
import boto3
import requests
from config import LABEL_STUDIO_API_URL, LABEL_STUDIO_API_KEY

# Set this to the correct storage type and ID from Label Studio
STORAGE_TYPE = "s3"  # could be 's3', 'gcs', etc.
STORAGE_ID = 2  # update this if your S3 storage ID is different


def trigger_label_studio_storage_sync():
    headers = {
        "Authorization": f"Token {LABEL_STUDIO_API_KEY}",
        "Content-Type": "application/json"
    }

    sync_url = f"{LABEL_STUDIO_API_URL}/api/storages/{STORAGE_TYPE}/{STORAGE_ID}/sync"

    try:
        response = requests.post(sync_url, headers=headers)

        if response.status_code == 200:
            return {
                "message": "Label Studio storage sync triggered successfully.",
                "status": "success"
            }
        else:
            return {
                "message": f"Failed to trigger sync: {response.text}",
                "status": "error"
            }
    except Exception as e:
        return {
            "message": f"Error triggering storage sync: {str(e)}",
            "status": "error"
        }


def lambda_handler(event, context):
    response = trigger_label_studio_storage_sync()
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
