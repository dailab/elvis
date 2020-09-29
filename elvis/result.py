import logging
from elvis.connection_point import ConnectionPoint


class ElvisResult:
    """Represents the result of an Elvis simulation. 

    Don't use this directly, instead pass it to one of the provided functions for evaluating Elvis results.
    """

    def __init__(self):
        self.power_connection_points = {}

    def store_power_connection_points(self, power_connection_points, pos_current_time_stamp):
        """Adds the key pos_current_time_stamp and the power assigned to the individual connection
            point to self.power_connection_points if the assigned power is not 0.

            Args:
                power_connection_points: (dict): Containing the connection points as keys as type
                    :obj: `connection_point.ConnectionPoint`. Values are the powers to be assigned
                    as float.
                pos_current_time_stamp: (int): Position of the current time stamp in the list
                    containing all time stamps.
        """
        for connection_point in power_connection_points:
            assert isinstance(connection_point, ConnectionPoint)

            power = power_connection_points[connection_point]
            if power != 0:
                if connection_point.id not in self.power_connection_points:
                    self.power_connection_points[connection_point.id] = {}
                self.power_connection_points[connection_point.id][pos_current_time_stamp] = power

    def to_yaml(self):
        """Serialize this ElvisResult to a yaml string."""

        pass

    def to_csv(self, file_name):
        """Serialize this ElvisResult to a CSV file."""

        pass

    @staticmethod
    def from_yaml(yaml_str):
        """Create an ElvisResult from a yaml string."""

        pass

    @staticmethod
    def from_json(json_str):
        """Create an ElvisResult from a yaml string."""

        pass

    @staticmethod
    def from_csv(file_name):
        """Create an ElvisResult from a CSV file."""

        pass
