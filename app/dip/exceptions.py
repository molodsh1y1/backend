from rest_framework.exceptions import ValidationError as DRFValidationError


class CustomValidationError(DRFValidationError):
    """
    Custom validation error that formats errors
    """

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)

    def get_full_details(self):
        if isinstance(self.detail, (list, dict)):
            return self.detail
        return {'errors': self.detail}


class CustomErrorSerializerMixin:
    """
    A mixin that formats validation errors

    Example usage:

    class MySerializer(CustomErrorSerializerMixin, serializers.ModelSerializer):
        ...
    """

    def is_valid(self, raise_exception=False):
        try:
            return super().is_valid(raise_exception=raise_exception)
        except DRFValidationError as exc:
            if raise_exception:
                errors = []
                for field, error_messages in exc.detail.items():
                    if isinstance(error_messages, list):
                        for error_message in error_messages:
                            if isinstance(error_message, dict) and 'message' in error_message:
                                error_message = error_message['message']
                            errors.append({
                                'error_message': str(error_message),
                                'error_field': field
                            })
                    else:
                        errors.append({
                            'error_message': str(error_messages),
                            'error_field': field
                        })

                raise DRFValidationError({'errors': errors})
            return False
