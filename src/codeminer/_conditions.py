"""Condition handling: format and display API warnings, messages, and errors.

Mirrors the R client's `print_captured_warnings_and_messages()` and error
formatting, using `rich` to reproduce the bullet-style output of R's `cli`
package.

The API JSON response contains structured conditions::

    {
        "warnings": [["Warnings: 2"], {"!": "msg1", "i": "hint"}, ...],
        "messages": [["Messages: 0"]],
        "error": {"error_type": "class_name", "error_message": {"x": "msg", "i": "hint"}}
    }

Bullet-type names from R's cli::cli_bullets():
    "x" = error cross (red)
    "!" = warning bang (yellow)
    "i" = info (cyan)
    "*" = generic bullet
    "-" = no bullet (indented)
"""

import warnings

from rich.console import Console
from rich.text import Text

from .exceptions import CodeMinerError

_console = Console(stderr=True)

_BULLET_MAP = {
    "x": ("[bold red]✖[/bold red]", "red"),
    "!": ("[yellow]![/yellow]", "yellow"),
    "i": ("[cyan]ℹ[/cyan]", "cyan"),
    "*": ("•", None),
    "-": (" ", None),
}


def _format_condition(condition_dict):
    """Format a single condition (dict of bullet_name: text) for rich output.

    Parameters
    ----------
    condition_dict : dict
        A dict mapping bullet names to message text,
        e.g. ``{"!": "Something happened", "i": "Try this instead"}``.

    Returns
    -------
    list[str]
        Lines of rich markup ready for console.print().
    """
    lines = []
    for name, text in condition_dict.items():
        bullet_char, _ = _BULLET_MAP.get(name, (" ", None))
        lines.append(f"{bullet_char} {text}")
    return lines


def _print_conditions(parsed_response):
    """Replay warnings and messages from a parsed API response.

    Mirrors R's ``print_captured_warnings_and_messages()``. Skips the first
    element of each list (the count string like "Warnings: 2").

    Parameters
    ----------
    parsed_response : dict
        The full parsed JSON response from the API.
    """
    warning_items = parsed_response.get("warnings", [])
    message_items = parsed_response.get("messages", [])

    # Skip count element (first item), process remaining conditions
    for item in warning_items[1:]:
        if isinstance(item, dict):
            lines = _format_condition(item)
            for line in lines:
                _console.print(line)

    for item in message_items[1:]:
        if isinstance(item, dict):
            lines = _format_condition(item)
            for line in lines:
                _console.print(line)


def _raise_api_error(parsed_error, status_code):
    """Format and raise a CodeMinerError from a structured API error response.

    Mirrors the R client's error handling in ``api_request()``, which feeds
    the structured message vector back into ``cli::cli_abort()`` to reproduce
    the exact same formatted output.

    Parameters
    ----------
    parsed_error : dict
        The ``"error"`` field from the API response JSON, containing
        ``"error_type"`` and ``"error_message"`` keys.
    status_code : int
        The HTTP status code.

    Raises
    ------
    CodeMinerError
        Always raised with the formatted message.
    """
    error_type = parsed_error.get("error_type", "API Error")
    error_message = parsed_error.get("error_message", {})

    # Format the bullet list for display
    if isinstance(error_message, dict):
        lines = _format_condition(error_message)
        formatted = "\n".join(lines)
        # Also print with rich formatting to stderr
        _console.print(f"[bold red]Error ({error_type}):[/bold red]")
        for line in lines:
            _console.print(f"  {line}")
    elif isinstance(error_message, str):
        formatted = error_message
        _console.print(f"[bold red]Error ({error_type}):[/bold red] {error_message}")
    else:
        formatted = str(error_message)
        _console.print(f"[bold red]Error ({error_type}):[/bold red] {formatted}")

    raise CodeMinerError(
        formatted, error_type=error_type, error_message=error_message
    )
