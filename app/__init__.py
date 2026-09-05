"""Leave Tracker application package.

``app.main`` is the application. This module re-exports it so ``from app import
app`` and ``from app.main import app`` are the same object - there is one app,
one set of routes, and one persistence layer behind them.
"""

from app.main import app

__all__ = ["app"]
