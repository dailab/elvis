"""Class representing vehicle types. Especially in regard of their battery."""
from elvis.battery import EVBattery


class ElectricVehicle:
    """Models the charging behaviour of a specific EV model."""

    def __init__(self, brand: str, model: str, battery: EVBattery, probability):
        self.brand = brand
        self.model = model
        self.battery = battery
        self.probability = probability

    def __str__(self):
        printout = self.brand + ', ' + self.model
        return printout

    def to_dict(self):
        dictionary = dict()
        dictionary['brand'] = self.brand
        dictionary['model'] = self.model
        dictionary['battery'] = self.battery.to_dict()
        dictionary['probability'] = self.probability
        return dictionary
