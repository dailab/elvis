"""Class representing vehicle types. Especially in regard of their battery."""
from elvis.battery import EVBattery


class ElectricVehicle:
    """Models the charging behaviour of a specific EV model."""

    def __init__(self, brand: str, model: str, battery: EVBattery, probability):
        assert isinstance(battery, EVBattery)
        assert isinstance(probability, (float, int))

        self.brand = brand
        self.model = model
        self.battery = battery
        self.probability = probability

    def __str__(self):
        printout = self.brand + ', ' + self.model
        return printout

    def to_dict(self):
        dictionary = self.__dict__.copy()
        dictionary['battery'] = self.battery.to_dict()
        return dictionary

    @staticmethod
    def from_dict(**kwargs):
        """Initialise an instance of ChargingEvent with values stored in a dict.

        Args:

            **kwargs: Arbitrary keyword arguments.
        """

        necessary_keys = ['brand', 'model', 'battery', 'probability']

        for key in necessary_keys:
            assert key in kwargs, 'Not all necessary keys are included to create a VehicleType ' \
                                  'from dict.'

        brand = kwargs['brand']
        model = kwargs['model']
        probability = kwargs['probability']
        battery = EVBattery.from_dict(**kwargs['battery'])

        return ElectricVehicle(brand, model, battery, probability)

