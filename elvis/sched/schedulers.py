""" """


class SchedulingPolicy:
    def schedule(self, config, free_connection_points, busy_connection_points):
        """Subclasses should override this with their scheduling implementation."""
        raise NotImplementedError()


class Uncontrolled(SchedulingPolicy):
    """Implements the 'Uncontrolled' scheduling policy."""

    def schedule(self, config, free_connection_points, busy_connection_points):
        """Assign maximum power to all vehicles possible in disregard of available power from
        grid. Infrastructure limits will be disregarded."""

        assign_power = {}
        resolution = config.resolution
        # All connection points without vehicle get 0 power.
        for connection_point in free_connection_points:
            assign_power[connection_point] = 0

        # For ll connection points with a connected vehicle assign max possible power
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

    def schedule(self, config, free_connection_points, busy_connection_points):
        """Assign power to all connected vehicles. Vehicle boundaries as well as infrastructure
            boundaries have to be met. The power is distributed in order of arrival time."""

        assign_power = {}
        # All connection points without vehicle get 0 power.
        for connection_point in free_connection_points:
            assign_power[connection_point] = 0

        # order all

        """go one after the other and assign max_power_possible:
        soc_target_max, hardware_max (from connection point to transformer)"""

        pass


class WithStorage(SchedulingPolicy):
    """Implements the 'Storage' scheduling policy."""

    def schedule(self, config):
        pass


class DiscriminationFree(SchedulingPolicy):
    """Implements the 'Discrimination Free' scheduling policy."""

    def schedule(self, config):
        pass


class Optimized(SchedulingPolicy):
    """Implements the 'Optimized' scheduling policy."""

    def schedule(self, config):
        pass




# all free connection point: power = 0
# all busy connection points:
#     get power with that soc = 1 can be reached -> Done
#     get power with that soc_target can be reached, if soc_target != 1 -> Done
#     get power max of hardware
#     get power minimum of hardware
#
#     assign min(maxes) to all connection points
#     check if charging point boundaries are met



        # for connection_point in busy_connection_points:
        #     soc_target = connection_point.connected_cars['soc_target']
        #     power_to_soc_target = connection_point.power_to_charge_target(time_step_size,
        #                                                                   soc_target)
        #     max_hardware_power = connection_point.max_hardware_power()
        #     min_hardware_power = connection_point.min_hardware_power()
        #
        #     # Assign max power possible based on connection point
        #     # proceed only if feasible range exists
        #     if max_hardware_power >= min_hardware_power:
        #         # if soc_target can be met this time_step assign power to do so
        #         if power_to_soc_target < max_hardware_power:
        #             assign_power[connection_point] = power_to_soc_target
        #         else:
        #             assign_power[connection_point] = max_hardware_power
        #     # if no feasible range exists: assign 0
        #     else:
        #         assign_power[connection_point] = 0
        #
        # # Check if charging point boundaries will be exceeded
        # for charging_point in charging_points:
        #     connection_points = charging_point.connection_points
        #
        #     # Add all power drawn from charging point
        #     power_sum = 0
        #     for connection_point in connection_points:
        #         power_sum += assign_power[connection_point]
        #     # if max power possible is lower than minimum power no solution can be found: assign 0
        #     if power_sum <= charging_point.min_power:
        #         for connection_point in connection_points:
        #             assign_power[connection_point] = 0
        #     elif