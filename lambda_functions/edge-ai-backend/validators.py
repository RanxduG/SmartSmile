"""
Input validation functions
"""
import re
import base64
from exceptions import ValidationError
from config import VALID_CONFIDENCE_LEVELS, MAX_IMAGE_SIZE_MB


def validate_user_id(user_id):
    """Validate user_id format"""
    if not user_id:
        raise ValidationError("Missing user_id parameter")

    # Assuming user_id should be alphanumeric and minimum 3 characters
    if not re.match(r'^[a-zA-Z0-9_-]{3,}$', user_id):
        raise ValidationError("Invalid user_id format. Must be alphanumeric and at least 3 characters")

    return True


def validate_patient_post(data):
    """Validate patient post data"""
    # Check required fields
    required_fields = ['user_id', 'image_data', 'confidence']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    # Validate user_id
    validate_user_id(data['user_id'])

    # Validate confidence level
    if data['confidence'] not in VALID_CONFIDENCE_LEVELS:
        raise ValidationError(f"Invalid confidence level. Must be one of: {', '.join(VALID_CONFIDENCE_LEVELS)}")

    # Validate base64 image data
    image_data = data['image_data']

    # Remove any potential header in the base64 string
    if ',' in image_data:
        image_data = image_data.split(',')[1]

    try:
        # Try to decode the base64 data
        image_binary = base64.b64decode(image_data)

        # Check image size (max 5MB)
        image_size_mb = len(image_binary) / (1024 * 1024)
        if image_size_mb > MAX_IMAGE_SIZE_MB:
            raise ValidationError(f"Image size exceeds maximum allowed ({MAX_IMAGE_SIZE_MB}MB)")

    except Exception as e:
        raise ValidationError(f"Invalid base64 image data: {str(e)}")

    return True


def validate_doctor_request(data):
    """Validate doctor request data"""
    # Add validation for doctor specific requests
    return True