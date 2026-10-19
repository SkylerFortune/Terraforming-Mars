"""Hand-written card hooks, one module per expansion.

Importing this package registers every hook in `registry.HOOKS` and every continuation in
`engine.pending.CONTINUATIONS`. `base` goes first because the others reuse its shared
continuations (`gain.stock`, `gain.production`, ...).
"""
from . import base, corporations, prelude  # noqa: F401
from . import venus_next, colonies, prelude2, turmoil, promo  # noqa: F401  (not written yet)
from . import ares, moon, pathfinders, underworld, ceos  # noqa: F401  (not written yet)
from .registry import HOOKS, hook  # noqa: F401
