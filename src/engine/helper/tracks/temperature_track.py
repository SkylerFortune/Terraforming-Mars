from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureTrack:
    MIN_VALUE: int = -30
    MAX_VALUE: int = 8
    STEP: int = 1

    value = MIN_VALUE

    def increase(self) -> "TemperatureTrack":
        new_value = self.value + self.STEP
        if new_value > self.MAX_VALUE:
            raise ValueError("Temperature cannot exceed " + str(self.MAX_VALUE))
        return TemperatureTrack(new_value)