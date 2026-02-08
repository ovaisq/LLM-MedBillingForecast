#!/usr/bin/env python3
"""FastAPI entry point for Billing Forecast GPT service."""

import logging
import os
import ssl

# Set up logging
logging.basicConfig(level=logging.INFO)

from app.main import app

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment

    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 5001))
    ssl_cert = os.environ.get("SSL_CERTFILE", "cert.pem")
    ssl_key = os.environ.get("SSL_KEYFILE", "key.pem")

    # Configure SSL context if certificate files exist
    ssl_context = None
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
        logging.info("SSL enabled with cert: %s, key: %s", ssl_cert, ssl_key)
    else:
        logging.warning("SSL certificate files not found. Running without SSL.")

    # Run the server
    if ssl_context:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            ssl_context=ssl_context,
        )
    else:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
        )
