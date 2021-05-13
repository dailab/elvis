"""Create infrastructure: connect charging points to transformer and charging points to
    charging stations."""

from copy import deepcopy

from elvis.charging_station import ChargingStation
from elvis.charging_point import ChargingPoint
from elvis.infrastructure_node import Transformer, Storage
from elvis.battery import StationaryBattery


def set_up_infrastructure(infrastructure):
    """Reads in infrastructure layout as a dict and converts it into a tree shaped infrastructure
        design with nodes representing the hardware components:
            transformer: :obj: `infrastructure_node.Transformer`
            charging station: :obj: `charging_station.ChargingStation`
            charging point: :obj: `charging_point.ChargingPoint`
        Returns all charging points.

    Args:
        infrastructure: (dict): Contains more nested dicts with the values to initialise the
            infrastructure nodes.
            Dict design:
                transformer: {min_power(float), max_power(float), infrastructure(list)}

            For each instance of charging station in infrastructure:
                charging sation: {min_power(float), max_power(float), charging_points(list)}

            For each instance of charging_point in charging_stations:
                charging_point: {min_power(float), max_power(float)}

    Returns:
        charging_points: (list): Contains n instances of :obj: `charging_point.ChargingPoint`.
    """
    charging_points = []
    transformer = None
    # build infrastructure and create node instances
    # Add transformer
    for __transformer in infrastructure['transformers']:
        transformer = Transformer(__transformer['min_power'], __transformer['max_power'])
        # Add all charging points and their charging points
        for __charging_station in __transformer['charging_stations']:
            charging_station = ChargingStation(__charging_station['min_power'],
                                               __charging_station['max_power'],
                                               transformer)

            # Add all charging points of current charging point
            for __charging_point in __charging_station['charging_points']:
                __charging_point = ChargingPoint(__charging_point['min_power'],
                                                 __charging_point['max_power'],
                                                 charging_station)

                charging_points.append(__charging_point)
        if 'storage' in __transformer.keys():
            __battery = __transformer['storage']
            if 'efficiency' in __battery.keys():
                bat_eff = __battery['efficiency']
            else:
                bat_eff = 1
            battery = StationaryBattery(capacity=__battery['capacity'],
                                        max_charge_power=__battery['max_power'],
                                        min_charge_power=__battery['min_power'],
                                        efficiency=bat_eff)
            storage = Storage(battery, transformer)

    assert isinstance(transformer, Transformer), 'Invalid infrastructure dict.'
    transformer.set_up_leafs()
    # transformer.draw_infrastructure()

    return charging_points


def wallbox_infrastructure(num_cp, power_cp, num_cp_per_cs=1, power_cs=None,
                           power_transformer=None, min_power_cp=0, min_power_cs=0,
                           min_power_transformer=0):
    """Builds an Elvis conform infrastructure.

    Args:
        num_cp: (int): Number of charging points.
        num_cp_per_cs: (int) Number of charging points per charging station.
        power_cp: (int or float): Max power per charging point.
        power_cs: (int or float): Max power of the charging station.
        power_transformer: (int or float): Max power of the transformer.
        min_power_cp: (int or float): Minimum power (if not 0) for the charging point.
        min_power_cs: (int or float): Minimum power (if not 0) for the charging station.
        min_power_transformer: (int or float) : Minimum power (if not 0) for the charging station.

    Returns:
        infrastructure: (dict)
    """
    # Validate Input
    assert isinstance(num_cp_per_cs, int), 'Only integers are allowed for the number of ' \
                                           'charging points per charging station.'
    num_cs = int(num_cp / num_cp_per_cs)
    assert num_cp % num_cp_per_cs == 0, 'Only integers are allowed for the number of charging ' \
                                        'stations. The passed number of charging points and the ' \
                                        'number of charging points per charging station are not ' \
                                        'realisable.'
    num_cs = int(num_cp / num_cp_per_cs)

    msg_power_numeric = 'The power assigned to the infrastructure elements must be of type int or' \
                        'float. The power must be bigger than 0.'

    if power_cs is None:
        power_cs = power_cp * num_cp_per_cs
    assert isinstance(power_cp, (int, float)), msg_power_numeric
    assert isinstance(power_cs, (int, float)), msg_power_numeric
    if power_transformer is None:
        power_transformer = num_cs * num_cp_per_cs * power_cp
    assert isinstance(power_transformer, (int, float)), msg_power_numeric
    assert isinstance(min_power_cp, (int, float)), msg_power_numeric
    assert isinstance(min_power_transformer, (int, float)), msg_power_numeric
    assert isinstance(min_power_cs, (int, float)), msg_power_numeric

    msg_min_max = 'The min power assigned to a infrastructure node must be lower than the ' \
                  'max power.'
    assert power_cp >= min_power_cp, msg_min_max
    assert power_cs >= min_power_cs, msg_min_max
    assert power_transformer >= min_power_transformer, msg_min_max

    transformer = {'charging_stations': [], 'id': 'transformer1',
                   'min_power': min_power_transformer, 'max_power': power_transformer}

    charging_point = {'min_power': min_power_cp, 'max_power': power_cp}

    charging_station = {'min_power': min_power_cs, 'max_power': power_cs,
                        'charging_points': []}

    for i in range(num_cs):
        charging_station_temp = deepcopy(charging_station)
        charging_station_temp['id'] = 'cs' + str(i + 1)
        for j in range(num_cp_per_cs):
            charging_point_temp = deepcopy(charging_point)
            charging_point_temp['id'] = 'cp' + str(i * num_cp_per_cs + j+1)
            charging_station_temp['charging_points'].append(charging_point_temp)
        transformer['charging_stations'].append(charging_station_temp)

    infrastructure = {'transformers': [transformer]}

    return infrastructure
