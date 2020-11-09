from elvis.units import Energy
from elvis.units import Power


class Battery:
    """Models a generic battery."""

    def __init__(self, capacity: Energy, max_charge_power: Power,
                 min_charge_power: Power, efficiency: float):
        """Create instance of Battery given all parameters."""
        assert isinstance(capacity, (float, int))
        assert isinstance(max_charge_power, (float, int))
        assert isinstance(min_charge_power, (float, int))
        assert isinstance(efficiency, (float, int)) and (0 <= efficiency <= 1)
        # battery capacity (kWh)
        self.capacity = capacity

        # maximum supported charging power (W)
        self.max_charge_power = max_charge_power

        # minimum supported charging power (W)
        self.min_charge_power = min_charge_power

        # battery efficiency (%)
        self.efficiency = efficiency

    def to_dict(self):
        dictionary = self.__dict__.copy()
        return dictionary


class EVBattery(Battery):
    """Models an electric vehicle battery."""

    def __init__(self, *args, **kwargs):
        super(EVBattery, self).__init__(*args, **kwargs)

    def max_power_possible(self, current_soc):
        """Return the max power that can be assigned to the battery in regard of the current
            SOC.
            As of implementation right now return power assignable to the car:
                Max_power_at_battery_pins / conversion_efficiency.

        Args:
            current_soc: (float): Current state of charge: [0, 1]

        Return:
            max_power_possible: (float): Max assignable power.

        TODO: Implement SOC dependence."""
        return self.max_charge_power

    def min_power_possible(self, current_soc):
        """Return the min power that can be assigned to the battery in regard of the current
        SOC.

        Args:
            current_soc: (float): Current state of charge: [0, 1]

        Return:
            max_power_possible: (float): Max assignable power.

        TODO: Implement SOC dependence."""

        return self.min_charge_power

    @staticmethod
    def from_dict(**kwargs):
        """Initialise an instance of ChargingEvent with values stored in a dict.

        Args:

            **kwargs: Arbitrary keyword arguments.
        """

        necessary_keys = ['capacity', 'max_charge_power', 'min_charge_power', 'efficiency']

        for key in necessary_keys:
            assert key in kwargs, 'Not all necessary keys are included to create an EVBattery ' \
                                  'from dict. Missing: ' + key

        capacity = kwargs['capacity']
        max_charge_power = kwargs['max_charge_power']
        min_charge_power = kwargs['min_charge_power']

        efficiency = kwargs['efficiency']

        return EVBattery(capacity, max_charge_power, min_charge_power, efficiency)
