import json
import logging
from config import BUCKET_NAME, LOG_LEVEL
from patient_service import handle_patient_post, get_imgs_by_user_id
from doctor_service import get_all_lowconf_images
from utils import build_response
from validators import validate_patient_post, validate_user_id
from exceptions import ValidationError, S3ServiceError, ServiceError

# Configure logging
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)


def lambda_handler(event, context):
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")

        http_method = event.get('httpMethod')

        # Handle GET requests with query parameters
        if http_method == 'GET' and 'queryStringParameters' in event and event['queryStringParameters']:
            query_params = event['queryStringParameters']
            logger.info(f"Query parameters: {json.dumps(query_params)}")

            user = query_params.get('user')

            if user == 'patient':
                try:
                    user_id = query_params.get('user_id')
                    validate_user_id(user_id)

                    user_img_data = get_imgs_by_user_id(user_id)
                    return build_response(200, {
                        'user': user,
                        'message': 'Images retrieved successfully',
                        'data': user_img_data
                    })
                except ValidationError as e:
                    logger.warning(f"Validation error: {str(e)}")
                    return build_response(400, {'message': str(e)})

            elif user == 'doctor':
                # Get all low confidence images for doctor review
                all_param = query_params.get('all')
                if all_param and all_param.lower() == 'true':
                    try:
                        user_img_data = get_all_lowconf_images()
                        return build_response(200, {
                            'message': 'All low-confidence images retrieved successfully',
                            'data': user_img_data
                        })
                    except S3ServiceError as e:
                        logger.error(f"S3 service error: {str(e)}")
                        return build_response(500, {'message': str(e)})
            else:
                logger.warning(f"Invalid user type: {user}")
                return build_response(400, {'message': 'Invalid user type'})

        # Process POST requests
        if http_method == 'POST':
            # Parse the body
            try:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
                logger.info(f"Request body type: {type(body)}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {str(e)}, Body: {event.get('body', 'None')}")
                return build_response(400, {'message': f'Invalid JSON in request body: {str(e)}'})

            user = body.get('user')

            if user == 'patient':
                try:
                    # Validate patient post data
                    validate_patient_post(body)

                    # Process the patient post
                    s3_path = handle_patient_post(body, BUCKET_NAME)

                    return build_response(200, {
                        'user': user,
                        'message': 'Image uploaded successfully',
                        'path': s3_path,
                        'requires_review': body.get('confidence') == 'low'
                    })
                except ValidationError as e:
                    logger.warning(f"Validation error: {str(e)}")
                    return build_response(400, {'message': str(e)})
                except S3ServiceError as e:
                    logger.error(f"S3 service error: {str(e)}")
                    return build_response(500, {'message': str(e)})
            else:
                logger.warning(f"Invalid user type: {user}")
                return build_response(400, {'message': 'Invalid user type or operation'})

        logger.warning(f"Invalid request method: {http_method}")
        return build_response(400, {'message': 'Invalid request method or parameters'})

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return build_response(400, {'message': str(e)})
    except S3ServiceError as e:
        logger.error(f"S3 service error: {str(e)}")
        return build_response(500, {'message': str(e)})
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        return build_response(500, {'message': str(e)})
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        return build_response(500, {'message': f'Internal server error'})