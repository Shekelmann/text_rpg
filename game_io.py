"""Presentation boundary shared by the terminal and desktop frontends.

Only the game worker installs a backend. Other threads and existing tests keep
using builtins, without process-wide monkeypatches or stdout redirection.
"""

import builtins
from contextlib import contextmanager
from contextvars import ContextVar
import os


_backend = ContextVar("game_io_backend", default=None)


@contextmanager
def use_backend(backend):
    token = _backend.set(backend)
    try:
        yield backend
    finally:
        _backend.reset(token)


def print(*values, sep=" ", end="\n", file=None, flush=False):
    backend = _backend.get()
    if backend is None or file is not None:
        return builtins.print(*values, sep=sep, end=end, file=file, flush=flush)
    backend.write((" " if sep is None else sep).join(map(str, values))
                  + ("\n" if end is None else end))


def input(prompt="", *, kind="menu", choices=None, default=""):
    """Read unchanged string values; optional metadata describes UI controls.

    Menus may supply explicit (value, label) pairs in future. The compatibility
    backend derives them from the existing numbered text when choices is None.
    """
    backend = _backend.get()
    if backend is None:
        return builtins.input(prompt)
    return backend.read(prompt, kind=kind, choices=choices, default=default)


def clear():
    backend = _backend.get()
    if backend is None:
        os.system("cls" if os.name == "nt" else "clear")
    else:
        backend.clear()


def present(view, **data):
    """Optional structured presentation; terminal renderers remain the fallback."""
    backend = _backend.get()
    if backend is None:
        return False
    backend.present(view, **data)
    return True


def bind_state(player, world):
    """Let the frontend take read-only snapshots at game I/O boundaries."""
    backend = _backend.get()
    if backend is not None:
        backend.bind_state(player, world)
