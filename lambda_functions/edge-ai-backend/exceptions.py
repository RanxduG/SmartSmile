"""
Custom exceptions for the application
"""

class ServiceError(Exception):
    """Base exception for all service errors"""
    pass

class ValidationError(ServiceError):
    """Exception raised for validation errors"""
    pass

class S3ServiceError(ServiceError):
    """Exception raised for S3 service errors"""
    pass

class PatientServiceError(ServiceError):
    """Exception raised for patient service errors"""
    pass

class DoctorServiceError(ServiceError):
    """Exception raised for doctor service errors"""
    pass