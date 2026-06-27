"""Compatibility voice module.

The project now uses edge_voice.py as the single speech input/output backend.
This wrapper keeps older imports working without loading a second voice stack.
"""

from edge_voice import listen, speak


__all__ = ["listen", "speak"]
