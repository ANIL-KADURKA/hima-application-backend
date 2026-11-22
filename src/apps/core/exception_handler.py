import logging

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import exception_handler as default_exception_handler
from rest_framework.views import set_rollback

logger = logging.getLogger("apps.api")


def api_exception_handler(exc: Exception, context: dict[str, object]) -> Response:
    response = default_exception_handler(exc, context)
    request = context.get("request")
    method = request.method if isinstance(request, Request) else "unknown"
    path = request.path if isinstance(request, Request) else "unknown"

    if response is None:
        status_code = 500
        code = "internal_server_error"
        message = "An internal server error occurred."
        details: object = None
        set_rollback()
        logger.error(
            "Unhandled API exception method=%s path=%s exception=%s",
            method,
            path,
            type(exc).__name__,
        )
        return Response(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
            status=status_code,
        )

    status_code = response.status_code
    details = response.data if isinstance(exc, ValidationError) else None

    if isinstance(exc, ValidationError):
        code = "validation_error"
        message = "Request validation failed."
    elif status_code >= 500:
        code = "internal_server_error"
        message = "An internal server error occurred."
    elif isinstance(exc, APIException):
        code = str(exc.default_code)
        message = str(exc.detail)
    else:
        code = "api_error"
        message = "The request could not be completed."

    if status_code >= 500:
        logger.error(
            "API exception method=%s path=%s status=%s code=%s exception=%s",
            method,
            path,
            status_code,
            code,
            type(exc).__name__,
        )
    else:
        logger.info(
            "API request rejected method=%s path=%s status=%s code=%s",
            method,
            path,
            status_code,
            code,
        )

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    return response
