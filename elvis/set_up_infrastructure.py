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


def wallbox_infrastructure(num_stations, num_connections, power_connection, power_station,
                           power_transformer, min_power_connection=0, min_power_station=0,
                           min_power_transformer=0):
    """Builds an Elvis conform infrastructure.

    Args:
        num_stations: (int): Number of charging stations.
        num_connections: (int) Number of connection points per charging station.
        power_connection: (int or float): Max power per connection point.
        power_station: (int or float): Max power of the charging station.
        power_transformer: (int or float): Max power of the transformer.
        min_power_connection: (int or float): Minimum power (if not 0) for the connection point.
        min_power_station: (int or float): Minimum power (if not 0) for the charging station.
        min_power_transformer: (int or float) : Minimum power (if not 0) for the charging station.

    Returns:
        infrastructure: (dict)
    """
    # Validate Input
    assert isinstance(num_stations, int), 'Only integers are allowed for the number of charging ' \
                                          'stations.'
    assert isinstance(num_connections, int), 'Only integers are allowed for the number of ' \
                                             'connection points per charging station.'

    msg_power_numeric = 'The power assigned to the infrastructure elements must be of type int or' \
                        'float. The power must be bigger than 0.'
    assert isinstance(power_connection, (int, float)), msg_power_numeric
    assert isinstance(power_station, (int, float)), msg_power_numeric
    assert isinstance(power_transformer, (int, float)), msg_power_numeric
    assert isinstance(min_power_connection, (int, float)), msg_power_numeric
    assert isinstance(min_power_transformer, (int, float)), msg_power_numeric
    assert isinstance(min_power_station, (int, float)), msg_power_numeric

    msg_min_max = 'The min power assigned to a infrastructure node must be lower than the ' \
                  'max power.'
    assert power_connection >= min_power_connection, msg_min_max
    assert power_station >= min_power_station, msg_min_max
    assert power_transformer >= min_power_transformer, msg_min_max

    transformer = {'charging_points': [], 'id': 'transformer1',
                   'min_power': min_power_transformer, 'max_power': power_transformer}

    connection_point = {'min_power': min_power_connection, 'max_power': power_connection}

    charging_station = {'min_power': min_power_station, 'max_power': power_station,
                        'connection_points': []}

    for i in range(num_connections):
        connection_point_temp = connection_point
        connection_point_temp['id'] = 'connection_point' + str(i + 1)
        charging_station['connection_points'].append(connection_point_temp)

    for i in range(num_stations):
        charging_station_temp = charging_station
        charging_station_temp['id'] = 'connection_point' + str(i + 1)
        transformer['charging_points'].append(charging_station_temp)

    infrastructure = {'transformers': [transformer]}

    return infrastructure
