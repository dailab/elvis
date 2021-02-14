""" """
from elvis.infrastructure_node import Transformer, Storage
from elvis.charging_point import ChargingPoint
from elvis.utility.elvis_general import floor


class SchedulingPolicy:
    def __init__(self):
        self.state = None

    def schedule(self, config, free_cps, busy_cps):
        """Subclasses should override this with their scheduling implementation."""
        raise NotImplementedError()

    @staticmethod
    def get_storage_system(free_cps, busy_cps):
        """Returns the storage_system from the infrastructure by accessing a charging point.
        Free cps and busy cps necessary since both (not at the same time) could be empty sets."""

        transformer = SchedulingPolicy.get_transformer(free_cps, busy_cps)

        storage_system = None
        for child in transformer.children:
            if isinstance(child, Storage):
                storage_system = child
        return storage_system

    @staticmethod
    def get_transformer(free_cps, busy_cps):
        """Returns the transformer from the infrastructure by accessing a charging point.
        Free cps and busy cps necessary since both (not at the same time) could be empty sets."""

        if len(free_cps) > 0:
            rand_cp = free_cps.copy().pop()
            assert isinstance(rand_cp, ChargingPoint), 'Sets should contain cps.'
            transformer = rand_cp.get_transformer()
        else:
            rand_cp = busy_cps.copy().pop()
            assert isinstance(rand_cp, ChargingPoint), 'Sets should contain cps.'
            transformer = rand_cp.get_transformer()

        return transformer


class Uncontrolled(SchedulingPolicy):
    """Implements the 'Uncontrolled' scheduling policy."""

    def __str__(self):
        return 'Uncontrolled'

    def schedule(self, config, free_cps, busy_cps, time_steps_pos=0):
        """Assign maximum power to all vehicles possible in disregard of available power from
        grid. Infrastructure limits will be disregarded."""

        assign_power = {'cps': {cp: 0 for cp in set.union(free_cps, busy_cps)}}
        assign_power['storage'] = {}
        resolution = config.resolution

        transformer = SchedulingPolicy.get_transformer(free_cps, busy_cps)
        storage_system = SchedulingPolicy.get_storage_system(free_cps, busy_cps)

        total_power = 0

        # For all charging points with a connected vehicle assign max possible power
        for cp in busy_cps:
            power_cp = cp.max_power
            connected_vehicle = cp.connected_vehicle
            soc = connected_vehicle['soc']
            battery = connected_vehicle['vehicle_type'].battery
            # Max power the battery can charge with at current SOC
            max_power_battery = battery.max_power_possible(soc)
            # Power needed to fully charge battery
            power_to_charge_full = cp.power_to_charge_target(resolution, 1.0)
            # Get the stricter constraint
            power = (min(max_power_battery, power_to_charge_full, power_cp))
            assign_power['cps'][cp] = power
            total_power += power

        # If power assigned is higher than transformer limit
        if storage_system is not None:
            if total_power > transformer.max_power:
                max_storage = storage_system.storage.max_discharge_power(0, resolution)
                # The power from the storage system is not able to cover the whole transformer overhead
                if max_storage < total_power - transformer.max_power:
                    assign_power['storage'][storage_system] = - max_storage
                # Storage covers the transformer overhead
                else:
                    storage_discharge_load = - floor(total_power - transformer.max_power)
                    assign_power['storage'][storage_system] = storage_discharge_load
            # Transformer is able to cover load by itself
            else:
                assign_power['storage'][storage_system] = 0

        return assign_power


