"""Application entry point."""
from __future__ import annotations

import sys


def main() -> int:
    """Launch the Ts2Mp4 application."""
    from src.app import create_app

    app, window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
