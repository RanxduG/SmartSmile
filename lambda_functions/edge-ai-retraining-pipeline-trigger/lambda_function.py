import json
import websocket
import boto3
import requests

def lambda_handler(event, context):
    # === Step 1: Check item count in S3 folder ===
    s3 = boto3.client('s3')
    bucket_name = "edge-ai-s3"
    txt_folder_prefix = 'training_data/new_data/txt_files/'

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=txt_folder_prefix)

    txt_file_count = 0
    for page in page_iterator:
        if 'Contents' in page:
            txt_file_count += len(page['Contents'])

    print(f"Found {txt_file_count} text files in {txt_folder_prefix}")

    # === Step 2: Skip retraining if not enough .txt files ===
    if txt_file_count <= 100:
        print("Not enough new text files. Skipping model retraining.")
        return {
            'statusCode': 200,
            'body': json.dumps('Skipped retraining: Not enough new data.')
        }

    # === Step 3: Trigger SageMaker Notebook for retraining ===
    sm_client = boto3.client('sagemaker')
    notebook_instance_name = 'Edge-AI-Model-Retraining'

    url = sm_client.create_presigned_notebook_instance_url(
        NotebookInstanceName=notebook_instance_name
    )['AuthorizedUrl']
    print(f"Notebook URL: {url}")

    # Extract host and protocol
    url_tokens = url.split('/')
    http_proto = url_tokens[0]
    http_hn = url_tokens[2].split('?')[0].split('#')[0]

    # Get session and cookies
    session = requests.Session()
    session.get(url)
    cookies = "; ".join(f"{key}={value}" for key, value in session.cookies.items())

    # WebSocket to trigger notebook run
    ws = websocket.create_connection(
        f"wss://{http_hn}/terminals/websocket/1",
        cookie=cookies,
        host=http_hn,
        origin=f"{http_proto}//{http_hn}"
    )

    ws.send("""[ "stdin", "jupyter nbconvert --execute --to notebook --inplace /home/ec2-user/SageMaker/Retrianing-Pipeline.ipynb --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=1500\\r" ]""")
    ws.close()

    return {
        'statusCode': 200,
        'body': json.dumps('Retraining triggered.')
    }
