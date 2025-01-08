from flask import make_response
from werkzeug.exceptions import HTTPException
import json

#Define Exception -> Not Found
class NotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('',status_code)

#Define Exception -> Not according to Policies
class BusninessValidationError(HTTPException):
    def __init__(self, status_code, error_message):
        error =  {'Error':error_message}
        self.response = make_response(json.dumps(error),status_code)