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

from rich.console import Console

from .exceptions import CodeMinerError

_console = Console(stderr=True)

_bullet_map = {
    "x": ("[bold red]✖[/bold red]", "red"),
    "!": ("[yellow]![/yellow]", "yellow"),
    "i": ("[cyan]ℹ[/cyan]", "cyan"),
    "*": ("•", None),
    "-": (" ", None),
}

_plain_bullet_map = {
    "x": "✖",
    "!": "!",
    "i": "ℹ",
    "*": "•",
    "-": " ",
}


def _unbox(value):
    """Unwrap single-element lists to plain scalars.

    R's jsonlite wraps scalars in length-1 arrays by default, so the API
    returns e.g. ``{"x": ["message"]}`` instead of ``{"x": "message"}``.
    """
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _format_condition(condition_dict, plain=False):
    """Format a single condition (dict of bullet_name: text).

    Parameters
    ----------
    condition_dict : dict
        A dict mapping bullet names to message text,
        e.g. ``{"!": "Something happened", "i": "Try this instead"}``.
        Values may be single-element lists (R jsonlite boxing).
    plain : bool
        If True, return plain text without rich markup.

    Returns
    -------
    list[str]
        Formatted lines (rich markup or plain text).
    """
    lines = []
    for name, text in condition_dict.items():
        text = _unbox(text)
        if plain:
            bullet_char = _plain_bullet_map.get(name, " ")
        else:
            bullet_char, _ = _bullet_map.get(name, (" ", None))
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
    if not isinstance(parsed_response, dict):
        return
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
    # Auth filter and other simple plumber errors return ``{"error": ["msg"]}``
    # or ``{"error": "msg"}`` rather than the structured
    # ``{"error_type": ..., "error_message": ...}`` shape — surface those
    # plainly instead of crashing on ``.get``.
    if not isinstance(parsed_error, dict):
        if isinstance(parsed_error, list):
            short_msg = "; ".join(str(_unbox(item)) for item in parsed_error)
        else:
            short_msg = str(_unbox(parsed_error))
        if not short_msg:
            short_msg = f"HTTP {status_code}"
        error_type = f"http_{status_code}"
        _console.print(
            f"\n[bold red]Error[/bold red] (HTTP {status_code}): {short_msg}"
        )
        raise CodeMinerError(
            short_msg, error_type=error_type, error_message=parsed_error
        )

    error_type = _unbox(parsed_error.get("error_type", "API Error"))
    error_message = parsed_error.get("error_message", {})

    # Print rich-formatted error to stderr (the "pretty" display)
    if isinstance(error_message, dict):
        rich_lines = _format_condition(error_message)
        _console.print(f"\n[bold red]Error[/bold red] ({error_type}):")
        for line in rich_lines:
            _console.print(f"  {line}")
        # Short plain-text message for the exception repr
        first_value = _unbox(next(iter(error_message.values())))
        short_msg = str(first_value)
    elif isinstance(error_message, str):
        _console.print(f"\n[bold red]Error[/bold red] ({error_type}): {error_message}")
        short_msg = error_message
    else:
        short_msg = str(error_message)
        _console.print(f"\n[bold red]Error[/bold red] ({error_type}): {short_msg}")

    raise CodeMinerError(
        short_msg, error_type=error_type, error_message=error_message
    )
