from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from app.services.s3_service import get_s3_service
from app.middleware.auth import jwt_required, admin_required

uploads_ns = Namespace('uploads', description='File upload operations', path='/uploads')

# Define model for response documentation
upload_response_model = uploads_ns.model('UploadResponse', {
    'url': fields.String(required=True, description='Public URL of the uploaded file'),
    'key': fields.String(required=True, description='S3 object key (path in bucket)'),
    'original_filename': fields.String(required=True, description='Original filename')
})

# File upload parser for Swagger documentation
upload_parser = uploads_ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='Image file to upload')
upload_parser.add_argument('folder', location='form', type=str, required=False, help='S3 folder/prefix (default: uploads)')

# File delete parser
delete_parser = uploads_ns.parser()
delete_parser.add_argument('key', location='args', type=str, required=True, help='S3 key or URL of the file to delete')

# File update parser
update_parser = uploads_ns.parser()
update_parser.add_argument('file', location='files', type=FileStorage, required=True, help='New image file to upload')
update_parser.add_argument('old_key', location='form', type=str, required=True, help='S3 key or URL of the old file to replace')
update_parser.add_argument('folder', location='form', type=str, required=False, help='S3 folder/prefix (default: uploads)')

# Delete response model
delete_response_model = uploads_ns.model('DeleteResponse', {
    'message': fields.String(required=True, description='Success message'),
    'deleted_key': fields.String(required=True, description='S3 key that was deleted')
})

# Multiple upload parser
multiple_upload_parser = uploads_ns.parser()
multiple_upload_parser.add_argument('files', location='files', type=FileStorage, required=True, action='append', help='Multiple image files to upload')
multiple_upload_parser.add_argument('folder', location='form', type=str, required=False, help='S3 folder/prefix (default: uploads)')

# Failed upload model (for individual file failures)
failed_upload_model = uploads_ns.model('FailedUpload', {
    'original_filename': fields.String(required=True, description='Original filename that failed'),
    'error': fields.String(required=True, description='Error message')
})

# Upload summary model
upload_summary_model = uploads_ns.model('UploadSummary', {
    'total': fields.Integer(required=True, description='Total number of files'),
    'successful': fields.Integer(required=True, description='Number of successful uploads'),
    'failed': fields.Integer(required=True, description='Number of failed uploads')
})

# Multiple upload response model
multiple_upload_response_model = uploads_ns.model('MultipleUploadResponse', {
    'successful': fields.List(fields.Nested(upload_response_model), description='Successfully uploaded files'),
    'failed': fields.List(fields.Nested(failed_upload_model), description='Failed uploads'),
    'summary': fields.Nested(upload_summary_model, description='Upload summary')
})


