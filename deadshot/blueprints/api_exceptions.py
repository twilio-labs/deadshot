from flask import jsonify

# This file defines standard API error responses


class APIException(Exception):
    def __init__(
            self,
            code,
            message=None,
            errors=None,
            resource=None,
            field=None,
            value=None,
            payload=None
    ):
        self.code = code
        self.message = message
        self.errors = errors
        self.resource = resource
        self.field = field
        self.value = value
        self.payload = payload

    def jsonify(self):
        response = dict(self.payload or ())
        response["code"] = self.code
        if self.message is not None:
            response["message"] = self.message
        if self.errors is not None:
            response["errors"] = self.errors
        if self.resource is not None:
            response["resource"] = self.resource
        if self.field is not None and self.value is not None:
            response["field"] = self.field
            response["value"] = self.value
        return jsonify(response)


class BadRequestException(APIException):
    def __init__(self, message):
        APIException.__init__(
            self,
            code=400,
            message=message)


class UnauthorizedException(APIException):
    def __init__(self, message):
        APIException.__init__(
            self,
            code=401,
            message=message)


class ResourceNotFoundException(APIException):
    def __init__(self, resource, field, value):
        APIException.__init__(
            self,
            code=404,
            resource=resource,
            field=field,
            value=value
        )


class UnprocessableEntityException(APIException):
    def __init__(self, message, errors):
        APIException.__init__(
            self,
            code=422,
            message=message,
            errors=errors)


class InternalServerErrorException(APIException):
    def __init__(self, message):
        APIException.__init__(
            self,
            code=500,
            message=message)
