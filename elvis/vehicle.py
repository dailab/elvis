"""Class representing vehicle types. Especially in regard of their battery."""
from elvis.battery import EVBattery


class ElectricVehicle:
    """Models the charging behaviour of a specific EV model."""

    def __init__(self, brand: str, model: str, battery: EVBattery):
        self.brand = brand
        self.model = model
        self.battery = battery

    def __str__(self):
        printout = 'Brand: ' + str(self.brand) + ', model: ' + str(self.model)
        return printout
