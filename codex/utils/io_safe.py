"""
codex.utils.io_safe
Atomic and safe IO helpers for Codex.

Provides:
 - atomic_write(path, data, encoding="utf-8")
 - atomic_write_text(path, text, encoding="utf-8")

These functions write to a temporary file on the same filesystem and then atomically replace the destination.
This mitigates partial-write corruption and works better with OneDrive-like syncers.
"""
from __future__ import annotations
import os
import tempfile
from typing import Union

def atomic_write(path: str, data: Union[bytes, str], encoding: str = "utf-8") -> None:
    """
    Atomically write `data` to `path`. If `data` is str, encoding is used.
    """
    dirn = os.path.dirname(os.path.abspath(path)) or "."
    # Ensure target directory exists
    os.makedirs(dirn, exist_ok=True)
    # Write to temporary file on same filesystem
    fd, tmp = tempfile.mkstemp(dir=dirn)
    try:
        with os.fdopen(fd, "wb") as f:
            if isinstance(data, str):
                f.write(data.encode(encoding))
            else:
                f.write(data)
        # Use os.replace for atomic move
        os.replace(tmp, path)
    finally:
        # If something went wrong and tmp still exists, try to remove
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    """
    Convenience wrapper to write text content atomically.
    """
    atomic_write(path, text, encoding=encoding)
