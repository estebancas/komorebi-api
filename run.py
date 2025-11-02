"""
WSGI entry point for production deployment.
This file is used by gunicorn to run the application.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # This is only used for development with `python run.py`
    # In production, gunicorn will import the app object directly
    app.run(debug=False, host='0.0.0.0', port=8080)
