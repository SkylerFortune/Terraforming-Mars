from dataclasses import dataclass

from classes.helper.production import Production
from classes.helper.resources import Resources

@dataclass
class Reward:
    production: Production | None = None
    resources: Resources | None = None
    city: int = 0
    greenery: int = 0
    ocean: int = 0
    temperature: int = 0
    special: str = ""