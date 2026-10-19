from dataclasses import dataclass


@dataclass(frozen=True)
class OceansTrack:
    MIN_VALUE: int = 0
    MAX_VALUE: int = 9
    STEP: int = 1

    value: int = 0

    def increase(self) -> "OceansTrack":
        new_value = self.value + self.STEP
        if new_value > self.MAX_VALUE:
            raise ValueError("Oceans cannot exceed " + str(self.MAX_VALUE))
        return OceansTrack(new_value)