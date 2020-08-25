"""Connection point representation.

A connection point links the charging infrastructure to the charging vehicles.
It is limited by its power limits where as the lower limit has to be understood as at least the
lower limit or zero.

"""


class ConnectionPoint:
    """Represents a point of connection between :obj: `charging_point.ChargingPoint` and
    vehicles."""

    counter = 1

    def __init__(self, limits, charging_point):
        """Create a connection point given all parameters.

        Args:
            limits: (tuple): (minimum power level as float, maximium power level as float)
            charging_point: (:obj: `charging_point.ChargingPoint`): Charging point the connection
            point belongs to.
            """
        self.id = 'Connection point: ' + str(ConnectionPoint.counter)
        ConnectionPoint.counter += 1

        self.max_power = limits[0]
        self.min_power = limits[1]

        self.connected_vehicle = None

        self.charging_point = charging_point

    def __str__(self):
        printout = str(self.id) + ' ' + str(self.connected_vehicle)
        return printout

    def connect_vehicle(self, event):
        """Assign dict of charging event as connected vehicle.

        Args:
            event: (:obj: `charging_event.ChargingEvent): Event of car arrival."""
        self.connected_vehicle = event.to_dict()

    def disconnect_vehicle(self):
        """Set field connected_vehicle to None so connection point is available for
            vehicle connection."""
        self.connected_vehicle = None
