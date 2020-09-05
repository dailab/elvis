"""Representation of a charging point of the infrastructure.

A charging point is the point of coupling between connection point (connection to the car)
and the grid. In LV grids the charging point immediately connects to the grid in MV grids a
transformer is needed in between.
- The charging point may consist of multiple connection points.
TODO:
    - It may be automated: After a car is charged it automatically connects itself to another car if
    available.
    - It may be inductive: No physical connection between car and connection point is needed:
    lower efficiency.
- Or manual: User have to connect and disconnect their vehicle by hand: Longer phases of inactivity.
TODO:
    - It can be operated with direct current or alternating current where different efficiencies
    have to be considered.
    - Its power is the sum over the power of its connection points.
    - It is limited by its power limits where the lower limit has to be understood as at least the
    lower limit or zero.
"""

#from elvis.connection_point import ConnectionPoint
from elvis.infrastructure_node import InfrastructureNode


class ChargingPoint(InfrastructureNode):
    """Models a charging point of the charging ingrastructure.

    TODO:
        - Get values from config.
    """

    counter = 1

    def __init__(self, min_power, max_power, parent):
        # id
        identification = 'Charging point_' + str(ChargingPoint.counter)
        ChargingPoint.counter += 1

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

    # def set_connection_points_static(self, n):
    #     """Create n connection points.
    #     With static values for power limits
    #
    #     Args:
    #         n: (int): Number of connection points to be created.
    #
    #     Returns:
    #         connection_points: (list): Containing the connection points as instances from
    #         :obj: `ConnectionPoint`.
    #     """
    #     connection_points = []
    #
    #     while n > 0:
    #         n -= 1
    #         connection_points.append(ConnectionPoint((2, 5), self))
    #     return connection_points
