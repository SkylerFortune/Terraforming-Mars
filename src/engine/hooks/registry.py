from typing import Callable


HOOKS: dict[str, dict[str, Callable]] = {}

def hook(*card_ids, name):
    def deco(fn):
        for cid in card_ids:
            if name in HOOKS.setdefault(cid, {}):
                raise ValueError(f"duplicate {name} hook for {cid}")
            HOOKS[cid][name] = fn
        return fn
    return deco