
class ElectricVehicle:
    """Models the charging behaviour of a specific EV model."""

    def __init__(self, brand: str, model: str, battery: EVBattery):
        self.brand = brand
        self.model = model
        self.battery = battery