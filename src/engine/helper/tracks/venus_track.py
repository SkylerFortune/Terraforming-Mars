from dataclasses import dataclass


@dataclass(frozen=True)
class VenusTrack:
    MIN_VALUE: int = 0
    MAX_VALUE: int = 30
    STEP: int = 1

    value: int = 0

    def increase(self) -> "VenusTrack":
        new_value = self.value + self.STEP
        if new_value > self.MAX_VALUE:
            raise ValueError("Venus cannot exceed " + str(self.MAX_VALUE))
        return VenusTrack(new_value)