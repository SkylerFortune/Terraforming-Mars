from dataclasses import dataclass


@dataclass
class Production:
    money: int = 0
    steel: int = 0
    titanium: int = 0
    plants: int = 0
    heat: int = 0
    energy: int = 0

