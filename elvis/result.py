import logging
from numpy import histogram
from elvis.connection_point import ConnectionPoint
from elvis.config import ScenarioConfig, ScenarioRealisation
from elvis.utility.elvis_general import num_time_steps


class ElvisResult:
    """Represents the result of an Elvis simulation. 

    Don't use this directly, instead pass it to one of the provided functions for evaluating Elvis
    results.
    """

    def __init__(self, scenario=None, realisation_file_name=None):
        self.power_connection_points = {}
        self.aggregated_load_profile = None

        if scenario is not None:
            assert isinstance(scenario, ScenarioRealisation), 'Result.scenario must be of type ' \
                                                              'ScenarioRealisation'
        self.scenario = scenario

        if realisation_file_name is not None:
            assert self.scenario is not None, 'To store the simulated ScenarioRealisation the ' \
                                              'scenario must be passed as type of ' \
                                              'ScenarioRealisation.'
            self.scenario.to_json(r'../data/realisations/' + str(realisation_file_name) + '.JSON')

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

    def aggregate_load_profile(self, num_simulation_steps=None):

        if num_simulation_steps is None:
            assert self.scenario is not None, 'If using result.aggregate_load_profile without ' \
                                              'passing the number of simulation steps the ' \
                                              'field result.scenario must be set to the scenario ' \
                                              'realisation.'

            num_simulation_steps = num_time_steps(self.scenario.start_date, self.scenario.end_date,
                                                  self.scenario.resolution)
        load_profile = []

        for time_step in range(num_simulation_steps):
            power = 0
            for cp in self.power_connection_points:
                if time_step in self.power_connection_points[cp].keys():
                    power += self.power_connection_points[cp][time_step]

            load_profile.append(power)

        self.aggregated_load_profile = load_profile

        return load_profile

    def total_energy_charged(self):
        power = 0
        for cp in self.power_connection_points:
            for time_step in self.power_connection_points[cp]:
                power += self.power_connection_points[cp][time_step]
        return float(power)

    def max_load(self):
        """Calculates the max load of an aggregated load profile:

            max_load: (float): Max load that is generated by the charging infrastructure.
        """
        assert self.aggregated_load_profile is not None, 'Before calculating KPIs the aggreagated' \
                                                         'load profile must be calculated.'
        return max(self.aggregated_load_profile)

    def simultaneity_factor(self, infrastructure=None, bins=None):
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

        if bins is None:
            power_hardware_max = self.get_power_connection_points(infrastructure)
            power_max = self.max_load()
            return power_max / power_hardware_max
        else:
            power_hardware_max = self.get_power_connection_points(infrastructure)
            sim = [i / power_hardware_max for i in self.aggregated_load_profile]
            hist = histogram(sim, bins)
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
    def get_power_connection_points(infrastructure):
        """Sums over the power of all connection points in an Elvis conform infrastructure dict.

        Args:
            infrastructure: Elvis conform infrastructure dict.

        Returns:
            power_sum: (float): Sum over the power of all connection points.
        """
        msg_wrong_infrastructure = "Infrastructure must be Elvis conform."
        assert isinstance(infrastructure, dict), msg_wrong_infrastructure
        assert 'transformers' in infrastructure.keys(), msg_wrong_infrastructure
        power_sum = 0
        for transformer in infrastructure['transformers']:
            assert 'charging_points' in transformer.keys(), msg_wrong_infrastructure
            for charging_station in transformer['charging_points']:
                assert 'connection_points' in charging_station.keys(), msg_wrong_infrastructure
                for connection_point in charging_station['connection_points']:
                    assert 'max_power' in connection_point.keys()
                    assert isinstance(connection_point['max_power'], (float, int))
                    power_sum += connection_point['max_power']

        return power_sum
