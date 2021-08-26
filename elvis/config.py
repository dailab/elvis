"""This module contains all classes necessary to configure scenarios that can then be simulated
by Elvis."""

import logging
import warnings
import datetime
import pandas as pd
import yaml
import gzip
import json

import elvis.sched.schedulers as schedulers
from elvis.charging_event_generator import create_charging_events_from_weekly_distribution as \
    events_from_week_arr_dist
from elvis.charging_event_generator import create_charging_events_from_gmm as events_from_gmm
from elvis.utility.elvis_general import create_time_steps, num_time_steps, transform_data, \
    adjust_resolution, repeat_data
from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.charging_event import ChargingEvent
from elvis.set_up_infrastructure import wallbox_infrastructure


class ScenarioConfig:
    """Describes a scenario defined by its stochastic distributions and hardware parameters."""
    def __init__(self, **kwargs):
        # Time series data
        self.emissions_scenario = None
        self.emissions_scenario_res_data = None
        self.emissions_scenario_repeat = None
        self.emissions_scenario_col_pos = 0
        self.renewables_scenario = None

        self.transformer_preload = None
        self.transformer_preload_res_data = None
        self.transformer_preload_repeat = False
        self.transformer_preload_col_pos = 0

        # Event parameters
        self.sample_method = 'independent_normal_dist'  # or GMM
        self.arrival_distribution = None
        self.vehicle_types = []
        self.mean_park = None
        self.std_deviation_park = None
        self.mean_soc = None
        self.std_deviation_soc = None
        self.max_parking_time = 24
        self.num_charging_events = None
        self.charging_events = None
        self.gmm_means = None
        self.gmm_weights = None
        self.gmm_covariances = None

        # Infrastructure (behaviour)
        self.infrastructure = None
        self.queue_length = None
        self.disconnect_by_time = None
        self.opening_hours = None
        self.scheduling_policy = None
        self.df_charging_period = None

        if 'emissions_scenario' in kwargs:
            self.with_emissions_scenario(kwargs['emissions_scenario'])
        if 'renewables_scenario' in kwargs:
            self.renewables_scenario = kwargs['renewables_scenario']
        if 'transformer_preload' in kwargs:
            self.transformer_preload = kwargs['transformer_preload']

        if 'vehicle_types' in kwargs:
            self.vehicle_types = kwargs['vehicle_types']

        if 'opening_hours' in kwargs:
            self.with_opening_hours(kwargs['opening_hours'])

        if 'sample_method' in kwargs:
            self.sample_method = kwargs['sample_method']

        if 'charging_events' in kwargs:
            self.charging_events = kwargs['charging_events']
        if 'arrival_distribution' in kwargs:
            self.with_arrival_distribution(kwargs['arrival_distribution'])
        if 'infrastructure' in kwargs:
            self.with_infrastructure(kwargs['infrastructure'])
        if 'scheduling_policy' in kwargs:
            self.with_scheduling_policy(kwargs['scheduling_policy'])
        if isinstance(self.scheduling_policy, schedulers.DiscriminationFree):
            if 'df_charging_period' in kwargs:
                self.with_df_charging_period(kwargs['df_charging_period'])
            else:
                self.with_df_charging_period(datetime.timedelta(minutes=15))
        if 'mean_park' in kwargs:
            self.with_mean_park(kwargs['mean_park'])
        if 'std_deviation_park' in kwargs:
            self.with_std_deviation_park(kwargs['std_deviation_park'])
        if 'mean_soc' in kwargs:
            self.with_mean_soc(kwargs['mean_soc'])
        if 'std_deviation_soc' in kwargs:
            self.with_std_deviation_soc(kwargs['std_deviation_soc'])

        # Gaussian Mixture Model params
        if 'gmm_means' in kwargs:
            self.gmm_means = kwargs['gmm_means']
        if 'gmm_weights' in kwargs:
            self.gmm_weights = kwargs['gmm_weights']
        if 'gmm_covariances' in kwargs:
            self.gmm_covariances = kwargs['gmm_covariances']

        if 'max_parking_time' in kwargs:
            self.max_parking_time = kwargs['max_parking_time']
        if 'num_charging_events' in kwargs:
            self.with_num_charging_events(kwargs['num_charging_events'])
        if 'queue_length' in kwargs:
            self.with_queue_length(kwargs['queue_length'])
        if 'disconnect_by_time' in kwargs:
            self.with_disconnect_by_time(kwargs['disconnect_by_time'])
        if 'transformer_preload_res_data' in kwargs:
            self.transformer_preload_res_data = kwargs['transformer_preload_res_data']
        if 'transformer_preload_repeat' in kwargs:
            self.transformer_preload_repeat = kwargs['transformer_preload_repeat']
        if 'transformer_preload_col_pos' in kwargs:
            self.transformer_preload_col_pos = kwargs['transformer_preload_col_pos']
        if 'emissions_scenario_res_data' in kwargs:
            self.emissions_scenario_res_data = kwargs['emissions_scenario_res_data']
        if 'emissions_scenario_repeat' in kwargs:
            self.emissions_scenario_repeat = kwargs['emissions_scenario_repeat']
        if 'emissions_scenario_col_pos' in kwargs:
            self.emissions_scenario_col_pos = kwargs['emissions_scenario_col_pos']

    def __str__(self):
        printout = ''
        if self.vehicle_types is None:
            printout += str('Vehicle types: None\n')
        else:
            printout = 'Vehicle types: ' + str(vt + '\n' for vt in self.vehicle_types)

        printout += str('Mean parking time: ' + str(self.mean_park) + '\n')
        printout += str('Std deviation of parking time: ' + str(self.std_deviation_park) + '\n')
        printout += str('Mean value of the SOC distribution: ' + str(self.mean_soc) + '\n')
        printout += str('Std deviation of the SOC distribution: ' +
                        str(self.std_deviation_soc) + '\n')
        printout += str('Max parking time: ' +
                        str(self.max_parking_time) + '\n')
        printout += str('Number of charging events per week: ' +
                        str(self.num_charging_events) + '\n')

        if self.disconnect_by_time is True:
            printout += str('Vehicles are disconnected only depending on their parking time\n')
        else:
            printout += str('Vehicles are disconnected depending on their SOC and their parking'
                            'parking time (what ever comes first\n')
        if self.queue_length is None:
            printout += str('No queue is considered.\n')
        else:
            printout += str('Queue length: ' + str(self.queue_length) + '\n')

        printout += str('Opening hours: ' + str(self.opening_hours) + '\n')
        printout += str('Scheduling policy: ' + str(self.scheduling_policy) + '\n')

        return printout

    def to_dict(self):
        dictionary = self.__dict__.copy()
        if self.scheduling_policy is not None:
            dictionary['scheduling_policy'] = str(self.scheduling_policy)
        if self.charging_events is not None:
            dictionary['charging_events'] = [ce.to_dict() for ce in self.charging_events]

        # TODO what if transformer preload is not a list
        dictionary['transformer_preload'] = self.transformer_preload

        if len(self.vehicle_types) > 0:
            dictionary['vehicle_types'] = [vehicle.to_dict() for vehicle in self.vehicle_types]

        return dictionary

    @staticmethod
    def from_dict(dictionary):

        assert type(dictionary) is dict, 'Input of wrong type: ' + str(type(dictionary))

        config = ScenarioConfig()
        config.with_infrastructure(dictionary['infrastructure'])
        config.with_scheduling_policy(dictionary['scheduling_policy'])
        if 'mean_park' in dictionary:
            config.with_mean_park(dictionary['mean_park'])
        if 'std_deviation_park' in dictionary:
            config.with_std_deviation_park(dictionary['std_deviation_park'])
        if 'mean_soc' in dictionary:
            config.with_mean_soc(dictionary['mean_soc'])
        if 'std_deviation_soc' in dictionary:
            config.with_std_deviation_soc(dictionary['std_deviation_soc'])
        config.with_num_charging_events(dictionary['num_charging_events'])
        config.with_queue_length(dictionary['queue_length'])
        config.with_disconnect_by_time(dictionary['disconnect_by_time'])

        if 'df_charging_period' in dictionary:
            config.with_df_charging_period(dictionary['df_charging_period'])
        else:
            config.with_df_charging_period(datetime.timedelta(minutes=15))

        if 'sample_method' in dictionary:
            config.sample_method = dictionary['sample_method']
        if 'max_parking_time' in dictionary:
            config.max_parking_time = dictionary['max_parking_time']

        if 'opening_hours' in dictionary:
            config.with_opening_hours(dictionary['opening_hours'])

        if 'transformer_preload' in dictionary:
            config.transformer_preload = dictionary['transformer_preload']

        config.with_vehicle_types(vehicle_types=dictionary['vehicle_types'])
        if 'arrival_distribution' in dictionary:
            config.with_arrival_distribution(dictionary['arrival_distribution'])
        if 'charging_events' in dictionary:
            config.charging_events = dictionary['charging_events']

        if 'gmm_means' in dictionary:
            config.gmm_means = dictionary['gmm_means']
        if 'gmm_weights' in dictionary:
            config.gmm_weights = dictionary['gmm_weights']
        if 'gmm_covariances' in dictionary:
            config.gmm_covariances = dictionary['gmm_covariances']

        if 'transformer_preload_res_data' in dictionary:
            config.transformer_preload_res_data = dictionary['transformer_preload_res_data']
        if 'transformer_preload_repeat' in dictionary:
            config.transformer_preload_repeat = dictionary['transformer_preload_repeat']
        if 'transformer_preload_col_pos' in dictionary:
            config.transformer_preload_col_pos = dictionary['transformer_preload_col_pos']
        if 'emissions_scenario_res_data' in dictionary:
            config.emissions_scenario_res_data = dictionary['emissions_scenario_res_data']
        if 'emissions_scenario_repeat' in dictionary:
            config.emissions_scenario_repeat = dictionary['emissions_scenario_repeat']
        if 'emissions_scenario_col_pos' in dictionary:
            config.emissions_scenario_col_pos = dictionary['emissions_scenario_col_pos']

        return config

    def to_yaml(self, yaml_file):
        data = self.to_dict()
        with open(yaml_file, 'w') as file:
            yaml.dump(data, file, default_flow_style=None)
        return

    @staticmethod
    def from_yaml(yaml_str):
        """Create an instance of ScenarioConfig from a yaml str.

        Args:
            yaml_str: (dict): Import from yaml file.
            """
        assert type(yaml_str) == dict, 'The data specified in the yaml for creating an instance ' \
                                       'Scenario scenario must be a dict.'

        return ScenarioConfig.from_dict(yaml_str)

    def create_realisation(self, start_date, end_date, resolution):
        """Creates a realisation of self given the required time parameters.

        Args:
            start_date: (:obj: `datetime.datetime`): First time stamp.
            end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
            resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

        Returns:
            realisation: (:obj: `elvis.scenario.ScenarioRealisation`): Scenario realisation.
        """

        time_params = {'start_date': start_date, 'end_date': end_date, 'resolution': resolution}
        realisation = ScenarioRealisation(config=self, **time_params)
        return realisation

    def with_arrival_distribution(self, arrival_distribution):
        # TODO: Add pandas
        assert type(arrival_distribution) is list, 'Arrival distribution must be of type list or ' \
                                                   'pandas DataFrame.'

        msg_invalid_value_type = "Arrival distribution should be of type: pandas DataFrame or a " \
                                 "list containing float or int."
        # Check if all values in list are either float or int
        if arrival_distribution is list:
            assert all(isinstance(x, (float, int)) for x in arrival_distribution), \
                msg_invalid_value_type
        else:
            NotImplementedError()

        self.arrival_distribution = arrival_distribution

        return

    # Outdated
    def with_charging_events(self, charging_events):
        """Update the arrival distribution to use.
        """
        assert isinstance(charging_events, list), 'charging_events must be of type list'
        assert all(isinstance(x, ChargingEvent) for x in charging_events), \
            'All elements of charging_events must be of type ChargingEvent'
        self.charging_events = charging_events

        return self

    def with_emissions_scenario(self, emissions_scenario, col_pos=0, res_data=None, repeat=False):
        """Assigns values regarding the emissions scenario to config.

        Args:
            emissions_scenario: Either of type int/float, list, or pandas DataFrame/Series.
            col_pos: (int): If emissions scenario is of type pandas DataFrame: col_pos refers to
                the column the emissions scenario is stored.
            res_data: (datetime.timedelta): If emissions scenario is of type list and does not align
                with the simulation period: res_data states the time difference in between two
                adjacent values of emissions scenario.
            repeat: (bool): If emissions scenario is of type list and does not align with the
                simulation period: repeat=True indicates that the list shall be repeated until
                the whole simulation period is covered.
        """
        if isinstance(emissions_scenario, (pd.Series, pd.DataFrame)):
            self.emissions_scenario = emissions_scenario
        else:
            assert isinstance(emissions_scenario, (int, float, list)), \
                'Emissions scenario must be of type list or pandas DataFrame.'

            msg_invalid_value_type = "Emissions scenario should be of type: pandas DataFrame or" \
                                     " a list containing float or int."
            # Check if all values in list are either float or int
            if type(emissions_scenario) is list:
                assert all(isinstance(x, (float, int)) for x in emissions_scenario), \
                    msg_invalid_value_type

            self.emissions_scenario = emissions_scenario

        if res_data is not None:
            assert isinstance(res_data, (str, datetime.timedelta))
            if type(res_data) is str:
                try:
                    date = datetime.datetime.strptime(res_data, '%H:%M:%S')
                    self.emissions_scenario_res_data = datetime.timedelta(hours=date.hour,
                                                                          minutes=date.minute,
                                                                          seconds=date.second)
                except ValueError:
                    try:
                        seconds = pd.Timedelta(res_data).total_seconds()
                        self.emissions_scenario_res_data = datetime.timedelta(seconds=seconds)
                    except ValueError:
                        print('Incorrect timedelta format for resolution pls use: %H:%M:%S or '
                              'a pandas conform timedelta format.')
            # datetime.timedelta
            else:
                self.emissions_scenario_res_data = res_data

        if repeat is not False:
            assert type(repeat) is bool, 'Repeat can only be True or False.'
            self.emissions_scenario = True

        if col_pos != 0:
            assert isinstance(col_pos, int), 'Column position (col_pos) must be a positive integer'
            assert col_pos >= 0, 'Column position (col_pos) must be a positive integer'
            self.emissions_scenario_col_pos = col_pos
        return self

    def with_renewables_scenario(self, renewables_scenario):
        """Update the renewable energy scenario to use."""

        self.renewables_scenario = renewables_scenario
        return self

    def with_transformer_preload(self, transformer_preload, col_pos=0, res_data=None, repeat=False):
        """Assigns values regarding the transformer preload to config.

        Args:
            transformer_preload: Either of type int/float, list, or pandas DataFrame/Series.
            col_pos: (int): If transformer_preload is of type pandas DataFrame: col_pos refers to
                the column the transformer preload is stored.
            res_data: (datetime.timedelta): If transfomer preload is of type list and does not align
                with the simulation period: res_data states the time difference in between two
                adjacent values of transformer preload.
            repeat: (bool): If transformer preload is of type list and does not align with the
                simulation period: repeat=True indicates that the list shall be repeated until
                the whole simulation period is covered.
        """
        if isinstance(transformer_preload, (pd.Series, pd.DataFrame)):
            self.transformer_preload = transformer_preload
        else:
            assert isinstance(transformer_preload, (int, float, list)), \
                'Transformer preload must be of type list or pandas DataFrame.'

            msg_invalid_value_type = "Transformer preload should be of type: pandas DataFrame or" \
                                     " a list containing float or int."
            # Check if all values in list are either float or int
            if type(transformer_preload) is list:
                assert all(isinstance(x, (float, int)) for x in transformer_preload), \
                    msg_invalid_value_type

            self.transformer_preload = transformer_preload

        if res_data is not None:
            assert isinstance(res_data, (str, datetime.timedelta))
            if type(res_data) is str:
                try:
                    date = datetime.datetime.strptime(res_data, '%H:%M:%S')
                    self.transformer_preload_res_data = datetime.timedelta(hours=date.hour,
                                                                           minutes=date.minute,
                                                                           seconds=date.second)
                except ValueError:
                    try:
                        seconds = pd.Timedelta(res_data).total_seconds()
                        self.transformer_preload_res_data = datetime.timedelta(seconds=seconds)
                    except ValueError:
                        print('Incorrect timedelta format for resolution pls use: %H:%M:%S or '
                              'a pandas conform timedelta format.')
            # datetime.timedelta
            else:
                self.transformer_preload_res_data = res_data

        if repeat is not False:
            assert type(repeat) is bool, 'Repeat can only be True or False.'
            self.transformer_preload_repeat = True

        if col_pos != 0:
            assert isinstance(col_pos, int), 'Column position (col_pos) must be a positive integer'
            assert col_pos > 0, 'Column position (col_pos) must be a positive integer'
            self.transformer_preload_col_pos = col_pos
        return self

    def with_scheduling_policy(self, scheduling_policy_input):
        """Update the scheduling policy to use.
        Default: :obj: `elvis.sched.schedulers.Uncontrolled`.
        Use default if input not a str or str can not be matched.

        Args:
            scheduling_policy_input: Either str containing name of the scheduling policy to be used.
                Or instance of :obj: `elvis.sched.schedulers.SchedulingPolicy`.
        """
        # set default
        scheduling_policy = schedulers.Uncontrolled()

        # if input is already instance of Scheduling Policy assign
        if isinstance(scheduling_policy_input, schedulers.SchedulingPolicy):
            self.scheduling_policy = scheduling_policy_input
            return self

        # ensure input is str. If not return default
        if type(scheduling_policy_input) is not str:
            logging.error('Scheduling policy should be of type str or an instance of '
                          'SchedulingPolicy. The uncontrolled strategy has been used as a default.')
            self.scheduling_policy = scheduling_policy
            return self

        # Match string
        if scheduling_policy_input in ('Uncontrolled', 'UC', 'Uc', 'uc'):
            self.scheduling_policy = schedulers.Uncontrolled()

        elif scheduling_policy_input in ('Discrimination Free', 'DF', 'df'):
            self.scheduling_policy = schedulers.DiscriminationFree()

        elif scheduling_policy_input == 'FCFS':
            self.scheduling_policy = schedulers.FCFS()

        elif scheduling_policy_input in ('With Storage', 'ws', 'WS'):
            self.scheduling_policy = schedulers.WithStorage()

        elif scheduling_policy_input in ('Optimized', 'opt', 'OPT'):
            self.scheduling_policy = schedulers.Optimized()

        # invalid str use default: Uncontrolled
        else:
            logging.error('"%s" can not be matched to any existing scheduling policy.'
                          'Please use: "Uncontrolled", "Discrimination Free", "FCFS", '
                          '"With Storage" or "Optimized". '
                          'Uncontrolled is the default value and has been used for the simulation.',
                          str(scheduling_policy_input))

            self.scheduling_policy = schedulers.Uncontrolled()
        return self

    def with_infrastructure(self, infrastructure=None, **kwargs):
        """Update the infrastructure to use.
        Args:
            kwargs.num_cp: (int): Number of charging points.
            kwargs.num_cp_per_cs: (int) Number of charging points per charging station.
            kwargs.power_cp: (int or float): (optional) Max power per charging point.
            kwargs.power_cs: (int or float): (optional) Max power of the charging station.
            kwargs.power_transformer: (int or float): (optional) Max power of the transformer.
            kwargs.min_power_cp: (int or float): (optional) Minimum power (if not 0) for the
                charging point.
            kwargs.min_power_cs: (int or float): (optional) Minimum power (if not 0) for the
                charging station.
            kwargs.min_power_transformer: (int or float) : (optional) Minimum power (if not 0) for
                the charging station.
        """
        if infrastructure is not None:
            assert type(infrastructure) is dict
            self.infrastructure = infrastructure
        else:
            err_msg = '%s is a necessary key to initialise an elvis infrastructure as a wallbox ' \
                      'infrastructure.'
            keys = kwargs.keys()
            assert 'num_cp' in keys, (err_msg, 'num_cp')
            assert 'power_cp' in keys, (err_msg, 'power_cp')

            num_cp = kwargs['num_cp']
            power_cp = kwargs['power_cp']

            if 'num_cp_per_cs' in keys:
                num_cp_per_cs = kwargs['num_cp_per_cs']
            else:
                num_cp_per_cs = 1
            if 'power_cs' in keys:
                power_cs = kwargs['power_cs']
            else:
                power_cs = None
            if 'power_transformer' in keys:
                power_transformer = kwargs['power_transformer']
            else:
                power_transformer = None
            if 'min_power_cp' in keys:
                min_power_cp = kwargs['min_power_cp']
            else:
                min_power_cp = 0
            if 'min_power_cs' in keys:
                min_power_cs = kwargs['min_power_cs']
            else:
                min_power_cs = 0
            if 'min_power_transformer' in keys:
                min_power_transformer = kwargs['min_power_transformer']
            else:
                min_power_transformer = 0

            self.infrastructure = wallbox_infrastructure(
                num_cp, power_cp, num_cp_per_cs, power_cs, power_transformer, min_power_cp,
                min_power_cs, min_power_transformer)

        return self

    def with_vehicle_types(self, vehicle_types=None, **kwargs):
        """Update the vehicle types to use."""

        if vehicle_types is not None:
            for vehicle_type in vehicle_types:
                if isinstance(vehicle_type, ElectricVehicle):
                    self.add_vehicle_types(vehicle_type=vehicle_type)
                elif isinstance(vehicle_type, dict):
                    self.add_vehicle_types(**vehicle_type)
                else:
                    # TODO: List relevant information.
                    raise TypeError('Using with_vehicle_types with a list: All list entries '
                                    'must either be of type ElectricVehicle or dict, containing'
                                    'all relevant information.')

            return self
        else:
            self.add_vehicle_types(**kwargs)
            return self

    def with_df_charging_period(self, charging_period):

        assert isinstance(charging_period, (str, datetime.timedelta)), (
            'Charging period must either be a str in format: %H:%M:%S or an instance '
            'of datetime.timedelta')

        # str
        if type(charging_period) is str:
            try:
                date = datetime.datetime.strptime(charging_period, '%H:%M:%S')
                self.df_charging_period = datetime.timedelta(hours=date.hour,
                                                             minutes=date.minute,
                                                             seconds=date.second)
            except ValueError:
                try:
                    seconds = pd.Timedelta(charging_period).total_seconds()
                    self.df_charging_period = datetime.timedelta(seconds=seconds)
                except ValueError:
                    print('Incorrect timedelta format for resolution pls use: %H:%M:%S or '
                          'a pandas conform timedelta format.')
        # datetime.timedelta
        else:
            self.df_charging_period = charging_period

        return self

    def add_vehicle_types(self, vehicle_type=None, **kwargs):
        """Add a supported vehicle type to this configuration or a list of vehicle types.
            If no instance of vehicle type is passed an instance of vehicle_type is created if
            kwargs contains the necessary keys (see below).
            If vehicle_type is passed:
                - vehicle_type: (:obj: `vehicle.ElectricVehicle`

            If battery instance is passed kwargs has to to contain:
                - brand: (str): Brand of the vehicle.
                - model: (str): Model of the vehicle.
                - battery: (:obj: `battery.EVBattery`): Battery instance
            If no battery is passed and shall be initialized:
                - brand: (str): Brand of the vehicle.
                - model: (str): Model of the vehicle.
                - capacity: (float): Capacity of the battery in kWh.
                - max_charge_power: (float): Max power in kW.
                - min_charge_power: (float): Min power in kW.
                - efficiency: (float): [0, 1]

            Raises:
                AssertionError:
                    - If vehicle_type is of type list and at least one of the entries is not of
                        type :obj: `ElectricVehicle`.
                    - If vehicle type is not a list and not of type :obj: `ElectricVehicle`.
                    - If kwargs are passed and the keys do not contain the variable names listed
                        above.
        """
        # if list with multiple vehicle_type instances is passed add multiple
        if type(vehicle_type) is list:
            for vehicle in vehicle_type:
                assert isinstance(vehicle, ElectricVehicle)
                self.vehicle_types.append(vehicle)
                return
        # if an instance of vehicle type is passed assign
        elif vehicle_type is not None:
            assert isinstance(vehicle_type, ElectricVehicle)
            self.vehicle_types.append(vehicle_type)
            return

        assert 'brand' in kwargs
        assert 'model' in kwargs
        assert 'probability' in kwargs
        assert 'battery' in kwargs

        brand = str(kwargs['brand'])
        model = str(kwargs['model'])
        probability = kwargs['probability']

        # if all fields of ElectricVehicle are passed and an instance of EVBattery is already made
        if isinstance(kwargs['battery'], EVBattery):
            battery = kwargs['battery']
            self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
            return

        # if there is no instance of EVBattery check if all parameters are passed.
        assert 'capacity' in kwargs['battery']
        assert 'max_charge_power' in kwargs['battery']
        assert 'min_charge_power' in kwargs['battery']
        assert 'efficiency' in kwargs['battery']

        capacity = kwargs['battery']['capacity']
        max_charge_power = kwargs['battery']['max_charge_power']
        min_charge_power = kwargs['battery']['min_charge_power']
        efficiency = kwargs['battery']['efficiency']

        # Power degradations when battery reaches certain SOC level shall be considered
        if 'start_power_degradation' and 'max_degradation_level' in kwargs['battery']:
            start_power_degradation = kwargs['battery']['start_power_degradation']
            max_degradation_level = kwargs['battery']['max_degradation_level']

            battery = EVBattery(capacity=capacity,
                                max_charge_power=max_charge_power,
                                min_charge_power=min_charge_power,
                                efficiency=efficiency,
                                start_power_degradation=start_power_degradation,
                                max_degradation_level=max_degradation_level)
        # No SOC-dependent power degradations considered
        else:
            battery = EVBattery(capacity=capacity, max_charge_power=max_charge_power,
                                min_charge_power=min_charge_power, efficiency=efficiency, )

        # get instance of ElectricVehicle with initialized battery
        self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
        return self

    def with_opening_hours(self, opening_hours):
        """Update the opening hours to use."""

        if opening_hours is None:
            self.opening_hours = opening_hours
            return self

        assert isinstance(opening_hours, tuple), 'Opening hours is expected to be a tuple.'
        assert len(opening_hours) == 2, 'Opening hours is expected to be a tuple with 2 values'
        _open = opening_hours[0]
        _close = opening_hours[1]
        assert isinstance(_open, (float, int)), 'Values in opening hours must be of type int or ' \
                                                'float representing the hours of the day.'
        assert isinstance(_open, (float, int)), 'Values in opening hours must be of type int or ' \
                                                'float representing the hours of the day.'

        assert _open <= _close, 'The first value (opening hour) is expected to be smaller than ' \
                                'the 2nd value (closing hour).'
        assert _close <= 24, 'The last value(closing hour) is expected to be smaller or equal to 24'
        assert _open >= 0, 'The first value(opening hour) is expected to be bigger or equal to 0'

        self.opening_hours = opening_hours
        return self

    def with_num_charging_events(self, num_charging_events):
        """Update the number of charging events to use."""
        # TODO: Can be float?
        assert type(num_charging_events) is int
        self.num_charging_events = num_charging_events
        return self

    def with_queue_length(self, queue_length):
        """Update maximal length of queue."""
        assert type(queue_length) is int
        self.queue_length = queue_length
        return self

    def with_disconnect_by_time(self, disconnect_by_time):
        """Update decision variable on how to disconnect cars."""
        assert type(disconnect_by_time) is bool
        self.disconnect_by_time = disconnect_by_time
        return self

    def with_mean_park(self, mean_park):
        """Update decision variable on how to disconnect cars."""
        assert isinstance(mean_park, (int, float))
        assert 0 < mean_park < 24, "The mean parking time should be in between 0 and 24 hours."
        self.mean_park = mean_park
        return self

    def with_std_deviation_park(self, std_deviation_park):
        """Update decision variable on how to disconnect cars."""
        assert isinstance(std_deviation_park, (int, float)), 'The mean of the std deviation of ' \
                                                             'the parking time must be of type ' \
                                                             'float.'

        assert 0 <= std_deviation_park
        self.std_deviation_park = std_deviation_park
        return self

    def with_max_parking_time(self, max_parking_time):
        """Update decision variable on how to disconnect cars."""
        assert isinstance(max_parking_time, (int, float)), 'The mean of the std deviation of ' \
                                                           'the parking time must be of type ' \
                                                           'float.'

        assert 0 <= max_parking_time
        self.max_parking_time = max_parking_time
        return self

    def with_mean_soc(self, mean_soc):
        """Update decision variable on how to disconnect cars."""
        assert isinstance(mean_soc, (int, float)), 'The mean of the SOC must be of type float.'
        assert 0 < mean_soc < 1, "The mean parking time should be in between 0 and 24 hours."
        self.mean_soc = mean_soc
        return self

    def with_std_deviation_soc(self, std_deviation_soc):
        """Update decision variable on how to disconnect cars."""
        assert isinstance(std_deviation_soc, (int, float)), 'The std deviation of the SOC must' \
                                                            'be of type int or float.'
        assert 0 <= std_deviation_soc, 'The std deviation of the SOC must be bigger than 0.'
        self.std_deviation_soc = std_deviation_soc
        return self


