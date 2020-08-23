"""Create infrastructure: connect charging points to transformer and connection points to
    charging points."""

from charging_point import ChargingPoint


def set_up_charging_points(cp_setup):
    """Turns list with n integers x into list of n charging points with x connections points.

    Args:
        cp_setup: (list): Instance represents the amount of connection points for that
            charging point.

    Returns:
        charging_points: (list): Contains n instances of :obj: `ChargingPoint`.
    """

    charging_points = []
    for elem in cp_setup:
        charging_points.append(ChargingPoint(elem))

    return charging_points