class FCFS(SchedulingPolicy):
    """Implements the 'First Come First Serve' scheduling policy."""

    def __str__(self):
        return 'FCFS'

    def schedule(self, config, free_cps, busy_cps, time_step_pos=0):
        """Assign power to all connected vehicles. Vehicle boundaries as well as infrastructure
            boundaries have to be met. The power is distributed in order of arrival time.
            """

        assign_power = {'cps': {cp: 0 for cp in set.union(free_cps, busy_cps)}}
        assign_power['storage'] = {}
        resolution = config.resolution
        preload = config.transformer_preload[time_step_pos]

        # All charging points with a connected vehicle assign max possible power
        sorted_busy_cps = list(busy_cps)
        sorted_busy_cps.sort(key=lambda x: x.connected_vehicle['leaving_time'])

        # Get transformer and storage system
        storage_system = SchedulingPolicy.get_storage_system(free_cps, busy_cps)
        if storage_system is not None:
            assign_power['storage'][storage_system] = 0
        transformer = SchedulingPolicy.get_transformer(free_cps, busy_cps)

        # Sum all power that is assigned in order to identify which power must be delivered by
        # the storage based on the initial transformer maximum
        total_power_assigned = 0
        max_power_transformer_0 = transformer.max_hardware_power(assign_power['cps'], preload)
        power_storage = 0
        max_power_storage = 0

        for cp in sorted_busy_cps:
            # check what the max power possible from vehicle to grid is based on hardware
            # and the already assigned power of every component (node)
            max_hardware_power = cp.max_hardware_power()
            parent = cp
            go_on = True
            while go_on is True:
                if parent.parent is not None:
                    parent = parent.parent
                    # If the parent is the Transformer: Also pass preload
                    if isinstance(parent, Transformer):
                        max_power_transformer = parent.max_hardware_power(assign_power['cps'],
                                                                          preload)
                        if storage_system is not None:
                            max_power_storage = \
                                storage_system.storage.max_discharge_power(power_storage,
                                                                           resolution)
                            power_available = max_power_transformer + max_power_storage
                        else:
                            power_available = max_power_transformer
                        power_available = floor(power_available)
                        max_hardware_power = min(max_hardware_power, power_available)
                    else:
                        max_hardware_power = min(max_hardware_power,
                                                 parent.max_hardware_power(assign_power['cps']))
                else:
                    go_on = False

            power_to_charge_full = floor(cp.power_to_charge_target(resolution, 1.0))
            power = min(power_to_charge_full, max_hardware_power)
            total_power_assigned += power
            if total_power_assigned > max_power_transformer_0 and max_power_storage != 0:
                power_storage = total_power_assigned - max_power_transformer_0
                power_storage = floor(power_storage)

            assign_power['cps'][cp] = power
        if storage_system is not None:
            assign_power['storage'][storage_system] = -power_storage

        return assign_power


class WithStorage(SchedulingPolicy):
    """Implements the 'Storage' scheduling policy."""

    def __str__(self):
        return 'With Storage'

    def schedule(self, config, free_cps, busy_cps, time_step_pos=0):
        pass


