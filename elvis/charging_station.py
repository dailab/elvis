"""Representation of a charging station of the infrastructure.

A charging station is the point of coupling between charging point (connection to the car)
and the grid. In LV grids the charging station immediately connects to the grid in MV grids a
transformer is needed in between.
- The charging station may consist of multiple charging points.
TODO:
    - It may be automated: After a car is charged it automatically connects itself to another car if
    available.
    - It may be inductive: No physical connection between car and charging point is needed:
    lower efficiency.
- Or manual: User have to connect and disconnect their vehicle by hand: Longer phases of inactivity.
TODO:
    - It can be operated with direct current or alternating current where different efficiencies
    have to be considered.
    - Its power is the sum over the power of its charging points.
    - It is limited by its power limits where the lower limit has to be understood as at least the
    lower limit or zero.
"""

from elvis.utility.elvis_general import floor
from elvis.infrastructure_node import InfrastructureNode


class ChargingStation(InfrastructureNode):
    """Models a charging point of the charging ingrastructure.
    """

    counter = 1

    def __init__(self, min_power, max_power, parent):
        # id
        identification = 'cs' + str(ChargingStation.counter)
        ChargingStation.counter += 1

        # power limits
        super().__init__(identification, min_power, max_power, parent=parent)

        # working principle
        self.manual = True
        self.automated = False
        self.inductive = False

        # power type AC = True, DC = False
        self.ac_power_supply = True

        self.efficiency = 1

    def __str__(self):
        return str(self.id)

    def max_hardware_power(self, power_assigned):
        """Determine max power possible to be assigned dependent on charging station limits and
            power already assigned to charging points connected to the charging station.
            Current simplification: Charging points always are directly connected to charging
            stations.

            Args:
                power_assigned: (dict): Contains all :obj: `charging_point.ChargingPoint` and
                    their currently already assigned power.
        """

        power_cps = 0
        for leaf in self.leafs:
            power_cps += power_assigned[leaf]

        max_power = self.max_power - power_cps
        max_power = floor(max_power)

        return max_power
