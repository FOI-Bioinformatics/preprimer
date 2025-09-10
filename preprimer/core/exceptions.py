"""
Exception classes for preprimer with comprehensive error handling.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PrePrimerError(Exception):
    """
    Base exception for all preprimer errors.
    
    Provides structured error handling with context, user-friendly messages,
    and proper logging integration.
    """
    
    def __init__(
        self, 
        message: str, 
        *, 
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list] = None
    ):
        """
        Initialize PrePrimerError with detailed context.
        
        Args:
            message: Technical error message for developers/logs
            user_message: User-friendly message for end users
            context: Additional context about the error
            suggestions: List of suggested solutions
        """
        super().__init__(message)
        self.technical_message = message
        self.user_message = user_message or message
        self.context = context or {}
        self.suggestions = suggestions or []
        
        # Log the technical details
        self._log_error()
    
    def _log_error(self):
        """Log error with appropriate level and context."""
        log_context = {
            "error_type": self.__class__.__name__,
            "technical_message": self.technical_message,
            "context": self.context
        }
        logger.error(f"{self.__class__.__name__}: {self.technical_message}", extra=log_context)
    
    def get_user_message(self) -> str:
        """Get user-friendly error message with suggestions."""
        message = self.user_message
        if self.suggestions:
            suggestions_text = "\n".join(f"  • {suggestion}" for suggestion in self.suggestions)
            message += f"\n\nSuggestions:\n{suggestions_text}"
        return message
    
    def add_context(self, **kwargs):
        """Add additional context to the error."""
        self.context.update(kwargs)
        return self
    
    def add_suggestion(self, suggestion: str):
        """Add a suggestion for resolving the error."""
        self.suggestions.append(suggestion)
        return self


class ParserError(PrePrimerError):
    """Raised when parsing fails."""
    
    def __init__(self, message: str, *, file_path: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if file_path:
            context['file_path'] = file_path
        
        # Default user message for parser errors only if not provided
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Failed to parse primer file{f' {file_path}' if file_path else ''}. "
                f"Please check the file format and try again."
            )
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class ValidationError(PrePrimerError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, *, field: Optional[str] = None, value: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if field:
            context['field'] = field
        if value:
            context['value'] = value
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Validation failed{f' for {field}' if field else ''}. "
                f"Please check your input and try again."
            )
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class AlignmentError(PrePrimerError):
    """Raised when alignment operations fail."""
    
    def __init__(self, message: str, *, tool: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if tool:
            context['alignment_tool'] = tool
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Alignment failed{f' with {tool}' if tool else ''}. "
                f"Please check your reference file and primer sequences."
            )
        
        if 'suggestions' not in kwargs:
            suggestions = []
            if tool:
                tool_upper = tool.upper()
                suggestions.extend([
                    f"Verify {tool_upper} is properly installed and accessible",
                    "Check that reference sequences are in correct format",
                    "Ensure primer sequences are valid"
                ])
            else:
                suggestions.extend([
                    "Check that reference sequences are in correct format",
                    "Ensure primer sequences are valid"
                ])
            kwargs['suggestions'] = suggestions
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class OutputError(PrePrimerError):
    """Raised when output writing fails."""
    
    def __init__(self, message: str, *, output_path: Optional[str] = None, format_name: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if output_path:
            context['output_path'] = output_path
        if format_name:
            context['format'] = format_name
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Failed to write output{f' to {output_path}' if output_path else ''}. "
                f"Please check file permissions and disk space."
            )
        
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Verify you have write permissions to the output directory",
                "Check available disk space",
                "Ensure the output directory exists"
            ]
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class ConfigError(PrePrimerError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, *, config_file: Optional[str] = None, setting: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if config_file:
            context['config_file'] = config_file
        if setting:
            context['setting'] = setting
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Configuration error{f' in {config_file}' if config_file else ''}. "
                f"Please check your configuration settings."
            )
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class SecurityError(PrePrimerError):
    """Raised when a security violation is detected."""
    
    def __init__(self, message: str, *, violation_type: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if violation_type:
            context['violation_type'] = violation_type
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = "Security violation detected. The operation was blocked for safety."
        
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Use only trusted input files",
                "Avoid file paths with '..' or suspicious characters",
                "Check file permissions and ownership"
            ]
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
    
    def _log_error(self):
        """Security errors get special logging treatment."""
        log_context = {
            "error_type": self.__class__.__name__,
            "technical_message": self.technical_message,
            "context": self.context,
            "security_alert": True
        }
        logger.warning(f"SECURITY: {self.technical_message}", extra=log_context)


class FileNotFoundError(ParserError):
    """Raised when a required file is not found."""
    
    def __init__(self, file_path: str, **kwargs):
        if 'user_message' not in kwargs:
            kwargs['user_message'] = f"File not found: {file_path}"
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check that the file path is correct",
                "Verify the file exists and is readable",
                "Use absolute paths if relative paths aren't working"
            ]
        super().__init__(
            f"Required file not found: {file_path}",
            file_path=file_path,
            **kwargs
        )


class InvalidFormatError(ParserError):
    """Raised when file format is invalid or unsupported."""
    
    def __init__(self, file_path: str, expected_format: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if expected_format:
            context['expected_format'] = expected_format
        
        # Only set user_message if not provided
        if 'user_message' not in kwargs:
            kwargs['user_message'] = (
                f"Invalid file format: {file_path}"
                f"{f'. Expected {expected_format} format' if expected_format else ''}"
            )
        
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check that the file is in the correct format",
                "Verify file headers and structure",
                "Try converting the file to the expected format"
            ]
        
        kwargs['context'] = context
        super().__init__(
            f"Invalid format for file {file_path}",
            file_path=file_path,
            **kwargs
        )


class CorruptedDataError(ParserError):
    """Raised when data appears corrupted or malformed."""
    
    def __init__(self, file_path: str, details: Optional[str] = None, **kwargs):
        technical_msg = f"Corrupted data in {file_path}"
        if details:
            technical_msg += f": {details}"
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = f"The file {file_path} appears to be corrupted or malformed."
            
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Try re-downloading or re-creating the file",
                "Check for file corruption (e.g., incomplete downloads)",
                "Validate the file with the original source"
            ]
        
        super().__init__(
            technical_msg,
            file_path=file_path,
            **kwargs
        )


class InsufficientDataError(ValidationError):
    """Raised when there's not enough data to perform the operation."""
    
    def __init__(self, message: str, required_count: Optional[int] = None, actual_count: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        if required_count is not None:
            context['required_count'] = required_count
        if actual_count is not None:
            context['actual_count'] = actual_count
        
        if 'user_message' not in kwargs:
            kwargs['user_message'] = f"Insufficient data to proceed. {message}"
        
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check that your input file contains the required data",
                "Verify that all necessary fields are populated",
                "Ensure the file is complete and not truncated"
            ]
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)


# Context manager for consistent error handling
class ErrorContext:
    """Context manager for consistent error handling patterns."""
    
    def __init__(self, operation_name: str, logger_name: Optional[str] = None):
        self.operation_name = operation_name
        self.logger = logging.getLogger(logger_name or __name__)
    
    def __enter__(self):
        self.logger.debug(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.debug(f"Completed {self.operation_name}")
            return False
        
        # Log the exception with context
        if issubclass(exc_type, PrePrimerError):
            # PrePrimerError already handles its own logging
            return False
        
        # Handle unexpected exceptions
        self.logger.error(
            f"Unexpected error in {self.operation_name}: {exc_val}",
            exc_info=True
        )
        return False


def handle_common_exceptions(operation_name: str):
    """Decorator for common exception handling patterns."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ErrorContext(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