class DiscriminationFree(SchedulingPolicy):
    """Implements the 'Discrimination Free' scheduling policy."""

    def __str__(self):
        return 'Discrimination Free'

    def schedule(self, config, free_cps, busy_cps, time_step_pos=0):
        assign_power = {'cps': {cp: 0 for cp in set.union(free_cps, busy_cps)}}
        assign_power['storage'] = {}
        resolution = config.resolution
        preload = config.transformer_preload[time_step_pos]

        self.update_state(busy_cps, config)
        sorted_busy_cps = self.sort_cps(config)

        storage_system = SchedulingPolicy.get_storage_system(free_cps, busy_cps)
        if storage_system is not None:
            assign_power['storage'][storage_system] = 0
        transformer = SchedulingPolicy.get_transformer(free_cps, busy_cps)

        # Sum all power that is assigned in order to identify which power must be delivered by
        # the storage based on the initial transformer maximum
        total_power_assigned = 0
        max_power_transformer_0 = transformer.max_hardware_power(assign_power['cps'], preload)
        power_storage = 0
        max_power_storage = 0

        for cp in sorted_busy_cps:
            # check what the max power possible from vehicle to grid is based on hardware
            # and the already assigned power of every component (node)
            max_hardware_power = cp.max_hardware_power()
            parent = cp
            go_on = True
            while go_on is True:
                if parent.parent is not None:
                    parent = parent.parent
                    # If the parent is the Transformer: Also pass preload
                    if isinstance(parent, Transformer):
                        max_power_transformer = parent.max_hardware_power(assign_power['cps'],
                                                                          preload)
                        if storage_system is not None:
                            max_power_storage = \
                                storage_system.storage.max_discharge_power(power_storage,
                                                                           resolution)
                            power_available = max_power_transformer + max_power_storage
                        else:
                            power_available = max_power_transformer
                        power_available = floor(power_available)
                        max_hardware_power = min(max_hardware_power, power_available)
                    else:
                        max_hardware_power = min(max_hardware_power,
                                                 parent.max_hardware_power(assign_power['cps']))
                else:
                    go_on = False

            power_to_charge_full = floor(cp.power_to_charge_target(resolution, 1.0))
            power = min(power_to_charge_full, max_hardware_power)
            total_power_assigned += power
            if total_power_assigned > max_power_transformer_0 and max_power_storage != 0:
                power_storage = total_power_assigned - max_power_transformer_0
                power_storage = floor(power_storage)
            if power == power_to_charge_full:  # car is limiting factor: charged within time step
                self.state[cp]['times_charged'] = self.state[cp]['times_charged'] + 1
            elif power < cp.max_hardware_power():
                pass  # infrastructure is limiting factor: handle as if not charged within time step
            else:  # car or charging point is limiting factor: charged within time step
                self.state[cp]['times_charged'] = self.state[cp]['times_charged'] + 1

            assign_power['cps'][cp] = power
        if storage_system is not None:
            assign_power['storage'][storage_system] = -power_storage

        return assign_power

    def sort_cps(self, config):
        secs_to_charge_constantly = config.df_charging_period.total_seconds()
        secs_per_step = config.resolution.total_seconds()
        time_steps_to_charge_in_a_row = int(max(secs_to_charge_constantly/secs_per_step, 1))

        state_list = list(self.state)
        # sort: with priority if sth is still in a charging window (time_steps_to_charge_in_a_row)
        # and secondly by the amount of times already charged
        state_list.sort(key=lambda x: self.state[x]['times_charged'] /
                        time_steps_to_charge_in_a_row)
        state_list.sort(key=lambda x: round((self.state[x]['times_charged'] /
                                             time_steps_to_charge_in_a_row) % 1, 2), reverse=True)

        return state_list

    def update_state(self, cps, config):
        if self.state is not None:
            state_keys = self.state.keys()

            # min_times_charged necessary to ensure cars that got just connected are not always
            # charged with priority
            if len(self.state) > 0:
                times_charged = [self.state[x]['times_charged'] for x in self.state]
                min_times_charged = floor(min(times_charged), 0)  # floor to integer
            else:
                min_times_charged = 0

            # update state
            secs_to_charge_constantly = config.df_charging_period.total_seconds()
            secs_per_step = config.resolution.total_seconds()
            time_steps_to_charge_in_a_row = int(max(secs_to_charge_constantly / secs_per_step, 1))
            for cp in self.state.copy():
                # to make sure the values don't rise endlessly
                sub = min_times_charged - min_times_charged % time_steps_to_charge_in_a_row
                self.state[cp]['times_charged'] = self.state[cp]['times_charged'] - sub

                # check that state has no cars that are not connected anymore
                if cp not in cps:
                    del self.state[cp]
                # make sure that the connected car has not changed
                else:
                    state_id = self.state[cp]['id']
                    look_up_cps = list(cps)
                    vehicle_id = look_up_cps[look_up_cps.index(cp)].connected_vehicle['id']

                    # update car if it changed
                    if state_id is not vehicle_id:
                        self.state[cp]['id'] = vehicle_id
                        self.state[cp]['times_charged'] = 0

            # check that state has all cars currently connected
            for cp in cps:
                if cp not in state_keys:
                    self.state[cp] = {'id': cp.connected_vehicle['id'],
                                      'times_charged': 0}

        else:  # will only be called once for initialisation
            self.state = dict()
            for cp in cps:

                self.state[cp] = {'id': cp.connected_vehicle['id'],
                                  'times_charged': 0}

        return




class Optimized(SchedulingPolicy):
    """Implements the 'Optimized' scheduling policy."""

    def __str__(self):
        return 'Optimized'

    def schedule(self, config):
        pass