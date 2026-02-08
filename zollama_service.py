"""©2024, Ovais Quraishi

    LICENSE: The 3-Clause BSD License - license.txt

    Backward compatibility wrapper for zollama.py Flask application.
    This file is kept for legacy purposes. Use main.py for the new FastAPI service.
"""
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from zollama.py for backward compatibility
from zollama import app as flask_app

# Export the Flask app for use with gunicorn or other WSGI servers
application = flask_app

if __name__ == "__main__":
    # Non-production WSGI settings:
    #  port 5000, listen to local ip address, use ssl
    # in production we use gunicorn
    flask_app.run(
        port=5009,
        host="0.0.0.0",
        ssl_context=("cert.pem", "key.pem"),
        debug=False,
    )
