import json, glob
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

@dataclass(frozen=True)
class CardDef:
    id: str
    name: str
    type: str
    module: str
    cost: int | None
    tags: tuple[str, ...]
    requirements: tuple[Mapping, ...]    # normalized, see below
    behavior: Mapping | None
    action: Mapping | None
    first_action: Mapping | None
    victory_points: int | str | Mapping | None
    resource_type: str | None
    hooks: Mapping[str, Callable]        # from your hand-written registry

def _as_tuple_of_dicts(req):
    if req is None: return ()
    if isinstance(req, dict): return (req,)  # the data uses a dict for one, a list for several
    return tuple(req)