import logging
from elvis.connection_point import ConnectionPoint


class ElvisResult:
    """Represents the result of an Elvis simulation. 

    Don't use this directly, instead pass it to one of the provided functions for evaluating Elvis results.
    """

    def __init__(self):
        self.power_connection_points = {}

    def store_power_connection_points(self, power_connection_points):
        """Append the lists containing the powers assigned in every time step.
            Called by simulate() each time_step.
            Args:
                - power_connection_points: (dict): Containing the connection points as keys as type
                    :obj: `connection_point.ConnectionPoint`. Values are the powers to be assigned
                    as float.
        """
        for connection_point in power_connection_points:
            assert isinstance(connection_point, ConnectionPoint)
            # append list containing the power of the connection points
            try:
                power = power_connection_points[connection_point]
                self.power_connection_points[connection_point.id].append(power)
            # if connection point not in dict add
            except KeyError:
                power = power_connection_points[connection_point]
                self.power_connection_points[connection_point.id] = [power]

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
