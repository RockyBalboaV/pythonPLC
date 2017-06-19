from flask_restful import HTTPException


class ModelNotFound(HTTPException):
    pass

custom_errors = {
    'ModelNotFound': {
        'data': "",
        'ok': 0,
    }
}