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
