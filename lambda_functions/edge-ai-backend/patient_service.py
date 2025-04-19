"""
Service module for patient-related operations
"""
import base64
import logging
from datetime import datetime
import json
from config import BUCKET_NAME
import s3_service
from exceptions import PatientServiceError, S3ServiceError

# Configure logging
logger = logging.getLogger(__name__)


def handle_patient_post(body, bucket_name):
    """Handle patient image upload"""
    # Extract image data and user_id
    image_data = body.get('image_data')  # Base64 encoded image
    user_id = body.get('user_id')
    confidence = body.get('confidence')

    logger.info(f"Processing patient image upload for user_id: {user_id}")

    # Validate the base64 data
    try:
        # Remove any potential header in the base64 string
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Decode image data
        image_binary = base64.b64decode(image_data)
    except Exception as e:
        logger.error(f"Error decoding base64 data: {str(e)}")
        raise PatientServiceError(f"Invalid base64 image data: {str(e)}")

    try:
        # Count existing images for this user to generate sequential image number
        response = s3_service.list_objects(bucket_name, f"uploads/{user_id}/")
        object_count = response.get('KeyCount', 0)
        image_num = object_count + 1

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{image_num}_{user_id}_{timestamp}.jpg"

        # Determine folder path based on confidence
        if confidence == 'high':
            folder = f"uploads/{user_id}/highconf/"
        elif confidence == 'low':
            folder = f"uploads/{user_id}/lowconf/"
        else:
            folder = f"uploads/{user_id}/no_conf/"

        # Upload to S3
        s3_path = folder + filename
        metadata = {
            'user_id': user_id,
            'timestamp': timestamp,
            'confidence': confidence
        }

        return s3_service.upload_file(image_binary, bucket_name, s3_path, "image/jpeg", metadata)
    except S3ServiceError as e:
        # Re-raise S3 errors without wrapping
        raise
    except Exception as e:
        logger.error(f"Error processing patient post: {str(e)}")
        raise PatientServiceError(f"Error processing patient image: {str(e)}")


def get_imgs_by_user_id(user_id):
    """Get all images for a specific user"""
    logger.info(f"Fetching images for user_id: {user_id}")

    try:
        # List objects in the bucket with the specified prefix
        response = s3_service.list_objects(BUCKET_NAME, f"uploads/{user_id}/")

        # Check if Contents exists
        if 'Contents' not in response:
            logger.info(f"No images found for user_id: {user_id}")
            return {}

        # Extract the object keys from the response
        object_keys = [obj['Key'] for obj in response.get('Contents', [])]

        # Generate presigned URLs for each object
        data = {
            'highconf': {},
            'lowconf': {},
            'verified': {}
        }

        for key in object_keys:
            # Skip directories
            if key.endswith('/'):
                continue

            if "highconf" in key:
                folder_type = "highconf"
            elif "lowconf" in key:
                folder_type = "lowconf"
            elif "verified" in key:
                folder_type = "verified"
            else:
                continue

            filename = key.split('/')[-1]
            url = s3_service.generate_presigned_url(BUCKET_NAME, key)

            if url:  # Only add if URL generation succeeded
                data[folder_type][filename] = {
                    "url": url,
                    "annotations": get_annotations_for_image(user_id, filename) if folder_type in ["highconf",
                                                                                                   "verified"] else []
                }

        return data
    except S3ServiceError as e:
        # Re-raise S3 errors without wrapping
        raise
    except Exception as e:
        logger.error(f"Error fetching images for user_id {user_id}: {str(e)}")
        raise PatientServiceError(f"Error fetching images: {str(e)}")


def get_annotations_for_image(user_id, filename):
    """Get annotations for a specific image"""
    try:
        # Check if there's an annotation file for this image
        annotation_key = f"annotations/{user_id}/{filename.replace('.jpg', '.json')}"

        response = s3_service.get_object(BUCKET_NAME, annotation_key)

        if response:
            try:
                annotation_data = json.loads(response['Body'].read().decode('utf-8'))
                return annotation_data
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing annotations JSON: {str(e)}")
                return []
            except Exception as e:
                logger.warning(f"Error reading annotations: {str(e)}")
                return []

        return []
    except S3ServiceError as e:
        # Log but return empty list as annotations are not critical
        logger.warning(f"S3 error retrieving annotations: {str(e)}")
        return []
    except Exception as e:
        logger.warning(f"Error retrieving annotations: {str(e)}")
        return []