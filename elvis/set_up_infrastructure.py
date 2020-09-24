"""Create infrastructure: connect charging points to transformer and connection points to
    charging points."""

from elvis.charging_point import ChargingPoint
from elvis.connection_point import ConnectionPoint
from elvis.infrastructure_node import Transformer


def set_up_infrastructure(infrastructure):
    """Reads in infrastructure layout as a dict and converts it into a tree shaped infrastructure
        design with nodes representing the hardware components:
            transformer: :obj: `infrastructure_node.Transformer`
            charging point: :obj: `charging_point.ChargingPoint`
            connection point: :obj: `connection_point.ConnectionPoint`
        Returns all connection points.

    Args:
        infrastructure: (dict): Contains more nested dicts with the values to initialise the
            infrastructure nodes.
            Dict design:
                transformer: {min_power(float), max_power(float), infrastructure(list)}

            For each instance of charging_point in infrastructure:
                charging_point: {min_power(float), max_power(float), connection_points(list)}

            For each instance of connection_point in connection_points:
                connection_point: {min_power(float), max_power(float)}

    Returns:
        connection_points: (list): Contains n instances of :obj: `connection_point.ConnectionPoint`.
    """
    connection_points = []
    # build infrastructure and create node instances
    # Add transformer
    for __transformer in infrastructure['transformers']:
        transformer = Transformer(__transformer['min_power'], __transformer['max_power'])
        # Add all charging points and their connection points
        for __charging_point in __transformer['charging_points']:
            charging_point = ChargingPoint(__charging_point['min_power'],
                                           __charging_point['max_power'],
                                           transformer)
            transformer.add_child(charging_point)
            # Add all connection points of current charging point
            for __connection_point in __charging_point['connection_points']:
                __connection_point = ConnectionPoint(__connection_point['min_power'],
                                                     __connection_point['max_power'],
                                                     charging_point)
                charging_point.add_child(__connection_point)
                connection_points.append(__connection_point)

    transformer.set_up_leafs()
    # transformer.draw_infrastructure()

    return connection_points
