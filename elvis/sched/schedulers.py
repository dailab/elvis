""" """
from elvis.infrastructure_node import Transformer


class SchedulingPolicy:
    def schedule(self, config, free_connection_points, busy_connection_points):
        """Subclasses should override this with their scheduling implementation."""
        raise NotImplementedError()


class Uncontrolled(SchedulingPolicy):
    """Implements the 'Uncontrolled' scheduling policy."""

    def __str__(self):
        return 'Uncontrolled'

    def schedule(self, config, free_connection_points, busy_connection_points, time_steps_pos=0):
        """Assign maximum power to all vehicles possible in disregard of available power from
        grid. Infrastructure limits will be disregarded."""

        assign_power = {}
        resolution = config.resolution
        # All connection points without vehicle get 0 power.
        for connection_point in free_connection_points:
            assign_power[connection_point] = 0

        # For all connection points with a connected vehicle assign max possible power
        for connection_point in busy_connection_points:
            connected_vehicle = connection_point.connected_vehicle
            soc = connected_vehicle['soc']
            battery = connected_vehicle['vehicle_type'].battery
            # Max power the battery can charge with at current SOC
            max_power_battery = battery.max_power_possible(soc)
            # Power needed to fully charge battery
            power_to_charge_full = connection_point.power_to_charge_target(resolution, 1.0)
            # Get the stricter constraint
            power = (min(max_power_battery, power_to_charge_full))
            assign_power[connection_point] = power

        return assign_power


class FCFS(SchedulingPolicy):
    """Implements the 'First Come First Serve' scheduling policy."""

    def __str__(self):
        return 'FCFS'

    def schedule(self, config, free_connection_points, busy_connection_points, time_step_pos=0):
        """Assign power to all connected vehicles. Vehicle boundaries as well as infrastructure
            boundaries have to be met. The power is distributed in order of arrival time.
            """

        assign_power = {cp: 0 for cp in set.union(free_connection_points, busy_connection_points)}
        resolution = config.resolution
        preload = config.transformer_preload[time_step_pos]

        # All connection points with a connected vehicle assign max possible power
        sorted_busy_connection_points = list(busy_connection_points)
        # TODO: Does only work if there is a connected vehicle (do we need an error handling here?)
        sorted_busy_connection_points.sort(key=lambda x: x.connected_vehicle['leaving_time'])
        for connection_point in sorted_busy_connection_points:
            # check what the max power possible from vehicle to grid is based on hardware
            # and the already assigned power of every component (node)
            max_hardware_power = connection_point.max_hardware_power()
            parent = connection_point
            go_on = True
            while go_on is True:
                if parent.parent is not None:
                    parent = parent.parent
                    # If the parent is the Transformer: Also pass preload
                    if isinstance(parent, Transformer):
                        max_hardware_power = min(max_hardware_power,
                                                 parent.max_hardware_power(assign_power, preload))
                    else:
                        max_hardware_power = min(max_hardware_power,
                                                 parent.max_hardware_power(assign_power))
                else:
                    go_on = False

            power_to_charge_full = connection_point.power_to_charge_target(resolution, 1.0)
            power = min(power_to_charge_full, max_hardware_power)

            assign_power[connection_point] = power




        """go one after the other and assign max_power_possible:
        soc_target_max, hardware_max (from connection point to transformer)"""

        return assign_power


class WithStorage(SchedulingPolicy):
    """Implements the 'Storage' scheduling policy."""

    def __str__(self):
        return 'With Storage'

    def schedule(self, config):
        pass


class DiscriminationFree(SchedulingPolicy):
    """Implements the 'Discrimination Free' scheduling policy."""

    def __str__(self):
        return 'Discrimination Free'

    def schedule(self, config):
        pass


class Optimized(SchedulingPolicy):
    """Implements the 'Optimized' scheduling policy."""

    def __str__(self):
        return 'Optimized'

    def schedule(self, config):
        pass