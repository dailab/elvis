from elvis.utility.elvis_general import floor
from elvis.units import Energy
from elvis.units import Power


class Battery:
    """Models a generic battery."""

    def __init__(self, capacity: Energy, max_charge_power: Power,
                 min_charge_power: Power, efficiency: float, start_power_degradation: float=1,
                 max_degradation_level: float=0):
        """Create instance of Battery given all parameters."""
        assert isinstance(capacity, (float, int)) and capacity > 0, \
            'Battery capacity must be greater than 0'
        assert isinstance(max_charge_power, (float, int))
        assert isinstance(min_charge_power, (float, int))
        assert isinstance(efficiency, (float, int)) and (0 <= efficiency <= 1)
        assert isinstance(start_power_degradation, (float, int)) and (0 <= start_power_degradation <= 1)
        assert isinstance(max_degradation_level, (float, int)) and (0 <= max_degradation_level <= 1)
        assert max_degradation_level * max_charge_power >= min_charge_power

        # battery capacity (kWh)
        self.capacity = capacity

        # maximum supported charging power (W)
        self.max_charge_power = max_charge_power

        # minimum supported charging power (W)
        self.min_charge_power = min_charge_power

        # battery efficiency ([0,1])
        self.efficiency = efficiency

        # SOC level at which the max power start degrading ([0,1])
        self.start_power_degradation = start_power_degradation

        # Remaining fraction of initial max_power at SOC = 1 (max degradation) ([0,1])
        # smaller max_degradation_level -> power degrades more:
        # max_power_possible * max_degradation_level
        self.max_degradation_level = max_degradation_level

    def to_dict(self):
        dictionary = self.__dict__.copy()
        return dictionary

    def max_power_possible(self, current_soc):
        """Return the max power that can be assigned to the battery in regard of the current
            SOC.
            As of implementation right now return power assignable to the car:
                Max_power_at_battery_pins / conversion_efficiency.

        Args:
            current_soc: (float): Current state of charge: [0, 1]

        Return:
            max_power_possible: (float): Max assignable power.

        """
        if current_soc > self.start_power_degradation:
            power_degradation = (current_soc - self.start_power_degradation) / \
                                (1-self.start_power_degradation) * \
                                 self.max_charge_power * (1 - self.max_degradation_level)

            max_power_possible = self.max_charge_power - power_degradation
            return max_power_possible

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

        if 'start_power_degradation' and 'max_degradation_level' in kwargs:
            start_power_degradation = kwargs['start_power_degradation']
            max_degradation_level = kwargs['max_degradation_level']

            return EVBattery(capacity, max_charge_power, min_charge_power, efficiency,
                             start_power_degradation, max_degradation_level)

        return EVBattery(capacity, max_charge_power, min_charge_power, efficiency)


class EVBattery(Battery):
    """Models an electric vehicle battery."""

    def __init__(self, *args, **kwargs):
        super(EVBattery, self).__init__(*args, **kwargs)


class StationaryBattery(Battery):
    """Models a stationary vehicle battery."""

    def __init__(self, *args, **kwargs):

        keys = kwargs.keys()

        if 'initial_soc' in keys:
            assert isinstance(kwargs['initial_soc'], (int, float)), 'Initial SOC must be numeric.'
            assert 0 <= kwargs['initial_soc'] <= 1, 'Initial SOC must be in between 0 and 1'
            self.soc = kwargs['initial_soc']
        else:
            self.soc = 0

        if 'min_soc' in keys:
            assert isinstance(kwargs['min_soc'], (int, float)), 'Min SOC must be numeric.'
            assert 0 <= kwargs['min_soc'] <= 1, 'Min SOC must be in between 0 and 1'
            self.min_soc = kwargs['min_soc']
        else:
            self.min_soc = 0

        self.power = 0
        self.soc_time = []

        super(StationaryBattery, self).__init__(*args, **kwargs)

    def max_discharge_power(self, cur_ass_power, step_length):
        """Calculates the max power possible to discharge the storage system regarding its power
            limits and its current energy level.

        Args:
            cur_ass_power: (float): Currently assigned power.
            step_length: (:obj: `datetime.timedelta`): Resolution of the simulation denoting the
                time in between two adjacent time steps.

        Returns:
            max_power: (float): Max power possible to discharge the storage system with.

        TODO:
            - integrate efficiencies
        """
        assert isinstance(cur_ass_power, (float, int)), 'Currently assigned power should be numeric'
        # Max power based on already assigned power and what is theoretically possible to discharge
        max_power_theo = self.max_charge_power - cur_ass_power

        # Power that leads to SOC = min_soc at the end of time step
        step_length_hours = step_length.total_seconds() / 3600
        soc_cur_ass_power = cur_ass_power / self.capacity * step_length_hours
        power_to_empty = (self.soc - soc_cur_ass_power - self.min_soc) * \
                         self.capacity / step_length_hours

        # Max power possible based on energy level and power limits
        max_power = max(min(max_power_theo, power_to_empty), 0)
        # Round down to 3 decimals
        max_power = floor(max_power)
        return max_power

    def charge(self, available_power, step_length):
        """
        Charges the battery with a given power or with whatever is possible considering its
            power limits and its current energy level.

        Args:
            available_power: (float): Power that is available from the transformer.
            step_length: (:obj: `datetime.timedelta`): Resolution of the simulation denoting the
                time in between two adjacent time steps.

        Returns:
            power_charged: The power the battery was actually charged with.

        TODO:
            - integrate efficiencies
        """
        assert isinstance(available_power, (float, int)), 'Available power should be numeric'
        assert available_power >= 0, 'The max charge power must be >= 0.'
        # Power needed to charge to SOC = 1 at the end of time step
        step_length_hours = step_length.total_seconds() / 3600
        max_power_to_full = (1 - self.soc) * self.capacity / step_length_hours

        # Max power possible considering all limits (available, power limits, energy level)
        power_charged = min(max_power_to_full, self.max_charge_power, available_power)

        # SOC change given the power to charge with
        delta_soc = power_charged * step_length_hours / self.capacity
        self.soc += delta_soc
        # Make sure SOC is within limits
        self.check_soc()
        self.power = power_charged
        self.soc_time.append(self.soc)
        return power_charged

    def discharge(self, power_to_discharge, step_length):
        """
        Tries to discharge the battery with given power. If either the power limits or the limit
            due to the current energy level is violated a ValueError will be raised.

        Args:
            power_to_discharge: (float): Power the system is supposed to be discharged with.
                Only positive values are allowed. These are understood to be discharged though.
            step_length: (:obj: `datetime.timedelta`): Resolution of the simulation denoting the
                time in between two adjacent time steps.

        TODO:
            - integrate efficiencies
            """
        assert isinstance(power_to_discharge,(float, int)), 'Currently assigned power ' \
                                                            'should be numeric'
        assert power_to_discharge >= 0, 'The max charge power must be >= 0.'

        # Max power too discharge with at current SOC
        max_discharge_power = self.max_discharge_power(0, step_length)

        if max_discharge_power < power_to_discharge:
            raise ValueError('Power to discharge with is out of the limits.')
        self.power = - power_to_discharge

        # SOC change given the power to discharge with
        step_length_hours = step_length.total_seconds() / 3600
        delta_soc = power_to_discharge * step_length_hours / self.capacity
        self.soc -= delta_soc
        # Make sure SOC is within limits
        self.check_soc()
        self.soc_time.append(self.soc)
        return

    def check_soc(self):
        assert 0 <= self.soc <= 1, 'SOC is out of limits.'
