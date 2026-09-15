"""
Standardized JSON Error Handlers and Response Wrappers.
Ensures uniform REST API response structures across all endpoints.
"""

import logging
from flask import jsonify, Flask

logger = logging.getLogger("PotholeApp.Errors")


class APIError(Exception):
    """
    Custom exception for controlled application-level errors.
    """
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def api_response(data=None, message: str = "Success", status_code: int = 200, meta: dict = None):
    """
    Constructs a uniform JSON success response.
    """
    payload = {
        "success": True,
        "status_code": status_code,
        "message": message,
        "data": data
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code


def api_error(message: str = "An error occurred", status_code: int = 400, details=None):
    """
    Constructs a uniform JSON error response.
    """
    payload = {
        "success": False,
        "status_code": status_code,
        "message": message,
        "details": details
    }
    return jsonify(payload), status_code


def register_error_handlers(app: Flask):
    """
    Registers global JSON error handlers with the Flask application.
    """
    @app.errorhandler(APIError)
    def handle_custom_api_error(error: APIError):
        logger.warning("Custom API Error [%d]: %s | Details: %s", error.status_code, error.message, error.details)
        return api_error(message=error.message, status_code=error.status_code, details=error.details)

    @app.errorhandler(400)
    def handle_bad_request(error):
        return api_error(message="Bad Request: The server could not understand the request.", status_code=400)

    @app.errorhandler(404)
    def handle_not_found(error):
        return api_error(message="Resource not found.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return api_error(message="HTTP Method not allowed for this endpoint.", status_code=405)

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        return api_error(
            message="Uploaded file is too large. Maximum allowed size is 25 MB.",
            status_code=413
        )

    @app.errorhandler(415)
    def handle_unsupported_media_type(error):
        return api_error(
            message="Unsupported media type. Supported image formats are JPG, JPEG, PNG, WEBP.",
            status_code=415
        )

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        logger.exception("Unhandled Internal Server Error: %s", error)
        return api_error(
            message="An internal server error occurred. Please contact the administrator.",
            status_code=500
        )