class ScenarioRealisation:
    """Describes a realisation based on the stochasticity of a ScenarioConfig."""

    @staticmethod
    def check_input(**kwargs):
        """Check if all necessary keys are in kwargs of __init__."""
        keys_necessary = ['emissions_scenario', 'renewables_scenario', 'opening_hours',
                          'infrastructure', 'scheduling_policy', 'queue_length',
                          'disconnect_by_time', 'start_date', 'end_date', 'resolution']

        for key in keys_necessary:
            assert key in kwargs, str(key) + ' is missing as an input to create a ' \
                                             'ScenarioRealisation.'
        return

    def __init__(self, config=None, **kwargs):
        """Can be either called with an instance of ScenarioConfig or a dict containing all
        necessary parameters."""

        self.charging_events = None
        self.emissions_scenario = None
        self.transformer_preload = None
        self.scheduling_policy = None

        # Time parameters
        try:
            # Start date
            assert isinstance(kwargs['start_date'], (str, datetime.datetime)), (
                'start_date must either be an isoformat compatible datetime str or an instance '
                'of datetime.datetime')
            # str
            if type(kwargs['start_date']) is str:
                try:
                    self.start_date = datetime.datetime.fromisoformat(kwargs['start_date'])
                except ValueError:
                    print('Incorrect date format for start_date pls use: %y-%m-%d %H:%M:%S')
            # datetime.datetime
            else:
                self.start_date = kwargs['start_date']

            # End Date
            assert isinstance(kwargs['end_date'], (str, datetime.datetime)), (
                'end_date must either be an isoformat compatible datetime str or an instance '
                'of datetime.datetime')

            # str
            if type(kwargs['end_date']) is str:
                try:
                    self.end_date = datetime.datetime.fromisoformat(kwargs['end_date'])
                except ValueError:
                    print('Incorrect date format for end_date pls use: %y-%m-%d %H:%M:%S')
            # datetime.datetime
            else:
                self.end_date = kwargs['end_date']

            # Resolution

            assert isinstance(kwargs['resolution'], (str, datetime.timedelta)), (
                'Resolution must either be a str in format: %H:%M:%S or an instance '
                'of datetime.timedelta')

            # str
            if type(kwargs['resolution']) is str:
                try:
                    date = datetime.datetime.strptime(kwargs['resolution'], '%H:%M:%S')
                    self.resolution = datetime.timedelta(hours=date.hour, minutes=date.minute,
                                                         seconds=date.second)
                except ValueError:
                    try:
                        seconds = pd.Timedelta(kwargs['resolution']).total_seconds()
                        self.resolution = datetime.timedelta(seconds=seconds)
                    except ValueError:
                        print('Incorrect timedelta format for resolution pls use: %H:%M:%S or '
                              'a pandas conform timedelta format.')
            # datetime.timedelta
            else:
                self.resolution = kwargs['resolution']

        # start_date, end_date or resolution not in kwargs
        except KeyError:
            print('Creating a ScenarioRealisation with a ScenarioConfig requires the'
                  'start_date, end_date and the resolution of the simulation to be passed '
                  'as key word arguments.')

        # With ScenarioConfig instance
        if isinstance(config, ScenarioConfig):
            self.with_emissions_scenario(config.emissions_scenario,
                                         self.start_date, self.end_date, self.resolution)
            self.renewables_scenario = config.emissions_scenario
            self.with_opening_hours(config.opening_hours)
            self.infrastructure = config.infrastructure
            self.with_scheduling_policy(config.scheduling_policy)
            self.sample_method = config.sample_method

            if config.df_charging_period is not None:
                self.df_charging_period = config.df_charging_period
            else:
                self.df_charging_period = datetime.timedelta(minutes=15)
            self.queue_length = config.queue_length
            self.disconnect_by_time = config.disconnect_by_time
            self.with_transformer_preload(config.transformer_preload,
                                          self.start_date, self.end_date, self.resolution,
                                          config.transformer_preload_col_pos,
                                          config.transformer_preload_res_data,
                                          config.transformer_preload_repeat)

            if config.charging_events is not None:
                self.charging_events = config.charging_events
            else:
                if self.sample_method is None or self.sample_method == 'independent_normal_dist':
                    self.transform_arrival_distribution()
                    time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                    self.charging_events = events_from_week_arr_dist(
                        config.arrival_distribution, time_steps, config.num_charging_events,
                        config.mean_park, config.std_deviation_park, config.mean_soc,
                        config.std_deviation_soc, config.vehicle_types, config.max_parking_time)
                elif self.sample_method in ['GMM', 'gmm']:
                    time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                    self.charging_events = events_from_gmm(
                        time_steps, config.num_charging_events, config.gmm_means,
                        config.gmm_weights, config.gmm_covariances, config.vehicle_types,
                        config.max_parking_time, config.mean_soc, config.std_deviation_soc)
                else:
                    ValueError('Events can only be sampled from independent weekly arrival '
                               'distributions ar a weekly GMM (gaussian mixture model)')

        else:
            self.check_input(**kwargs)
            self.with_emissions_scenario(kwargs['emissions_scenario'],
                                         self.start_date, self.end_date, self.resolution)
            self.renewables_scenario = kwargs['renewables_scenario']
            self.with_opening_hours(kwargs['opening_hours'])
            self.infrastructure = kwargs['infrastructure']
            self.with_scheduling_policy(kwargs['scheduling_policy'])

            if 'df_charging_period' in kwargs.keys():
                self.with_df_charging_period(kwargs['df_chaging_period'])
            else:
                self.df_charging_period = datetime.timedelta(minutes=15)
            self.queue_length = kwargs['queue_length']
            self.disconnect_by_time = kwargs['disconnect_by_time']
            self.start_date = kwargs['start_date']
            self.end_date = kwargs['end_date']
            self.resolution = kwargs['resolution']

            if 'charging_events' in kwargs:
                self.charging_events = [ChargingEvent.from_dict(**ce)
                                        for ce in kwargs['charging_events']]
            else:
                if self.sample_method is None or self.sample_method == 'independent_normal_dist':
                    time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                    self.charging_events = events_from_week_arr_dist(
                        kwargs['arrival_distribution'], time_steps, kwargs['num_charging_events'],
                        kwargs['mean_park'], kwargs['std_deviation_park'], kwargs['mean_soc'],
                        kwargs['std_deviation_soc'], kwargs['vehicle_types'],
                        kwargs['max_parking_time'])
                elif self.sample_method in ['GMM', 'gmm']:
                    time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                    self.charging_events = events_from_gmm(
                        time_steps, kwargs['num_charging_events'], kwargs['gmm_means'],
                        kwargs['gmm_weights'], kwargs['gmm_covariances'], kwargs['vehicle_types'],
                        kwargs['max_parking_time'], kwargs['mean_soc'], kwargs['std_deviation_soc'])
                else:
                    ValueError('Events can only be sampled from independent weekly arrival '
                               'distributions ar a weekly GMM (gaussian mixture model)')
            if 'transformer_preload' in kwargs:
                res_data = None
                repeat = None
                col_pos = 0
                if 'transformer_preload_res_data' in kwargs:
                    res_data = kwargs['transformer_preload_res_data']
                if 'transformer_preload_repeat' in kwargs:
                    repeat = kwargs['transformer_preload_repeat']
                if 'transformer_preload_col_pos' in kwargs:
                    col_pos = kwargs['transformer_preload_col_pos']

                self.with_transformer_preload(kwargs['transformer_preload'],
                                              self.start_date, self.end_date, self.resolution,
                                              col_pos, res_data, repeat)

        return

    def to_dict(self):
        dictionary = self.__dict__.copy()

        dictionary['scheduling_policy'] = str(self.scheduling_policy)
        # TODO: what if time series data is not a list
        dictionary['emissions_scenario'] = self.emissions_scenario
        dictionary['renewables_scenario'] = self.renewables_scenario
        dictionary['renewables_scenario'] = self.renewables_scenario

        dictionary['opening_hours'] = self.opening_hours
        dictionary['charging_events'] = [ce.to_dict(deep=True) for ce in self.charging_events]

        dictionary['start_date'] = str(self.start_date.isoformat())
        dictionary['end_date'] = str(self.end_date.isoformat())
        dictionary['resolution'] = str(self.resolution)

        if 'df_charging_period' in dictionary.keys():
            dictionary['df_charging_period'] = str(self.df_charging_period)

        return dictionary

    @staticmethod
    def from_dict(dictionary):
        realisation = ScenarioRealisation(**dictionary)
        return realisation

    # https://stackoverflow.com/questions/39450065/python-3-read-write-compressed-json-objects-from-to-gzip-file
    def save_to_disk(self, file_path):
        data = self.to_dict()

        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')

        with gzip.GzipFile(file_path, 'w') as fout:
            fout.write(json_bytes)

        return

    @staticmethod
    def from_disk(json_file_name):
        with gzip.GzipFile(json_file_name, 'r') as fin:
            json_bytes = fin.read()

        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)

        return ScenarioRealisation.from_dict(data)

    def transform_arrival_distribution(self):
        pass

    def with_transformer_preload(self, transformer_preload, start_date, end_date, resolution,
                                 col_pos=0, res_data=None, repeat=False):
        """Update the renewable energy scenario to use.
        Simulation time parameter must be set before transformer preload can be initialised.

        Args:
            transformer_preload: Either of type int/float, list, or pandas Series/DataFrame.
            start_date: (:obj: `datetime.datetime`): First time stamp.
            end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
            resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.
            col_pos: (int): If pandas DataFrame is passed indicates the column in which the
                emission values are stored.
            res_data: (datetime.timedelta): If list is passed that does not align with the
                simulation period, res_data displays the period inbetween two adjacent list entries.
            repeat: (bool): If list is passed that does not align with the
                simulation period and repeat is True the list is repeated until enough data points
                are available for the simulation period.

        """

        # Error messages
        msg_wrong_resolution_type = "If the transformer preload is passed as list and the" \
                                    "resolution is supposed to be of adjusted please" \
                                    "use type datetime.timedelta."
        msg_wrong_transformer_preload_type = "Transformer preload should be of type: " \
                                             "pandas DataFrame, list containing float or int," \
                                             " int, float."
        msg_alignement_unsuccessful = "Transformer preload could not be aligned to simulation" \
                                      "steps."
        msg_invalid_value_type = "Transformer preload should be of type: pandas DataFrame, " \
                                 "list containing float or int, int, float."
        msg_not_enough_data_points = "There are less values for the transformer preload than " \
                                     "simulation steps. Please adjust the data."

        # Check whether passed value is a DataFrame or a list
        if isinstance(transformer_preload, pd.DataFrame):  # DataFrame
            # Make sure length is aligned to simulation period and resolution
            # num_values = len(transformer_preload)
            transformer_preload = transformer_preload.iloc[:, col_pos]
            transformer_preload = transform_data(transformer_preload,
                                                 resolution, start_date, end_date)
        elif isinstance(transformer_preload, pd.Series):
            transformer_preload = transform_data(transformer_preload,
                                                 resolution, start_date, end_date)
        else:  # list or numeric
            num_simulation_steps = int((self.end_date - self.start_date) / self.resolution) + 1

            if isinstance(transformer_preload, (int, float)):
                transformer_preload = [transformer_preload] * num_simulation_steps

            assert type(transformer_preload) is list, msg_wrong_transformer_preload_type

            # Check if all values in list are either float or int
            assert all(isinstance(x, (float, int)) for x in transformer_preload), \
                msg_invalid_value_type

            # Check whether the length of the list alignes with the simulation period and resolution
            # If num_values don't fit simulation period and no action is wanted return error
            num_values = len(transformer_preload)

            assert num_simulation_steps <= num_values or res_data is not None or repeat, \
                msg_not_enough_data_points

            if res_data is not None:
                if type(res_data) is str:
                    try:
                        date = datetime.datetime.strptime(res_data, '%H:%M:%S')
                        res_data = datetime.timedelta(hours=date.hour, minutes=date.minute,
                                                      seconds=date.second)
                    except ValueError:
                        logging.error('%s is of incorrect format. Please use %s',
                                      res_data, '%H:%M:%S')
                        raise ValueError
                assert isinstance(res_data, datetime.timedelta), msg_wrong_resolution_type

                transformer_preload = adjust_resolution(transformer_preload, res_data,
                                                        self.resolution)

            if repeat is True:
                transformer_preload = repeat_data(transformer_preload, num_simulation_steps)

            # Should it be ==?
            assert len(transformer_preload) >= num_simulation_steps, msg_alignement_unsuccessful

        self.transformer_preload = transformer_preload

        return self

    def with_scheduling_policy(self, scheduling_policy_input):
        """Update the scheduling policy to use.
        Default: :obj: `elvis.sched.schedulers.Uncontrolled`.
        Use default if input not a str or str can not be matched.

        Args:
            scheduling_policy_input: Either str containing name of the scheduling policy to be used.
                Or instance of :obj: `elvis.sched.schedulers.SchedulingPolicy`.
        """
        # set default
        scheduling_policy = schedulers.Uncontrolled()

        # if input is already instance of Scheduling Policy assign
        if isinstance(scheduling_policy_input, schedulers.SchedulingPolicy):
            self.scheduling_policy = scheduling_policy_input
            return self

        # ensure input is str. If not return default
        if type(scheduling_policy_input) is not str:
            logging.error('Scheduling policy should be of type str or an instance of '
                          'SchedulingPolicy. The uncontrolled strategy has been used as a default.')
            self.scheduling_policy = scheduling_policy
            return self

        # Match string
        if scheduling_policy_input in ('Uncontrolled', 'UC', 'Uc', 'uc'):
            self.scheduling_policy = schedulers.Uncontrolled()

        elif scheduling_policy_input in ('Discrimination Free', 'DF', 'df'):
            self.scheduling_policy = schedulers.DiscriminationFree()

        elif scheduling_policy_input == 'FCFS':
            self.scheduling_policy = schedulers.FCFS()

        elif scheduling_policy_input in ('With Storage', 'ws', 'WS'):
            self.scheduling_policy = schedulers.WithStorage()

        elif scheduling_policy_input in ('Optimized', 'opt', 'OPT'):
            self.scheduling_policy = schedulers.Optimized()

        # invalid str use default: Uncontrolled
        else:
            logging.error('"%s" can not be matched to any existing scheduling policy.'
                          'Please use: "Uncontrolled", "Discrimination Free", "FCFS", '
                          '"With Storage" or "Optimized". '
                          'Uncontrolled is the default value and has been used for the simulation.',
                          str(scheduling_policy_input))

            self.scheduling_policy = schedulers.Uncontrolled()
        return self

    def with_df_charging_period(self, charging_period):

        assert isinstance(charging_period, (str, datetime.timedelta)), (
            'Charging period must either be a str in format: %H:%M:%S or an instance '
            'of datetime.timedelta')

        # str
        if type(charging_period) is str:
            try:
                date = datetime.datetime.strptime(charging_period, '%H:%M:%S')
                self.df_charging_period = datetime.timedelta(hours=date.hour,
                                                             minutes=date.minute,
                                                             seconds=date.second)
            except ValueError:
                try:
                    seconds = pd.Timedelta(charging_period).total_seconds()
                    self.df_charging_period = datetime.timedelta(seconds=seconds)
                except ValueError:
                    print('Incorrect timedelta format for resolution pls use: %H:%M:%S or '
                          'a pandas conform timedelta format.')
        # datetime.timedelta
        else:
            self.df_charging_period = charging_period

        return self

    def with_emissions_scenario(self, emissions_scenario, start_date, end_date, resolution,
                                col_pos=0, res_data=None, repeat=None):
        """Update emissions scenario variable representing the CO2-emissions per kWh at a given
        time.

        Args:
            emissions_scenario: Can be either of type int, float, list or pandas Series or
            DataFrame.
            start_date: (:obj: `datetime.datetime`): First time stamp.
            end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
            resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.
            col_pos: (int): If pandas DataFrame is passed indicates the column in which the
                emission values are stored.
            res_data: (datetime.timedelta): If list is passed that does not align with the
                simulation period, res_data displays the period inbetween two adjacent list entries.
            repeat: (bool): If list is passed that does not align with the
                simulation period and repeat is True the list is repeated until enough data points
                are available for the simulation period.
            """
        if emissions_scenario is None:
            return self

        assert isinstance(start_date, datetime.datetime), 'Start date must be datetime.datetime.'
        assert isinstance(end_date, datetime.datetime), 'End date must be datetime.datetime.'
        assert isinstance(resolution, datetime.timedelta), 'Resolution must be datetime.timedelta'
        assert isinstance(col_pos, int), 'Column must be a positive integer.'
        assert col_pos >= 0, 'Column must be a positive integer.'

        # Error messages
        msg_wrong_resolution_type = "If the transformer preload is passed as list and the" \
                                    "resolution is supposed to be of adjusted please" \
                                    "use type datetime.timedelta."
        msg_alignment_unsuccessful = "Transformer preload could not be aligned to simulation" \
                                     "steps."
        msg_invalid_value_type = "Transformer preload should be of type: pandas DataFrame, " \
                                 "list containing float or int, int, float."
        msg_not_enough_data_points = "There are less values for the transformer preload than " \
                                     "simulation steps. Please adjust the data."

        emissions_scenario_aligned = []

        # Constant value
        if isinstance(emissions_scenario, (float, int)):
            self.emissions_scenario = [emissions_scenario] * \
                                         num_time_steps(start_date, end_date, resolution)

        # pandas DataFrame
        elif isinstance(emissions_scenario, pd.DataFrame):
            emissions_scenario = emissions_scenario.iloc[:, col_pos]

            emissions_scenario_aligned = transform_data(emissions_scenario,
                                                        resolution, start_date, end_date)
        elif isinstance(emissions_scenario, pd.Series):
            emissions_scenario_aligned = transform_data(emissions_scenario,
                                                        resolution, start_date, end_date)
        elif isinstance(emissions_scenario, list):
            num_simulation_steps = num_time_steps(start_date, end_date, resolution)

            # Check if all values in list are either float or int
            assert all(isinstance(x, (float, int)) for x in emissions_scenario), \
                msg_invalid_value_type

            # Check whether the length of the list alignes with the simulation period and resolution
            # If num_values don't fit simulation period and no action is wanted return error
            num_values = len(emissions_scenario)

            assert num_simulation_steps < num_values or res_data is not None or repeat, \
                msg_not_enough_data_points

            if res_data is not None:
                if type(res_data) is str:
                    try:
                        date = datetime.datetime.strptime(res_data, '%H:%M:%S')
                        res_data = datetime.timedelta(hours=date.hour, minutes=date.minute,
                                                      seconds=date.second)
                    except ValueError:
                        logging.error('%s is of incorrect format. Please use %s',
                                      res_data, '%H:%M:%S')
                        raise ValueError
                assert isinstance(res_data, datetime.timedelta), msg_wrong_resolution_type

                emissions_scenario = adjust_resolution(emissions_scenario, res_data,
                                                       self.resolution)

            if repeat is True:
                emissions_scenario = repeat_data(emissions_scenario, num_simulation_steps)

            # Should it be ==?
            assert len(emissions_scenario) >= num_simulation_steps, msg_alignment_unsuccessful
        else:
            warnings.warn('Emissions are passed in an non convertible type. Please either use:'
                          'Float/int, list or pandas Series or DataFrame. The simulation is carried'
                          ' on without assigning emission values.')

        return emissions_scenario_aligned

    def with_opening_hours(self, opening_hours):
        """Update the opening hours to use."""

        if opening_hours is None:
            self.opening_hours = opening_hours
            return self

        assert isinstance(opening_hours, tuple), 'Opening hours is expected to be a tuple.'
        assert len(opening_hours) == 2, 'Opening hours is expected to be a tuple with 2 values'
        _open = opening_hours[0]
        _close = opening_hours[1]
        assert isinstance(_open,
                          (float, int)), 'Values in opening hours must be of type int or ' \
                                         'float representing the hours of the day.'
        assert isinstance(_open,
                          (float, int)), 'Values in opening hours must be of type int or ' \
                                         'float representing the hours of the day.'

        assert _open <= _close, 'The first value (opening hour) is expected to be smaller than ' \
                                'the 2nd value (closing hour).'
        assert _close <= 24, 'The last value(closing hour) is expected to be smaller or equal to 24'
        assert _open >= 0, 'The first value(opening hour) is expected to be bigger or equal to 0'

        self.opening_hours = opening_hours
        return self