@uploads_ns.route('/image')
class ImageUpload(Resource):
    @uploads_ns.doc('upload_image',
                    description='Upload an image file to S3. Returns the public URL. (Admin only)',
                    security='Bearer Auth')
    @jwt_required
    @admin_required
    @uploads_ns.expect(upload_parser)
    @uploads_ns.marshal_with(upload_response_model, code=201)
    def post(self):
        """Upload an image file to S3"""
        # Check if file is present in request
        if 'file' not in request.files:
            uploads_ns.abort(400, 'No file provided')

        file = request.files['file']

        # Check if file has a filename
        if file.filename == '':
            uploads_ns.abort(400, 'No file selected')

        # Validate file type (basic check)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

        if file_extension not in allowed_extensions:
            uploads_ns.abort(400, f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}')

        # Get optional folder parameter
        folder = request.form.get('folder', 'uploads')

        try:
            # Get S3 service and upload file
            s3_service = get_s3_service()
            result = s3_service.upload_file(file, folder=folder)

            return result, 201

        except ValueError as e:
            uploads_ns.abort(400, str(e))
        except Exception as e:
            uploads_ns.abort(500, f'Failed to upload file: {str(e)}')

    @uploads_ns.doc('delete_image',
                    description='Delete an image file from S3 by providing its key or URL. (Admin only)',
                    security='Bearer Auth')
    @jwt_required
    @admin_required
    @uploads_ns.expect(delete_parser)
    @uploads_ns.marshal_with(delete_response_model, code=200)
    def delete(self):
        """Delete an image file from S3"""
        # Get the S3 key from query parameters
        s3_key = request.args.get('key')

        if not s3_key:
            uploads_ns.abort(400, 'S3 key or URL is required')

        try:
            # Get S3 service and delete file
            s3_service = get_s3_service()

            # Extract just the key if a full URL was provided
            original_key = s3_key
            if s3_key.startswith('http'):
                s3_key = s3_key.split('.amazonaws.com/')[-1]

            s3_service.delete_file(original_key)

            return {
                'message': 'File deleted successfully',
                'deleted_key': s3_key
            }, 200

        except ValueError as e:
            uploads_ns.abort(400, str(e))
        except Exception as e:
            uploads_ns.abort(500, f'Failed to delete file: {str(e)}')

    @uploads_ns.doc('update_image',
                    description='Update an image by replacing an old file with a new one. (Admin only)',
                    security='Bearer Auth')
    @jwt_required
    @admin_required
    @uploads_ns.expect(update_parser)
    @uploads_ns.marshal_with(upload_response_model, code=200)
    def put(self):
        """Update an image file (delete old, upload new)"""
        # Check if file is present in request
        if 'file' not in request.files:
            uploads_ns.abort(400, 'No file provided')

        file = request.files['file']

        # Check if file has a filename
        if file.filename == '':
            uploads_ns.abort(400, 'No file selected')

        # Validate file type (basic check)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

        if file_extension not in allowed_extensions:
            uploads_ns.abort(400, f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}')

        # Get old key and folder parameters
        old_key = request.form.get('old_key')
        if not old_key:
            uploads_ns.abort(400, 'old_key is required')

        folder = request.form.get('folder', 'uploads')

        try:
            # Get S3 service and update file
            s3_service = get_s3_service()
            result = s3_service.update_file(old_key, file, folder=folder)

            return result, 200

        except ValueError as e:
            uploads_ns.abort(400, str(e))
        except Exception as e:
            uploads_ns.abort(500, f'Failed to update file: {str(e)}')


@uploads_ns.route('/images')
class ImageBulkUpload(Resource):
    @uploads_ns.doc('upload_multiple_images',
                    description='Upload multiple image files to S3 in a single request. Returns detailed results for each file. (Admin only)',
                    security='Bearer Auth')
    @jwt_required
    @admin_required
    @uploads_ns.expect(multiple_upload_parser)
    @uploads_ns.marshal_with(multiple_upload_response_model, code=201)
    def post(self):
        """Upload multiple image files to S3"""
        # Check if files are present in request
        if 'files' not in request.files:
            uploads_ns.abort(400, 'No files provided')

        # Get list of files from request
        files = request.files.getlist('files')

        if len(files) == 0:
            uploads_ns.abort(400, 'No files selected')

        # Validate file types (basic check)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

        validated_files = []
        validation_errors = []

        for file in files:
            if not file or not file.filename or file.filename == '':
                validation_errors.append({
                    'original_filename': 'unknown',
                    'error': 'No filename provided'
                })
                continue

            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

            if file_extension not in allowed_extensions:
                validation_errors.append({
                    'original_filename': file.filename,
                    'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
                })
                continue

            validated_files.append(file)

        # If no valid files after validation, return error
        if len(validated_files) == 0 and len(validation_errors) > 0:
            uploads_ns.abort(400, f'All files failed validation. First error: {validation_errors[0]["error"]}')

        # Get optional folder parameter
        folder = request.form.get('folder', 'uploads')

        try:
            # Get S3 service and upload files
            s3_service = get_s3_service()
            result = s3_service.upload_multiple_files(validated_files, folder=folder)

            # Merge validation errors with upload failures
            result['failed'].extend(validation_errors)
            result['summary']['failed'] = len(result['failed'])

            return result, 201

        except ValueError as e:
            uploads_ns.abort(400, str(e))
        except Exception as e:
            uploads_ns.abort(500, f'Failed to upload files: {str(e)}')
