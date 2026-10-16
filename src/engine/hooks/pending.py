# engine/pending.py
from typing import Callable


CONTINUATIONS: dict[str, Callable] = {}

def continuation(key: str):
    def deco(fn):
        if key in CONTINUATIONS:
            raise ValueError(f"duplicate continuation {key!r}")
        CONTINUATIONS[key] = fn
        return fn
    return deco

def ask(state, owner, *, kind, options, then, ctx=(), allow_pass=False):
    if then not in CONTINUATIONS:       # fail fast on typos
        raise KeyError(f"no continuation registered for {then!r}")
    ...

def resume(state, choice):
    pending = state.pending[0]
    return CONTINUATIONS[pending.then](state, pending.player, choice, **dict(pending.ctx))