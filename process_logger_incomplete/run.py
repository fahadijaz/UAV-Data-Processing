import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    if app is None:
        raise RuntimeError("Failed to create Flask app. Check your app factory and configuration.")
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    try:
        app.run(debug=debug_mode, host=host, port=port)
    except Exception as e:
        import traceback
        print("Exception occurred while running the app:")
        traceback.print_exc()
        raise
