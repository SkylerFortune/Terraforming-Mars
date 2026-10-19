from dataclasses import dataclass

from engine.helper.player.production_object import ProductionObject


@dataclass(frozen=True)
class ResourceObject:
    megacredits: int
    steel: int
    titanium: int
    plants: int
    energy: int
    heat: int

    def move_energy(self) -> 'ResourceObject':
        return ResourceObject(
            megacredits=self.megacredits,
            steel=self.steel,
            titanium=self.titanium,
            plants=self.plants,
            energy=0,
            heat=self.heat + self.energy
        )

    def decrease_resource(self, resource: str, amount: int) -> 'ResourceObject':
        return ResourceObject(
            megacredits=self.megacredits - (amount if resource == "megacredits" else 0),
            steel=self.steel - (amount if resource == "steel" else 0),
            titanium=self.titanium - (amount if resource == "titanium" else 0),
            plants=self.plants - (amount if resource == "plants" else 0),
            energy=self.energy - (amount if resource == "energy" else 0),
            heat=self.heat - (amount if resource == "heat" else 0)
        )

    def __add__(self, other: 'ProductionObject | ResourceObject | int') -> 'ResourceObject':
        if isinstance(other, ProductionObject):
            return ResourceObject(
                megacredits=self.megacredits + other.megacredits,
                steel=self.steel + other.steel,
                titanium=self.titanium + other.titanium,
                plants=self.plants + other.plants,
                energy=self.energy + other.energy,
                heat=self.heat + other.heat
            )
        elif isinstance(other, ResourceObject):
            return ResourceObject(
                megacredits=self.megacredits + other.megacredits,
                steel=self.steel + other.steel,
                titanium=self.titanium + other.titanium,
                plants=self.plants + other.plants,
                energy=self.energy + other.energy,
                heat=self.heat + other.heat
            )
        else:
            return ResourceObject(
                megacredits=self.megacredits + other,
                steel=self.steel + other,
                titanium=self.titanium + other,
                plants=self.plants + other,
                energy=self.energy + other,
                heat=self.heat + other
            )