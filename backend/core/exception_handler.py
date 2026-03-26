from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def mwt_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Add additive envelope
        # format: { "error": str, "code": str, "detail": str, "errors": original_drf_shape }
        
        detail = response.data.get('detail', 'Validation Error')
        code = getattr(exc, 'default_code', 'error')
        
        # Original DRF data is kept in 'errors'
        original_data = response.data
        
        response.data = {
            'error': detail,
            'code': code,
            'detail': detail,
            'errors': original_data
        }

    return response
