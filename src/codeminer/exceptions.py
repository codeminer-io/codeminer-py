"""Custom exception classes for the CodeMiner client."""


class CodeMinerError(Exception):
    """Error returned by the CodeMiner API.

    Attributes
    ----------
    error_type : str | None
        The R error class name (e.g. "codeminer_arg_validation_error").
    error_message : list[dict] | None
        The structured message vector from the API, preserving bullet-type
        names ("x", "!", "i", "*", "-").
    """

    def __init__(self, message, error_type=None, error_message=None):
        super().__init__(message)
        self.error_type = error_type
        self.error_message = error_message
