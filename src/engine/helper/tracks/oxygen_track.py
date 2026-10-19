from dataclasses import dataclass


@dataclass(frozen=True)
class OxygenTrack:
    MIN_VALUE: int = 0
    MAX_VALUE: int = 14
    STEP: int = 1

    value: int = -34

    def increase(self) -> "OxygenTrack":
        new_value = self.value + self.STEP
        if new_value > self.MAX_VALUE:
            raise ValueError("Oxygen cannot exceed " + str(self.MAX_VALUE))
        return OxygenTrack(new_value)