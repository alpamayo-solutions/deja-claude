"""Tests for the CLI entry point."""


def test_main_module_is_importable():
    """Verify the package can be imported."""
    from deja_claude import __version__

    assert __version__


def test_main_function_exists():
    """Verify the main entry point exists and is callable."""
    from deja_claude.__main__ import main

    assert callable(main)
