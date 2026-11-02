"""ANSI colour helpers for minigit output.

Usage::

    from minigit import color
    print(color.yellow("abc1234"))

Colors are emitted only when **all** of the following are true:

* ``sys.stdout.isatty()`` — stdout is a real terminal.
* The ``NO_COLOR`` environment variable is not set (see https://no-color.org/).
* The caller has not passed ``--no-color`` (stored via ``color.configure()``).

On Windows, ``configure()`` enables ANSI processing once via a no-op
``os.system("")`` call, which triggers the VT-sequence mode on Windows 10+.
"""

from __future__ import annotations

import os
import sys

# None  → not yet configured (behave as if False / respect isatty)
# True  → --no-color was passed; always off
_force_off: bool = False


def configure(*, no_color: bool = False) -> None:
    """Call once from ``cli.main()`` after argument parsing.

    Args:
        no_color: ``True`` when the user passed ``--no-color``.
    """
    global _force_off
    _force_off = no_color

    # Enable ANSI escape processing on Windows 10+ (harmless on other systems).
    if sys.platform == "win32" and not _force_off:
        os.system("")  # noqa: S605 – intentional, no user input involved


def _should_color() -> bool:
    """Return True only when color output is appropriate."""
    if _force_off:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def _ansi(code: int, text: str) -> str:
    if _should_color():
        return f"\033[{code}m{text}\033[0m"
    return text


# ── public helpers ──────────────────────────────────────────────────────────


def red(text: str) -> str:
    """Wrap *text* in red ANSI codes (used for errors / deletions)."""
    return _ansi(31, text)


def green(text: str) -> str:
    """Wrap *text* in green ANSI codes (used for additions / success)."""
    return _ansi(32, text)


def yellow(text: str) -> str:
    """Wrap *text* in yellow ANSI codes (used for commit SHAs / warnings)."""
    return _ansi(33, text)


def cyan(text: str) -> str:
    """Wrap *text* in cyan ANSI codes (used for hunk headers / info)."""
    return _ansi(36, text)


def bold(text: str) -> str:
    """Wrap *text* in bold ANSI codes."""
    return _ansi(1, text)


def bg_red(text: str) -> str:
    """Wrap *text* in red background ANSI codes."""
    return _ansi(41, text)


def bg_green(text: str) -> str:
    """Wrap *text* in green background ANSI codes."""
    return _ansi(42, text)
