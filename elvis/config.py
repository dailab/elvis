"""This module contains all classes necessary to configure scenarios that can then be simulated
by Elvis."""

import logging
import datetime
import pandas as pd
import math
import yaml
import gzip
import json

import elvis.sched.schedulers as schedulers
from elvis.charging_event_generator import create_charging_events_from_weekly_distribution as \
    events_from_week_arr_dist
from elvis.utility.elvis_general import create_time_steps
from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.charging_event import ChargingEvent
from elvis.distribution import EquallySpacedInterpolatedDistribution


class ScenarioConfig:
    """Describes a scenario defined by its stochastic distributions and hardware parameters."""
    def __init__(self, **kwargs):
        # Time series data
        self.emissions_scenario = None
        self.renewables_scenario = None

        self.transformer_preload = None
        self.transformer_preload_res_data = None
        self.transformer_preload_repeat = False

        # Event parameters
        self.arrival_distribution = None
        self.vehicle_types = []
        self.mean_park = None
        self.std_deviation_park = None
        self.mean_soc = None
        self.std_deviation_soc = None
        self.num_charging_events = None
        self.charging_events = None

        # Infrastructure (behaviour)
        self.infrastructure = None
        self.queue_length = None
        self.disconnect_by_time = None
        self.opening_hours = None
        self.scheduling_policy = None

        if 'emissions_scenario' in kwargs:
            self.emissions_scenario = kwargs['emissions_scenario']
        if 'renewables_scenario' in kwargs:
            self.renewables_scenario = kwargs['renewables_scenario']
        if 'transformer_preload' in kwargs:
            self.transformer_preload = kwargs['transformer_preload']

        if 'vehicle_types' in kwargs:
            self.vehicle_types = kwargs['vehicle_types']

        if 'opening_hours' in kwargs:
            self.opening_hours = kwargs['opening_hours']

        if 'charging_events' in kwargs:
            self.arrival_distribution = kwargs['arrival_distribution']
        if 'infrastructure' in kwargs:
            self.infrastructure = kwargs['infrastructure']
        if 'scheduling_policy' in kwargs:
            self.scheduling_policy = kwargs['scheduling_policy']
        if 'mean_park' in kwargs:
            self.mean_park = kwargs['mean_park']
        if 'std_deviation_park' in kwargs:
            self.std_deviation_park = kwargs['std_deviation_park']
        if 'mean_soc' in kwargs:
            self.mean_soc = kwargs['mean_soc']
        if 'std_deviation_soc' in kwargs:
            self.std_deviation_soc = kwargs['std_deviation_soc']
        if 'num_charging_events' in kwargs:
            self.num_charging_events = kwargs['num_charging_events']
        if 'queue_length' in kwargs:
            self.queue_length = kwargs['queue_length']
        if 'disconnect_by_time' in kwargs:
            self.disconnect_by_time = kwargs['disconnect_by_time']
        if 'transformer_preload_res_data' in kwargs:
            self.transformer_preload_res_data = kwargs['transformer_preload_res_data']
        if 'transformer_preload_repeat' in kwargs:
            self.transformer_preload_repeat = kwargs['transformer_preload_repeat']

    def __str__(self):
        printout = ''
        if self.vehicle_types is None:
            printout += str('Vehicle types: None\n')
        else:
            printout = ' Vehicle types: ' + str(vt + '\n' for vt in self.vehicle_types)

        printout += str('Mean parking time: ' + self.mean_park + '\n')
        printout += str('Std deviation of parking time: ' + self.std_deviation_park + '\n')
        printout += str('Mean value of the SOC distribution: ' + self.mean_soc + '\n')
        printout += str('Std deviation of the SOC distribution: ' + self.std_deviation_soc + '\n')
        printout += str('Number of charging events per week: ' + self.num_charging_events + '\n')

        if self.disconnect_by_time is True:
            printout += str('Vehicles are disconnected only depending on their parking time')
        else:
            printout += str('Vehicles are disconnected depending on their SOC and their parking'
                            'parking time (what ever comes first')
        if self.queue_length is None:
            printout += str('No queue is considered.')
        else:
            printout += str('Queue length: ' + self.queue_length + '\n')

        printout += str('Opening hours: ' + self.opening_hours + '\n')
        printout += str('Scheduling policy: ' + self.scheduling_policy + '\n')

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
        config.with_mean_park(dictionary['mean_park'])
        config.with_std_deviation_park(dictionary['std_deviation_park'])
        config.with_mean_soc(dictionary['mean_soc'])
        config.with_std_deviation_soc(dictionary['std_deviation_soc'])
        config.with_num_charging_events(dictionary['num_charging_events'])
        config.with_queue_length(dictionary['queue_length'])
        config.with_disconnect_by_time(dictionary['disconnect_by_time'])
        if 'resolution_preload' in dictionary:
            if 'repeat_preload' in dictionary:
                config.with_transformer_preload(dictionary['transformer_preload'],
                                                res_data=dictionary['resolution_preload'],
                                                repeat=dictionary['repeat_preload'])
            else:
                config.with_transformer_preload(dictionary['transformer_preload'],
                                                res_data=dictionary['resolution_preload'])
        elif 'repeat_preload' in dictionary:
            config.with_transformer_preload(dictionary['transformer_preload'],
                                            repeat=dictionary['repeat_preload'])
        else:
            config.with_transformer_preload(dictionary['transformer_preload'])

        config.with_vehicle_types(vehicle_types=dictionary['vehicle_types'])
        # TODO: Adjust with_wrrival_distribution method
        config.with_arrival_distribution(dictionary['arrival_distribution'])

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
                                       'Scenario config must be a dict.'

        return ScenarioConfig.from_dict(yaml_str)

    def create_realisation(self, start_date, end_date, resolution):
        """Creates a realisation of self given the required time parameters.

        Args:
            start_date: (:obj: `datetime.datetime`): First time stamp.
            end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
            resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

        Returns:
            realisation: (:obj: `elvis.config.ScenarioRealisation`): Scenario realisation.
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

    def with_transformer_preload(self, transformer_preload):
        # TODO: Add pandas
        assert type(transformer_preload) is list, 'Arrival distribution must be of type list or ' \
                                                   'pandas DataFrame.'

        msg_invalid_value_type = "Arrival distribution should be of type: pandas DataFrame or a " \
                                 "list containing float or int."
        # Check if all values in list are either float or int
        if transformer_preload is list:
            assert all(isinstance(x, (float, int)) for x in transformer_preload), \
                msg_invalid_value_type
        else:
            NotImplementedError()

        self.arrival_distribution = transformer_preload

        return

    # Outdated
    def with_charging_events(self, charging_events):
        """Update the arrival distribution to use.
        """

        if isinstance(charging_events[0], ChargingEvent):
            self.charging_events = charging_events

        elif type(charging_events[0]) is float or type(charging_events[0]) is int:
            msg_params_missing = 'Please assign config.num_charging_events and ' \
                                 'config.time_params, config.mean_park, config.std_deviation_' \
                                 'park, config.mean_soc, config.std_deviatoin_soc, ' \
                                 'before using config.with_charging_events with an ' \
                                 'arrival distribution.'

            assert type(self.num_charging_events) is int, \
                'Builder.num_charging_events not initialised. ' + msg_params_missing
            assert type(self.start_date) is not None, \
                'Builder.start_date not initialised. ' + msg_params_missing
            assert type(self.end_date) is not None, \
                'Builder.end_date not initialised. ' + msg_params_missing
            assert type(self.resolution) is not None, \
                'Builder.resolution not initialised. ' + msg_params_missing
            assert type(self.mean_park) is not None, \
                'Builder.mean_park not initialised. ' + msg_params_missing
            assert type(self.std_deviation_park) is not None, \
                'Builder.std_deviation not initialised. ' + msg_params_missing
            assert type(self.mean_soc) is not None, \
                'Builder.mean_soc not initialised. ' + msg_params_missing
            assert type(self.std_deviation_soc) is not None, \
                'Builder.std_deviation_soc not initialised. ' + msg_params_missing

            time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)

            # call elvis.charging_event_generator.create_charging_events_from_distribution
            self.charging_events = events_from_week_arr_dist(charging_events, time_steps,
                                                             self.num_charging_events, self.mean_park,
                                                             self.std_deviation_park, self.mean_soc,
                                                             self.std_deviation_soc, self.vehicle_types)

        return self

    def with_emissions_scenario(self, emissions_scenario):
        """Update the emissions scenario to use."""

        self.emissions_scenario = emissions_scenario
        return self

    def with_renewables_scenario(self, renewables_scenario):
        """Update the renewable energy scenario to use."""

        self.renewables_scenario = renewables_scenario
        return self

    def with_transformer_preload(self, transformer_preload, res_data=None, repeat=False):
        # TODO: Add pandas
        if type(transformer_preload) is pd.DataFrame:
            NotImplementedError()
        else:
            assert type(transformer_preload) is list, 'Transformer preload must be of type list ' \
                                                      'or pandas DataFrame.'

            msg_invalid_value_type = "Transformer preload should be of type: pandas DataFrame or" \
                                     " a list containing float or int."
            # Check if all values in list are either float or int
            assert all(isinstance(x, (float, int)) for x in transformer_preload), \
                msg_invalid_value_type

            self.transformer_preload = transformer_preload

        if res_data is not None:
            # TODO: Add pandas time strings
            assert type(res_data) is datetime.timedelta, 'The data resolution must be of type ' \
                                                         'datetime.datetime.'
            self.transformer_preload_res_data = res_data

        if repeat is not False:
            assert type(repeat) is bool, 'Repeat can only be True or False.'
            self.transformer_preload_repeat = True

            return

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
            return

        # ensure input is str. If not return default
        if type(scheduling_policy_input) is not str:
            logging.error('Scheduling policy should be of type str or an instance of '
                          'SchedulingPolicy. The uncontrolled strategy has been used as a default.')
            self.scheduling_policy = scheduling_policy
            return

        # Match string
        if scheduling_policy_input in ('Uncontrolled', 'UC', 'Uc', 'uc'):
            scheduling_policy = schedulers.Uncontrolled()

        elif scheduling_policy_input in ('Discrimination Free', 'DF', 'df'):
            scheduling_policy = schedulers.DiscriminationFree()

        elif scheduling_policy_input == 'FCFS':
            scheduling_policy = schedulers.FCFS()

        elif scheduling_policy_input in ('With Storage', 'ws', 'WS'):
            scheduling_policy = schedulers.WithStorage()

        elif scheduling_policy_input in ('Optimized', 'opt', 'OPT'):
            scheduling_policy = schedulers.Optimized()

        # invalid str use default: Uncontrolled
        else:
            logging.error('"%s" can not be matched to any existing scheduling policy.'
                          'Please use: "Uncontrolled", "Discrimination Free", "FCFS", '
                          '"With Storage" or "Optimized". '
                          'Uncontrolled is the default value and has been used for the simulation.',
                          str(scheduling_policy_input))

        self.scheduling_policy = scheduling_policy
        return self

    def with_infrastructure(self, infrastructure):
        """Update the charging points to use."""
        assert type(infrastructure) is dict
        self.infrastructure = infrastructure
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

        # get instance of battery
        battery = EVBattery(capacity=capacity, max_charge_power=max_charge_power,
                            min_charge_power=min_charge_power, efficiency=efficiency, )

        # get instance of ElectricVehicle with initialized battery
        self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
        return self

    def with_opening_hours(self, opening_hours):
        """Update the opening hours to use."""

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
            if type(kwargs['start_date']) is str:
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
                    print('Incorrect timedelta format for resolution pls use: %H:%M:%S')
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
            self.emissions_scenario = config.emissions_scenario
            self.renewables_scenario = config.emissions_scenario
            self.opening_hours = config.opening_hours
            self.infrastructure = config.infrastructure
            self.scheduling_policy = config.scheduling_policy
            self.queue_length = config.queue_length
            self.disconnect_by_time = config.disconnect_by_time
            self.transformer_preload = self.with_transformer_preload(
                config.transformer_preload, config.transformer_preload_res_data,
                config.transformer_preload_repeat)

            if config.charging_events is not None:
                self.charging_events = config.charging_events
            else:
                self.transform_arrival_distribution()
                # TODO: Differentiation needed. What if other than a one week period data is passed.
                time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                self.charging_events = events_from_week_arr_dist(
                    config.arrival_distribution, time_steps, config.num_charging_events,
                    config.mean_park, config.std_deviation_park, config.mean_soc,
                    config.std_deviation_soc, config.vehicle_types)

        else:
            self.check_input(**kwargs)
            self.emissions_scenario = kwargs['emissions_scenario']
            self.renewables_scenario = kwargs['renewables_scenario']
            self.opening_hours = kwargs['opening_hours']
            self.infrastructure = kwargs['infrastructure']
            self.scheduling_policy = kwargs['scheduling_policy']
            self.queue_length = kwargs['queue_length']
            self.disconnect_by_time = kwargs['disconnect_by_time']
            self.start_date = kwargs['start_date']
            self.end_date = kwargs['end_date']
            self.resolution = kwargs['resolution']

            if 'charging_events' in kwargs:
                self.charging_events = [ChargingEvent.from_dict(**ce)
                                        for ce in kwargs['charging_events']]
            else:
                time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)
                self.charging_events = events_from_week_arr_dist(
                    kwargs['arrival_distribution'], time_steps, kwargs['num_charging_events'],
                    kwargs['mean_park'], kwargs['std_deviation_park'], kwargs['mean_soc'],
                    kwargs['std_deviation_soc'], kwargs['vehicle_types'])

        return

    def to_dict(self):
        dictionary = self.__dict__

        dictionary['scheduling_policy'] = str(self.scheduling_policy)
        # TODO: what if time series data is not a list
        dictionary['emissions_scenario'] = self.emissions_scenario
        dictionary['renewables_scenario'] = self.renewables_scenario
        dictionary['renewables_scenario'] = self.renewables_scenario

        # TODO: Once opening hours data format is determined convert it properly
        dictionary['opening_hours'] = self.opening_hours
        dictionary['charging_events'] = [ce.to_dict() for ce in self.charging_events]

        dictionary['start_date'] = str(self.start_date.isoformat())
        dictionary['end_date'] = str(self.end_date.isoformat())
        dictionary['resolution'] = str(self.resolution)

        return dictionary

    @staticmethod
    def from_dict(dictionary):
        realisation = ScenarioRealisation(**dictionary)
        return realisation

    # https://stackoverflow.com/questions/39450065/python-3-read-write-compressed-json-objects-from-to-gzip-file
    def to_json(self, file_path):
        data = self.to_dict()

        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')

        with gzip.GzipFile(file_path, 'w') as fout:
            fout.write(json_bytes)

        return

    @staticmethod
    def from_json(json_file_name):
        with gzip.GzipFile(json_file_name, 'r') as fin:
            json_bytes = fin.read()

        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)

        return ScenarioRealisation.from_dict(data)

    def transform_arrival_distribution(self):
        pass

    def with_transformer_preload(self, transformer_preload, res_data=None, repeat=False):
        """Update the renewable energy scenario to use.
        Simulation time parameter must be set before transformer preload can be initialised."""
        # TODO: if trafo preload has another res_data than simulation or an offset a correct list
        # must be created

        """List possible cases:
        Case 1:
            List has n=simulationSteps entries.
            Meta info: None
            To Do: Nothing just pass.
        Case 2:
            List has n=simulationSteps entries.
            Meta info: Resolution. Repeat.
        Case 3:
            List has n!=simulation step entries.
            Meta info: None.
            To Do: Raise error
        Case 4:
            List has n!=simulationSteps entries.
            Meta info: Resolution.
            To Do: Adjust res_data as stated. Check if there are enough values. If not raise error

        Case 5:
            List has n!=simulationSteps entries.
            Meta info: Resolution. Repeat.
            To Do: Adjust Resolution. Repeat until n equals simulaiton steps.

        Case 7:
            DF has n=simulationSteps rows.
            Index of DF aligns with simulationSteps.
            To Do: Nothing just pass.
        Case 8:
            DF has n=simulationSteps rows.
            Index of DF does not align with simulationSteps."""

        def adjust_resolution(preload, res_data, res_simulation):
            """Adjusts res_data of the transformer preload to the simulation res_data.

            Args:
                preload: (list): Containing the transformer preload in "wrong"
                    res_data.
                res_data: (datetime.timedelta): Time in between two adjacent data points of
                    transformer preload with "wrong" res_data.
                res_simulation: (datetime.timedelta): Time in between two adjacent time steps in
                    the simulation.

            Returns:
                transformer_preload_new_res: (list): Transformer preload with linearly interpolated data
                    points having the res_data of the simulation.
                """

            x_values = list(range(len(preload)))
            distribution = EquallySpacedInterpolatedDistribution.linear(
                list(zip(x_values, preload)), None)

            coefficient = res_simulation / res_data
            x_values_new_res = list(range(math.ceil(len(preload) * 1 / coefficient)))
            x_values_new_res = [x * coefficient for x in x_values_new_res]

            transformer_preload_new_res = []
            for x in x_values_new_res:
                transformer_preload_new_res.append(distribution[x])

            return transformer_preload_new_res

        def repeat_data(preload, num_simulation_steps):
            """Repeats the transformer preload data until there are as many values as there are
            simulation steps.

            Args:
                preload: (list): Containing the data (floats) to be repeated.
                num_simulation_steps: (int): Number of simulation steps and expected length of
                    the transformer preload after it is repeated.

            Returns:
                transformer_preload_repeated: (list): Repeated values. len() = num_simulation_steps.
                """

            n = math.floor(num_simulation_steps / len(preload))

            transformer_preload_repeated = preload * n

            values_to_add = num_simulation_steps - len(transformer_preload_repeated)

            transformer_preload_repeated += preload[:values_to_add]

            return transformer_preload_repeated

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
            num_values = len(transformer_preload)
        else:  # list or numeric
            num_simulation_steps = int((self.end_date - self.start_date) / self.resolution) + 1

            if isinstance(transformer_preload, (int, float)):
                transformer_preload = [transformer_preload]

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

