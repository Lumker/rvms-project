class CoreException(Exception):
    """Base exception for core app"""
    pass

class ValidationError(CoreException):
    """Raised when validation fails"""
    pass

class PermissionDeniedError(CoreException):
    """Raised when user doesn't have required permissions"""
    pass

class NotFoundError(CoreException):
    """Raised when requested object is not found"""
    pass