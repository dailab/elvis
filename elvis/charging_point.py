"""Charging point representation.

A charging point links the charging infrastructure to the vehicles to be charged.
It is limited by its power limits where as the lower limit has to be understood as at least the
lower limit or zero.

"""
from elvis.utility.elvis_general import floor
from elvis.infrastructure_node import InfrastructureNode
from elvis.charging_station import ChargingStation


class ChargingPoint(InfrastructureNode):
    """Represents a point of connection between :obj: `charging_point.ChargingStation` and
    vehicles."""

    counter = 1

    def __init__(self, min_power, max_power, parent):
        """Create a charging point given all parameters.

        Args:
            min_power: (float): Min charging power that has to be assigned if not 0.
            max_power: (float): Max charging power that can be assigned.
            parent: (:obj: `charging_point.ChargingStation`): Charging station the charging
            point belongs to.
            """
        # A charging point must always be connected to a charging station
        assert isinstance(parent, ChargingStation)
        identification = 'cp ' + str(ChargingPoint.counter)
        ChargingPoint.counter += 1

        # set min and max power
        super().__init__(identification, min_power, max_power, parent=parent)

        self.connected_vehicle = None

    def __str__(self):
        printout = str(self.id)
        return printout

    def get_leaving_time(self):
        """Make sure a vehicle is connected and return its leaving_time."""
        assert self.connected_vehicle is not None

        return self.connected_vehicle['leaving_time']

    def connect_vehicle(self, event):
        """Assign dict of charging event as connected vehicle.

        Args:
            event: (:obj: `charging_event.ChargingEvent`): Event of car arrival."""
        self.connected_vehicle = event.to_dict(deep=False)

    def disconnect_vehicle(self):
        """Set field connected_vehicle to None so charging point is available for
            vehicle connection."""
        self.connected_vehicle = None

    def charge_vehicle(self, power, resolution):
        """Charges the vehicle according to assigned power, capacity and efficiencies.
        TODO: add efficiencies"""
        vehicle_type = self.connected_vehicle['vehicle_type']
        battery = vehicle_type.battery
        hours = resolution.total_seconds()/3600
        # TODO: This should be calculated by chaining some class methods from battery, vehicle type,
        # hardware. Each of them have different ways of converting/transporting power with their
        # specific losses
        delta = power * hours / battery.capacity

        self.connected_vehicle['soc'] = min(1, self.connected_vehicle['soc'] + delta)

    def max_hardware_power(self):
        """Calculate dependent on currently connected car the maximum power possible. Solely based
            on the charging point and battery boundaries no charging station boundaries considered.
            A further check whether this power exceeds the charging station boundaries has to be done
            separately. At the same time it is not checked whether the soc_target is met.
            TODO: Go up the tree."""

        if self.connected_vehicle is not None:
            vehicle = self.connected_vehicle
            vehicle_type = vehicle['vehicle_type']
            soc = vehicle['soc']
            battery = vehicle_type.battery

            max_power = min(self.max_power, battery.max_power_possible(soc))
            max_power = floor(max_power)
            return max_power
        return 0

    def min_hardware_power(self):
        """Calculate dependent on currently connected car the minimum power if not 0 needed
            to start charging.
            #TODO: Go up the tree."""

        if self.connected_vehicle is not None:
            vehicle = self.connected_vehicle
            vehicle_type = vehicle['vehicle_type']
            soc = vehicle['soc']
            battery = vehicle_type.battery

            min_power = max(self.min_power, battery.min_power_possible(soc))
            return min_power
        return 0

    def power_to_charge_target(self, timedelta, soc_target):
        """Calculate the average power needed in a time period to charge the battery of the
            connected vehicle to a given soc target.

        Args:
            timedelta: (:obj: `datetime.timedelta`): Length of the timeperiod.
            soc_target: (float): SOC target to be met.

        Returns:
            power_to_target: (float): Power needed to reach the given SOC target.
            If soc_target > current_soc: return 0."""

        if not self.check_soc(soc_target):
            # TODO: Raise SOC out of boundaries error.
            print('ERROR: SOC exceeded boundaries. SOC: ', soc_target)
            pass

        vehicle = self.connected_vehicle
        current_soc = self.connected_vehicle['soc']

        # if the battery is already charged further than the given SOC no power is needed
        if current_soc > soc_target:
            return 0

        vehicle_type = vehicle['vehicle_type']
        battery = vehicle_type.battery
        battery_capacity = battery.capacity
        timedelta_hours = timedelta.total_seconds() / 3600

        power_to_target = (soc_target - current_soc) * battery_capacity / timedelta_hours

        return power_to_target

    @staticmethod
    def check_soc(soc):
        """Make sure soc is in between [0, 1]"""
        if 0 <= soc <= 1.0:
            return True
        return False
