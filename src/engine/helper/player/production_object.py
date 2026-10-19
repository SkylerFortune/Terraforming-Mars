from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionObject:
    megacredits: int
    steel: int
    titanium: int
    plants: int
    energy: int
    heat: int

    def decrease_production(self, production: str, amount: int) -> 'ProductionObject':
        return ProductionObject(
            megacredits=self.megacredits - (amount if production == "megacredits" else 0),
            steel=self.steel - (amount if production == "steel" else 0),
            titanium=self.titanium - (amount if production == "titanium" else 0),
            plants=self.plants - (amount if production == "plants" else 0),
            energy=self.energy - (amount if production == "energy" else 0),
            heat=self.heat - (amount if production == "heat" else 0)
        )

    def __add__(self, other: 'ProductionObject | int') -> 'ProductionObject':
        if isinstance(other, int):
            return ProductionObject(
                megacredits=self.megacredits + other,
                steel=self.steel + other,
                titanium=self.titanium + other,
                plants=self.plants + other,
                energy=self.energy + other,
                heat=self.heat + other
            )
        else:
            return ProductionObject(
                megacredits=self.megacredits + other.megacredits,
                steel=self.steel + other.steel,
                titanium=self.titanium + other.titanium,
                plants=self.plants + other.plants,
                energy=self.energy + other.energy,
                heat=self.heat + other.heat
            )