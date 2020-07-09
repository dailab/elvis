
class Battery:
    """Models a generic battery."""

    def __init__(self, capacity: Energy, max_charge_power: Power, min_charge_power: Power, efficiency: float):
        # battery capacity (kWh)
        self.capacity = capacity

        # maximum supported charging power (W)
        self.max_charge_power = max_charge_power

        # minimum supported charging power (W)
        self.min_charge_power = min_charge_power

        # battery efficiency (%)
        self.efficiency = efficiency


class EVBattery(Battery):
    """Models an electric vehicle battery."""

    def __init__(self, *args, **kwargs):
        super(EVBattery, self).__init__(*args, **kwargs)
