"""
Service module for doctor-related operations
"""
import logging
from config import BUCKET_NAME
import s3_service
from exceptions import DoctorServiceError, S3ServiceError

# Configure logging
logger = logging.getLogger(__name__)


def get_all_lowconf_images():
    """Get all low confidence images for doctor review"""
    logger.info("Fetching all low confidence images")

    try:
        data = {}

        # First, list all user directories
        response = s3_service.list_objects(BUCKET_NAME, "uploads/")

        # Check if CommonPrefixes exists (folders)
        if 'CommonPrefixes' not in response:
            logger.info("No user directories found")
            return data

        # Extract user directories from CommonPrefixes
        user_prefixes = [prefix.get('Prefix') for prefix in response.get('CommonPrefixes', [])]
        logger.info(f"Found {len(user_prefixes)} user directories")

        for user_prefix in user_prefixes:
            # Extract user_id from the prefix (format: "uploads/user_id/")
            user_id = user_prefix.split('/')[1]
            logger.info(f"Processing user directory: {user_id}")

            # List objects in this user's low-conf directory
            try:
                low_conf_response = s3_service.list_objects(
                    BUCKET_NAME,
                    f"{user_prefix}lowconf/"
                )

                # Check if there are any objects
                if 'Contents' in low_conf_response:
                    # Extract the object keys
                    object_keys = [obj['Key'] for obj in low_conf_response.get('Contents', [])]
                    img_data = {}

                    # Generate presigned URLs for each object
                    for key in object_keys:
                        if key.endswith('/'):  # Skip directories
                            continue

                        filename = key.split('/')[-1]
                        url = s3_service.generate_presigned_url(BUCKET_NAME, key)
                        if url:  # Only add if URL generation succeeded
                            img_data[filename] = url

                    # Only add the user to the results if they have low-conf images
                    if img_data:
                        data[user_id] = img_data
                        logger.info(f"Added {len(img_data)} low-confidence images for user {user_id}")
            except S3ServiceError as e:
                # Log the error but continue with other users
                logger.warning(f"Error fetching low-confidence images for user {user_id}: {str(e)}")
                continue

        logger.info(f"Found low-confidence images for {len(data)} users")
        return data
    except S3ServiceError as e:
        # Re-raise S3 errors without wrapping
        raise
    except Exception as e:
        logger.error(f"Error fetching low-confidence images: {str(e)}")
        raise DoctorServiceError(f"Error fetching low-confidence images: {str(e)}")