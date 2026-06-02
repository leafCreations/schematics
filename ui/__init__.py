"""PySide6 structure editor."""

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    from ui.main_window import main as run_main_window

    return run_main_window(argv)
