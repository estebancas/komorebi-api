import os
import boto3
from botocore.exceptions import ClientError
import uuid
from werkzeug.utils import secure_filename


class S3Service:
    """Service for handling file uploads to AWS S3"""

    def __init__(self):
        """
        Initialize S3 client with credentials from environment variables.

        Required environment variables:
        - AWS_ACCESS_KEY_ID: IAM user access key
        - AWS_SECRET_ACCESS_KEY: IAM user secret key
        - AWS_S3_BUCKET_NAME: Name of the S3 bucket
        - AWS_REGION: AWS region (e.g., 'us-east-1')
        """
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        # Validate that all required credentials are present
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError(
                "Missing AWS credentials. Please set AWS_ACCESS_KEY_ID, "
                "AWS_SECRET_ACCESS_KEY, and AWS_S3_BUCKET_NAME environment variables."
            )

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )

    def upload_file(self, file, folder='uploads'):
        """
        Upload a file to S3 and return the public URL.

        Args:
            file: FileStorage object from Flask request.files
            folder: S3 folder/prefix where the file will be stored (default: 'uploads')

        Returns:
            dict: Contains 'url' (public URL of the uploaded file) and 'key' (S3 object key)

        Raises:
            ValueError: If file is invalid or has no filename
            ClientError: If S3 upload fails
        """
        if not file or not file.filename:
            raise ValueError('No file provided or file has no filename')

        # Secure the filename and generate a unique name to avoid collisions
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create the S3 key (path in bucket)
        s3_key = f"{folder}/{unique_filename}"

        try:
            # Upload file to S3
            # ACL='public-read' makes the file publicly accessible
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )

            # Construct the public URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

            return {
                'url': file_url,
                'key': s3_key,
                'original_filename': original_filename
            }

        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")


# Global instance to be used across the application
_s3_service_instance = None


def get_s3_service():
    """
    Get or create a singleton instance of S3Service.

    This ensures we only create one S3 client for the entire application,
    which is more efficient than creating a new client for each upload.

    Returns:
        S3Service: The S3 service instance
    """
    global _s3_service_instance
    if _s3_service_instance is None:
        _s3_service_instance = S3Service()
    return _s3_service_instance
