from numpy import histogram
from datetime import timedelta
import numpy as np
from elvis.charging_point import ChargingPoint
from elvis.config import ScenarioRealisation
from elvis.utility.elvis_general import num_time_steps, create_time_steps
from elvis.distribution import EquallySpacedInterpolatedDistribution
from elvis.infrastructure_node import Storage


class ElvisResult:
    """Represents the result of an Elvis simulation. 

    Don't use this directly, instead pass it to one of the provided functions for evaluating Elvis
    results.
    """

    def __init__(self, scenario=None, realisation_file_name=None):
        self.power_charging_points = {}
        self.power_storage_systems = {}
        self.aggregated_load_profile = None
        self.counter_rejections = 0
        self.charging_periods = None

        # used to cache the last saved timestamp for each charging point
        self._last_stored_cp_power = {}
        # used to cache the last save timestamp for the storage system
        self._last_stored_storage_power = {}

        if scenario is not None:
            assert isinstance(scenario, ScenarioRealisation), 'Result.scenario must be of type ' \
                                                              'ScenarioRealisation'
        self.scenario = scenario

        if realisation_file_name is not None:
            assert self.scenario is not None, 'To store the simulated ScenarioRealisation the ' \
                                              'scenario must be passed as type of ' \
                                              'ScenarioRealisation.'
            self.scenario.save_to_disk(r'../data/realisations/' + str(realisation_file_name))

    def store_power_charging_points(self, power_charging_points, pos_current_time_stamp, is_last_step):
        """Adds the key pos_current_time_stamp and the power assigned to the individual charging
            point to self.power_charging_points if the assigned power is not 0.

            Args:
                power_charging_points: (dict): Containing the charging points as keys as type
                    :obj: `cp.ChargingPoint`. Values are the powers to be assigned
                    as float.
                pos_current_time_stamp: (int): Position of the current time stamp in the list
                    containing all time stamps.
        """
        for cp in power_charging_points:
            assert isinstance(cp, ChargingPoint)

            power = power_charging_points[cp]
            
            if cp.id not in self.power_charging_points:
                self.power_charging_points[cp.id] = {}
            elif not is_last_step and (cp.id in self._last_stored_cp_power):
                if self._last_stored_cp_power[cp.id] == power:
                    continue
            
            self._last_stored_cp_power[cp.id] = power
            self.power_charging_points[cp.id][pos_current_time_stamp] = power

    def store_power_storage_systems(self, power_storage_systems, pos_current_time_stamp, is_last_step):
        """Saves the power assigned to the storage system in each time step.

        Args:
            power_storage_systems: (dict)): Power assigned to all storage systems.
            pos_current_time_stamp: (int): Current time step.
            is_last_step: (bool): Denotes whether the end of the simulation is reached.

        """

        for storage_system in power_storage_systems:
            assert isinstance(storage_system, Storage)

            power = power_storage_systems[storage_system]

            if storage_system.id not in self.power_storage_systems:
                self.power_storage_systems[storage_system.id] = {}
            elif not is_last_step and (storage_system.id in self._last_stored_storage_power):
                if self._last_stored_storage_power[storage_system.id] == power:
                    continue

            self._last_stored_storage_power[storage_system.id] = power
            self.power_storage_systems[storage_system.id][pos_current_time_stamp] = power

    def to_yaml(self):
        """Serialize this ElvisResult to a yaml string."""

        pass

    def to_csv(self, file_name):
        """Serialize this ElvisResult to a CSV file."""

        pass

    def aggregate_load_profile(self, num_simulation_steps=None):

        if num_simulation_steps is None:
            assert self.scenario is not None, 'If using result.aggregate_load_profile without ' \
                                              'passing the number of simulation steps the ' \
                                              'field result.scenario must be set to the scenario ' \
                                              'realisation.'

            num_simulation_steps = num_time_steps(self.scenario.start_date, self.scenario.end_date,
                                                  self.scenario.resolution)
        load_profile = []
        power = {}
        for time_step in range(num_simulation_steps):
            for cp in self.power_charging_points:
                if time_step in self.power_charging_points[cp].keys():
                    power[cp] = self.power_charging_points[cp][time_step]

            load_profile.append(sum(power.values()))

        self.aggregated_load_profile = load_profile

        return load_profile

    def get_storage_profile(self, num_simulation_steps=None):

        if num_simulation_steps is None:
            assert self.scenario is not None, 'If using result.get_storage_profile without ' \
                                              'passing the number of simulation steps the ' \
                                              'field result.scenario must be set to the scenario ' \
                                              'realisation.'

            num_simulation_steps = num_time_steps(self.scenario.start_date, self.scenario.end_date,
                                                  self.scenario.resolution)
        storage_profile = []
        power = {}
        for time_step in range(num_simulation_steps):
            for stor in self.power_storage_systems:
                if time_step in self.power_storage_systems[stor].keys():
                    power[stor] = self.power_storage_systems[stor][time_step]

            storage_profile.append(sum(power.values()))

        return storage_profile


    def total_energy_charged(self, resolution, num_simulation_steps=None):

        assert isinstance(resolution, timedelta)
        if self.aggregated_load_profile is not None:
            self.aggregate_load_profile(num_simulation_steps)

        load_profile = self.aggregated_load_profile

        energy = sum(load_profile)

        # convert to kWh
        energy /= 3600 / resolution.total_seconds()

        return energy

    def max_load(self):
        """Calculates the max load of an aggregated load profile:

            max_load: (float): Max load that is generated by the charging infrastructure.
        """
        assert self.aggregated_load_profile is not None, 'Before calculating KPIs the aggreagated' \
                                                         'load profile must be calculated.'
        return max(self.aggregated_load_profile)

    def simultaneity_factor(self, infrastructure=None, bins=None, quantile=None):
        """Calculates the simultaneity factor of the infrastructure.
            If bins is specified a histogram is returned.
            If bins is None only the max value is returned.

            The simultaneity factor for each time step is calculated via:
                (power assigned to all charging points) / (nominal power of all charging points)
            Args:
                infrastructure: (dict): Elvis conform infrastructure from which the nominal power
                    of all charging points is generated from.
                bins: (list): Containing the values for the bins as per numpy.histogram.

            returns.
                simultaneity_factor: (list or float):
                    If bins == None:
                        Float representing the max simultaneity that was reached over the simulation
                        period.
                    If bins is not None:
                        list of tuples containing the bin and the amount of time steps in which the
                        simultaneity factor is within that bin.
                """

        if (infrastructure is None) and (self.scenario is not None):
            infrastructure = self.scenario.infrastructure
        elif infrastructure is None and self.scenario is None:
            raise ValueError('If no scenario is stored in result an infrastructure has to be passed'
                             'to simultaneity factor to calculate the nominal power of the '
                             'charging points.')

        if self.aggregated_load_profile is None:
            assert self.scenario is not None, 'To calculate the simultaneity_factor the ' \
                                               'aggregated load profile must be calculated.'

            time_steps = num_time_steps(self.scenario.start_date, self.scenario.end_date,
                                        self.scenario.resolution)

            self.aggregate_load_profile(time_steps)
        assert self.aggregated_load_profile is not None, 'Before calculating KPIs the aggregated' \
                                                         'load profile must be calculated.'

        if (bins is None) and (quantile is None):
            power_hardware_max = self.get_power_charging_points(infrastructure)
            power_max = self.max_load()
            return power_max / power_hardware_max
        elif (bins is None) and not (quantile is None):
            power_hardware_max = self.get_power_charging_points(infrastructure)
            cf = np.array(self.aggregated_load_profile)/power_hardware_max
            return np.quantile(cf, q=quantile)
        else:
            power_hardware_max = self.get_power_charging_points(infrastructure)
            sim = [i / power_hardware_max for i in self.aggregated_load_profile]
            hist = histogram(sim, bins)
            return list(zip(hist[0], hist[1]))

    def electricity_costs_fix(self, electricity_rate):
        """Calculates the total electricity costs based on the electricity received from the grid
        assuming a constant electricity rate.

        Args:
            electricity_rate: (float): Costs per kWh.

        Returns:
            electricity_costs: (float): Total costs of electricity.

        TODO:
            - Storage integration
            - PV integration
        """

        total_energy = self.total_energy_charged()
        electricity_costs = total_energy * electricity_rate

        return electricity_costs

    def electricity_costs_24_variable(self, variable_electricity_rate):
        """Calculates the total electricity costs based on the electricity receives from the grid
        assuming a variable electricity during a day. This intraday cost distribution is assumed to
        be same for every day of the simulation.

        Args:
            variable_electricity_rate: (list): Containing floats representing the costs of
            electricity during one day.

        Returns:
            electricity_costs: (float): Total costs of electricity.

        TODO:
            - Storage integration
            - PV integration
        """

        assert type(variable_electricity_rate) == list, 'The variable electricity rate must be of '\
                                                        'type list.'

        msg_invalid_value_type = "Arrival distribution should be of type: pandas DataFrame or a " \
                                 "list containing float or int."

        # Check that all values in list are either float or int
        assert all(isinstance(x, (float, int)) for x in variable_electricity_rate), \
            msg_invalid_value_type

        time_coeff = 24/len(variable_electricity_rate)
        hour_stamps_costs = [x * time_coeff for x in range(len(variable_electricity_rate))]

        # Repeat first cost value
        hour_stamps_costs.append(24 + hour_stamps_costs[0])
        variable_electricity_rate.append(variable_electricity_rate[0])
        cost_distr = EquallySpacedInterpolatedDistribution.linear(
            list(zip(hour_stamps_costs, variable_electricity_rate)), None)

        time_stamps = create_time_steps(self.scenario.start_date, self.scenario.end_date,
                                        self.scenario.resolution)

        load_profile = self.aggregate_load_profile()

        electricity_costs = 0
        for i in list(range(len(load_profile))):
            p = load_profile[i]
            # get time stamp
            current_time_stamp = time_stamps[i]
            # calc the time in hours
            seconds = current_time_stamp.hour * 3600 + current_time_stamp.minute * 60 + \
                      current_time_stamp.second + current_time_stamp.microsecond / 1000000
            x_pos_time_stamp = seconds / 3600
            # lookup the price at the current time (linearly interpolated)
            price = cost_distr[x_pos_time_stamp]
            # add costs
            electricity_costs += p * price

        return electricity_costs

    def total_emissions(self):
        assert self.scenario is not None, 'Scenario in result must be specified in order to ' \
                                          'calculate the emissions.'
        assert self.scenario.emissions_scenario is not None, 'There must be a emissions_scenario ' \
                                                             'specified in order to calculate ' \
                                                             'emissions.'

        load_profile = self.aggregate_load_profile()
        emissions = self.scenario.emissions_scenario

        total_emissions = 0
        for i in range(len(load_profile)):
            total_emissions += load_profile[i] * emissions[i]

        return total_emissions

    def average_charging_time(self, in_hours=False):
        """Calculated the average parking time.
        Definition: The average time between the first time the car is charged and the last time.

        Args:
            in_hours: (bool): If true return average charging time as hours (float).
        Returns:
            average_charging_time: (datetime.timedelta): Mean time needed to charge a car.
        """

        assert self.charging_periods is not None, 'Charging periods must be assigned.'
        assert isinstance(self.charging_periods, dict), 'Charging periods should be of type dict.'

        event_counter = 0
        seconds = 0
        for event in self.charging_periods:
            event_counter += 1
            end = self.charging_periods[event]['last_charged']
            start = self.charging_periods[event]['arrival']
            seconds += (end - start).total_seconds()

        if in_hours is True:
            return seconds/3600/event_counter

        return timedelta(seconds=seconds/event_counter)

    def charging_time_histogram(self, bins=None):
        """Returns data for a charging time histogram"""

        assert self.charging_periods is not None, 'Charging periods must be assigned.'
        assert isinstance(self.charging_periods, dict), 'Charging periods should be of type dict.'

        charging_times = []
        for event in self.charging_periods:
            end = self.charging_periods[event]['last_charged']
            start = self.charging_periods[event]['arrival']
            minutes = (end - start).total_seconds() / 60
            charging_times.append(minutes)

        if bins is not None:
            hist = histogram(charging_times, bins)
        else:
            hist = histogram(charging_times)

        return list(zip(hist[0], hist[1]))

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

    @staticmethod
    def get_power_charging_points(infrastructure):
        """Sums over the power of all charging points in an Elvis conform infrastructure dict.

        Args:
            infrastructure: Elvis conform infrastructure dict.

        Returns:
            power_sum: (float): Sum over the power of all charging points.
        """
        msg_wrong_infrastructure = "Infrastructure must be Elvis conform."
        assert isinstance(infrastructure, dict), msg_wrong_infrastructure
        assert 'transformers' in infrastructure.keys(), msg_wrong_infrastructure
        power_sum = 0
        for transformer in infrastructure['transformers']:
            assert 'charging_stations' in transformer.keys(), msg_wrong_infrastructure
            for charging_station in transformer['charging_stations']:
                assert 'charging_points' in charging_station.keys(), msg_wrong_infrastructure
                for cp in charging_station['charging_points']:
                    assert 'max_power' in cp.keys()
                    assert isinstance(cp['max_power'], (float, int))
                    power_sum += cp['max_power']

        return power_sum
