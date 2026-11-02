"""Tests for the colour helper module (``minigit.color``)."""

from __future__ import annotations

import minigit.color as color

# ── helpers ──────────────────────────────────────────────────────────────────


def _reset(no_color: bool = False) -> None:
    """Reset module state and call configure() with the given flag."""
    color._force_off = False
    color.configure(no_color=no_color)


# ── color off: not a TTY (default in tests) ──────────────────────────────────


def test_no_color_when_not_a_tty(monkeypatch):
    """capsys / StringIO is not a TTY → no ANSI codes ever."""
    _reset()
    monkeypatch.delenv("NO_COLOR", raising=False)
    # stdout.isatty() already returns False inside pytest; no patching needed.
    assert color.yellow("abc") == "abc"
    assert color.red("abc") == "abc"
    assert color.green("abc") == "abc"
    assert color.cyan("abc") == "abc"
    assert color.bold("abc") == "abc"
    assert color.bg_red("abc") == "abc"
    assert color.bg_green("abc") == "abc"


# ── color off: NO_COLOR env var ───────────────────────────────────────────────


def test_no_color_env_var_suppresses_color(monkeypatch):
    """NO_COLOR being set (any value) disables color even for a fake TTY."""
    _reset()
    monkeypatch.setenv("NO_COLOR", "")
    monkeypatch.setattr("sys.stdout", _FakeTTY())
    assert color.yellow("sha1234") == "sha1234"
    assert color.bg_red("file.txt") == "file.txt"
    assert color.bg_green("file.txt") == "file.txt"


# ── color off: --no-color flag ────────────────────────────────────────────────


def test_no_color_flag_suppresses_color(monkeypatch):
    """configure(no_color=True) disables color even for a fake TTY."""
    _reset(no_color=True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout", _FakeTTY())
    assert color.yellow("sha1234") == "sha1234"
    assert color.bg_red("file.txt") == "file.txt"
    assert color.bg_green("file.txt") == "file.txt"


# ── color on: real TTY, no overrides ─────────────────────────────────────────


def test_color_on_when_tty(monkeypatch):
    """All helpers emit ANSI codes when stdout is a TTY and nothing suppresses color."""
    _reset()
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout", _FakeTTY())
    assert color.yellow("sha") == "\033[33msha\033[0m"
    assert color.red("x") == "\033[31mx\033[0m"
    assert color.green("x") == "\033[32mx\033[0m"
    assert color.cyan("x") == "\033[36mx\033[0m"
    assert color.bold("x") == "\033[1mx\033[0m"
    assert color.bg_red("x") == "\033[41mx\033[0m"
    assert color.bg_green("x") == "\033[42mx\033[0m"


# ── priority: --no-color beats TTY ───────────────────────────────────────────


def test_no_color_flag_beats_tty(monkeypatch):
    """--no-color wins even when stdout is a TTY and NO_COLOR is absent."""
    _reset(no_color=True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout", _FakeTTY())
    assert color.green("ok") == "ok"
    assert color.bg_red("ok") == "ok"
    assert color.bg_green("ok") == "ok"


# ── helper: fake TTY object ───────────────────────────────────────────────────


class _FakeTTY:
    """Minimal stdout stand-in that pretends to be a terminal."""

    def isatty(self) -> bool:
        return True
