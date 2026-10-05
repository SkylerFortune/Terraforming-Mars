from dataclasses import dataclass

@dataclass
class Tags:
    science: int = 0
    microbe: int = 0
    building: int = 0
    city: int = 0
    power: int = 0
    animal: int = 0
    plant: int = 0
    earth: int = 0
    jovian: int = 0
    venus: int = 0
    other: Tags | None = None
    everyone: Tags | None = None