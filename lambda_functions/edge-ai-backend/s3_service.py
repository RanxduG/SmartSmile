"""
Service module for handling S3 operations
"""
import boto3
import logging
from botocore.exceptions import ClientError
from config import BUCKET_NAME
from exceptions import S3ServiceError

# Configure logging
logger = logging.getLogger(__name__)


def get_s3_client():
    """Return a boto3 S3 client"""
    try:
        return boto3.client('s3')
    except Exception as e:
        logger.error(f"Failed to create S3 client: {str(e)}")
        raise S3ServiceError(f"Failed to create S3 client: {str(e)}")


def upload_file(file_binary, bucket_name, s3_path, content_type="image/jpeg", metadata=None):
    """Upload a file to S3"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Uploading file to S3: {bucket_name}/{s3_path}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_path,
            Body=file_binary,
            ContentType=content_type,
            Metadata=metadata or {}
        )
        logger.info(f"Successfully uploaded file to S3: {bucket_name}/{s3_path}")
        return s3_path
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        logger.error(f"S3 ClientError: {error_code} - {error_message}")
        raise S3ServiceError(f"S3 error: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise S3ServiceError(f"Error uploading to S3: {str(e)}")


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """Generate a presigned URL for an S3 object"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Generating presigned URL for: {bucket_name}/{object_key}")
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        # Don't raise an exception here as it's not critical - just return None
        return None
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return None


def list_objects(bucket_name, prefix):
    """List objects in S3 bucket with given prefix"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Listing objects in S3: {bucket_name}/{prefix}")
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return response
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        logger.error(f"S3 ClientError listing objects: {error_code} - {error_message}")
        raise S3ServiceError(f"S3 error listing objects: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error listing objects: {str(e)}")
        raise S3ServiceError(f"Error listing objects: {str(e)}")


def get_object(bucket_name, key):
    """Get an object from S3"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Getting object from S3: {bucket_name}/{key}")
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return response
    except s3_client.exceptions.NoSuchKey:
        logger.info(f"Object not found: {bucket_name}/{key}")
        return None
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'NoSuchKey':
            logger.info(f"Object not found: {bucket_name}/{key}")
            return None
        error_message = e.response.get('Error', {}).get('Message')
        logger.error(f"S3 ClientError getting object: {error_code} - {error_message}")
        raise S3ServiceError(f"S3 error getting object: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error getting object: {str(e)}")
        raise S3ServiceError(f"Error getting object: {str(e)}")


def copy_object(bucket_name, source_key, dest_key):
    """Copy an object within S3"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Copying object in S3 from {source_key} to {dest_key}")
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': source_key},
            Key=dest_key
        )
        logger.info(f"Successfully copied object in S3")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        logger.error(f"S3 ClientError copying object: {error_code} - {error_message}")
        raise S3ServiceError(f"S3 error copying object: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error copying object: {str(e)}")
        raise S3ServiceError(f"Error copying object: {str(e)}")


def delete_object(bucket_name, key):
    """Delete an object from S3"""
    s3_client = get_s3_client()

    try:
        logger.info(f"Deleting object from S3: {bucket_name}/{key}")
        s3_client.delete_object(Bucket=bucket_name, Key=key)
        logger.info(f"Successfully deleted object from S3")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        logger.error(f"S3 ClientError deleting object: {error_code} - {error_message}")
        raise S3ServiceError(f"S3 error deleting object: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error deleting object: {str(e)}")
        raise S3ServiceError(f"Error deleting object: {str(e)}")