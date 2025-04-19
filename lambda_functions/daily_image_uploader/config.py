"""
Configuration module for the Lambda function
All constants and configuration values should be placed here
"""
import logging
import boto3

# Initialize clients
ssm = boto3.client('ssm')
s3 = boto3.client('s3')


# Get parameters from Parameter Store
def get_parameters():
    response = ssm.get_parameters(
        Names=[
            '/edge-ai/bucket-name',
            '/edge-ai/label-studio-base-url',
            '/edge-ai/label-studio-api-key'
        ],
        WithDecryption=True
    )

    # Convert list of parameters to a dictionary
    params = {}
    for param in response['Parameters']:
        name = param['Name'].split('/')[-1]  # Get the last part of the parameter name
        params[name] = param['Value']

    return params


params = get_parameters()
print(params)
# S3 Configuration
BUCKET_NAME = params['bucket-name']

# Label Studio Configuration (kept for reference but used in separate Lambda)
LABEL_STUDIO_API_URL = params['label-studio-base-url']
LABEL_STUDIO_API_KEY = params['label-studio-api-key']