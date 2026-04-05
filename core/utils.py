from rest_framework.response import Response


class APIErrorResponse(Response):
    def __init__(
        self, status_code, message=None, reason=None, data=None, serial_valid=None
    ):
        payload = {
            "error": {
                "code": status_code,
                "message": message or self._get_serializer_validation_err(serial_valid),
                "reason": reason or self._get_default_reason(status_code),
            }
        }
        if data:
            payload["error"]["details"] = data
        super().__init__(payload, status=status_code)

    def _get_default_reason(self, status_code):
        return {
            400: "Validation Failed",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict Detected",
            500: "Internal Server Error",
        }.get(status_code, "Unknown Error")

    def _get_serializer_validation_err(self, errors):
        if not errors:
            return "Invalid input data"

        # Case 1: Multiple fields failing
        if len(errors) > 1:
            return (
                f"Validation failed for {len(errors)} fields. Please check the details."
            )

        try:
            # Case 2: Single field failing
            field_name = next(iter(errors))
            error_list = errors[field_name]

            # Extract the error string
            msg = error_list[0] if isinstance(error_list, list) else str(error_list)

            readable_field = field_name.replace("_", " ").capitalize()
            return f"{readable_field}: {msg}"

        except (KeyError, IndexError, TypeError):
            return "Invalid input data"
