"""Custom exception classes for the application."""


class CADProcessingError(Exception):
    """Base class for all CAD processing errors."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class InvalidStepFileError(CADProcessingError):
    """STEP file is corrupted or malformed (FATAL)."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid STEP file: {reason}", code="INVALID_STEP_FILE")


class LargeFileError(CADProcessingError):
    """File exceeds maximum size (RECOVERABLE)."""

    def __init__(self, file_size_mb: int, max_size_mb: int) -> None:
        super().__init__(
            f"File too large: {file_size_mb}MB > {max_size_mb}MB", code="FILE_TOO_LARGE"
        )


class NoSolidsFoundError(CADProcessingError):
    """Assembly has no solids (FATAL)."""

    def __init__(self) -> None:
        super().__init__("No solids found in assembly", code="NO_SOLIDS_FOUND")


class PartExtractionError(CADProcessingError):
    """Error extracting specific part (RECOVERABLE)."""

    def __init__(self, part_index: int, reason: str) -> None:
        super().__init__(
            f"Failed to extract part {part_index}: {reason}", code="PART_EXTRACTION_ERROR"
        )


class SvgGenerationError(CADProcessingError):
    """Error generating SVG (RECOVERABLE)."""

    def __init__(self, part_id: str, reason: str) -> None:
        super().__init__(
            f"Failed to generate SVG for {part_id}: {reason}", code="SVG_GENERATION_ERROR"
        )


class LLMApiError(CADProcessingError):
    """LLM API call failed (RECOVERABLE)."""

    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(f"LLM API error ({status_code}): {reason}", code="LLM_API_ERROR")


class AssemblyValidationError(CADProcessingError):
    """Generated assembly is invalid (RECOVERABLE)."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Assembly validation failed: {reason}", code="ASSEMBLY_VALIDATION_ERROR")
