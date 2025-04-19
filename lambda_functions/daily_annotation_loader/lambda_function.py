import json
import boto3
import requests
import zipfile
import io
from config import BUCKET_NAME, LABEL_STUDIO_API_URL, LABEL_STUDIO_API_KEY

s3 = boto3.client('s3')


def get_annotated_images_from_label_studio():
    EXPORT_URL = "http://lablestudio4-env.eba-wjbzecp8.eu-north-1.elasticbeanstalk.com/api/projects/1/export"
    headers = {
        "Authorization": f"Token {LABEL_STUDIO_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        zip_export_url = "http://lablestudio4-env.eba-wjbzecp8.eu-north-1.elasticbeanstalk.com/api/projects/1/export?exportType=YOLO"
        zip_response = requests.get(zip_export_url, headers=headers)
        print(f"zip data: {zip_response}")
        if zip_response.status_code != 200:
            return {"message": f"Failed to download YOLO export: {zip_response.text}", "status": "error"}
        zip_file = zipfile.ZipFile(io.BytesIO(zip_response.content))
        # Step 3: Upload each .txt file to S3
        for file_info in zip_file.infolist():
            print(f"file_info: {file_info}")
            if file_info.filename.endswith('.txt') and file_info.filename.startswith('labels/'):
                content = zip_file.read(file_info.filename).decode("utf-8")
                # Infer user_id from the filename if structured like 'images/user1/filename.txt'
                parts = file_info.filename.split('/')

                last_part = parts[-1]
                print(f"last_part: {last_part}")
                filename = last_part.split('__')[-1]

                print(f"filename: {filename}")
                print(f"content: {content}")
                s3_key = f"training_data/new_data/txt_files/{filename}"
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=content,
                    ContentType='text/plain'
                )

                # copy original image from s3 uploads/userid/image to training data/new_data/images/
                user_id = filename.split('_')[1]
                image_name = filename.replace('.txt', '.jpg')
                source_key = f"uploads/{user_id}/under_review/{image_name}"
                verified_key = f"uploads/{user_id}/verified/{image_name}"
                dest_key = f"training_data/new_data/images/{image_name}"
                print(f"source_key: {source_key}")
                # copy image to verified folder
                s3.copy_object(Bucket=BUCKET_NAME, CopySource={'Bucket': BUCKET_NAME, 'Key': source_key}, Key=dest_key)
                s3.copy_object(Bucket=BUCKET_NAME, CopySource={'Bucket': BUCKET_NAME, 'Key': source_key},
                               Key=verified_key)
                s3.delete_object(Bucket=BUCKET_NAME, Key=source_key)

                # delete task from label studio
                task_id = filename.split('_')[0]
                print(f"task_id: {task_id}")
                task_url = f"{LABEL_STUDIO_API_URL}/tasks/{task_id}"
                print(f"task_url: {task_url}")
                task_response = requests.delete(task_url, headers=headers)
                print(f"task_response: {task_response}")
                if task_response.status_code != 204:
                    return {"message": f"Failed to delete task {task_id}: {task_response.text}", "status": "error"}
                    print(f"Failed to delete task {task_id}: {task_response.text}")

        return {"message": "Successfully processed annotations and YOLO labels", "status": "success"}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "status": "error"}


def lambda_handler(event, context):
    try:
        # Call the function directly
        result = get_annotated_images_from_label_studio()

        # Return the result
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error processing request: {str(e)}'
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }