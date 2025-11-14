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

    def delete_file(self, s3_key):
        """
        Delete a file from S3.

        Args:
            s3_key: The S3 object key (path in bucket) to delete.
                    Can be either the full key (e.g., 'uploads/abc123.jpg')
                    or a full URL (will extract the key automatically)

        Returns:
            bool: True if deletion was successful

        Raises:
            ValueError: If s3_key is empty or invalid
            ClientError: If S3 deletion fails
        """
        if not s3_key:
            raise ValueError('No S3 key provided')

        # If a full URL is provided, extract just the key portion
        # URL format: https://bucket-name.s3.region.amazonaws.com/folder/filename.ext
        if s3_key.startswith('http'):
            # Extract the key from the URL (everything after the bucket domain)
            try:
                # Split by .amazonaws.com/ and take the part after it
                s3_key = s3_key.split('.amazonaws.com/')[-1]
            except Exception:
                raise ValueError('Invalid S3 URL format')

        try:
            # Delete the object from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True

        except ClientError as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")

    def update_file(self, old_s3_key, new_file, folder='uploads'):
        """
        Update a file by deleting the old one and uploading a new one.

        This is a convenience method that combines delete and upload operations
        to replace an existing file with a new one.

        Args:
            old_s3_key: The S3 key or URL of the file to replace
            new_file: FileStorage object from Flask request.files (the new file)
            folder: S3 folder/prefix for the new file (default: 'uploads')

        Returns:
            dict: Contains 'url' (public URL) and 'key' (S3 object key) of the new file

        Raises:
            ValueError: If old_s3_key or new_file is invalid
            ClientError: If S3 operations fail
        """
        if not old_s3_key:
            raise ValueError('No old S3 key provided')

        # First, upload the new file
        upload_result = self.upload_file(new_file, folder=folder)

        # If upload succeeds, delete the old file
        # Note: We do upload first, then delete, to avoid data loss if upload fails
        try:
            self.delete_file(old_s3_key)
        except Exception as e:
            # Log the error but don't fail the update - the new file is already uploaded
            # In production, you might want to log this or handle it differently
            print(f"Warning: Failed to delete old file during update: {str(e)}")

        return upload_result

    def upload_multiple_files(self, files, folder='uploads'):
        """
        Upload multiple files to S3 in a single operation.

        This method uploads multiple files and returns detailed results for each,
        including both successes and failures. Even if some files fail to upload,
        the others will still be processed.

        Args:
            files: List of FileStorage objects from Flask request.files
            folder: S3 folder/prefix where files will be stored (default: 'uploads')

        Returns:
            dict: Contains 'successful' (list of upload results) and 'failed' (list of errors)
                {
                    'successful': [
                        {'url': '...', 'key': '...', 'original_filename': '...'},
                        ...
                    ],
                    'failed': [
                        {'original_filename': '...', 'error': '...'},
                        ...
                    ],
                    'summary': {
                        'total': 5,
                        'successful': 4,
                        'failed': 1
                    }
                }

        Example:
            files = request.files.getlist('files')
            result = s3_service.upload_multiple_files(files, folder='products')
        """
        if not files or len(files) == 0:
            raise ValueError('No files provided')

        successful = []
        failed = []

        for file in files:
            try:
                # Validate each file
                if not file or not file.filename or file.filename == '':
                    failed.append({
                        'original_filename': file.filename if file else 'unknown',
                        'error': 'No filename provided'
                    })
                    continue

                # Upload the file
                result = self.upload_file(file, folder=folder)
                successful.append(result)

            except Exception as e:
                # Capture the error but continue processing other files
                failed.append({
                    'original_filename': file.filename if file else 'unknown',
                    'error': str(e)
                })

        return {
            'successful': successful,
            'failed': failed,
            'summary': {
                'total': len(files),
                'successful': len(successful),
                'failed': len(failed)
            }
        }


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
