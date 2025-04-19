"""
Utility functions for the Lambda function
"""
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)


def build_response(status_code, body):
    """Build a standardized API response"""
    try:
        # Ensure the body is properly serialized
        response_body = json.dumps(body)

        response = {
            'statusCode': status_code,
            'body': response_body,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

        # Log the response code (but not the full response for privacy)
        if status_code >= 400:
            logger.warning(f"Returning error response with status code {status_code}")
        else:
            logger.info(f"Returning successful response with status code {status_code}")

        return response
    except Exception as e:
        logger.error(f"Error building response: {str(e)}")
        # Fallback response if serialization fails
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error building response'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }