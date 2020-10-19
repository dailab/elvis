import logging
import datetime
import pandas as pd
import math
import yaml

import elvis.sched.schedulers as schedulers
from elvis.charging_event_generator import create_charging_events_from_distribution as create_events
from elvis.charging_event_generator import create_time_steps
from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.charging_event import ChargingEvent
from elvis.distribution import EquallySpacedInterpolatedDistribution


class ElvisConfig:
    """This class contains the relevant parameters to execute the charging simulation.

    Users of Elvis should not create instances of ElvisConfig directly but rather use 
    the ElvisConfigBuilder class, which sets sensible defaults and prevents incoherent
    configurations.
    """

    def __init__(self, charging_events, emissions_scenario, renewables_scenario,
                 infrastructure, vehicle_types, scheduling_policy, opening_hours, time_params,
                 num_charging_events, transformer_preload, mean_park, std_deviation_park,
                 queue_length=0, disconnect_by_time=True):
        """Create an ElvisConfig given all parameters.

        Args:
            charging_events: (list): Instances of type :obj: `charging_event.ChargingEvent`.
                Describing a charging event with its arrival time, arrival and target SOC as well
                as the vehicle type containing important information about the battery.
            time_params: (tuple): start date as :obj: `datetime.datetime`,
                end date as :obj: `datetime.datetime`,
                step size as :obj: `datetime.timedelta`.
            num_charging_events: (int): Total amount of charging events per week.
            transformer_preload: (list): Contains floats representing the preload at the
                transformer. Must have the same length as there are time steps in the simulation.
            queue_length: (int): Max length of waiting queue for vehicles.
            disconnect_by_time: (bool): True if cars are disconnected due to their parking time.
                False if cars are disconnected due to their SOC limit.
            mean_park: (float): Mean of the gaussian distribution the parking time is generated
                from.
            std_deviation_park: (float): Standard deviation of the gaussian distribution the parking
                time is generated from.
        """
        # not needed yet
        self.emissions_scenario = emissions_scenario
        self.renewables_scenario = renewables_scenario
        self.vehicle_types = vehicle_types

        self.opening_hours = opening_hours
        # TODO: Check that the preload and the time steps have same length
        self.transformer_preload = transformer_preload

        # already in use
        self.charging_events = charging_events
        self.infrastructure = infrastructure
        self.scheduling_policy = scheduling_policy
        self.start_date = time_params[0]
        self.end_date = time_params[1]
        self.resolution = time_params[2]

        self.mean_park = mean_park
        self.std_deviation_park = std_deviation_park

        self.num_charging_events = num_charging_events
        self.queue_length = queue_length
        self.disconnect_by_time = disconnect_by_time

    def num_simulation_steps(self):
        """Returns the number of simulation steps based on currently assigned time parameters."""
        return int((self.end_date - self.start_date) / self.resolution) + 1

    def to_yaml(self):
        """Serialize this ElvisConfig to a yaml string."""

        pass

    @staticmethod
    def from_yaml(yaml_str):
        """Create an ElvisConfig from a yaml string."""

        pass

    @staticmethod
    def from_json(json_str):
        """Create an ElvisConfig from a yaml string."""

        pass


class InvalidConfigException(Exception):
    pass


class ElvisConfigBuilder:
    """Helper class to simplify the creation of ElvisConfig objects.
    For further information about the variables please refer to :obj: `config.ElvisConfig`"""

    def __init__(self):
        # The distribution of vehicle arrivals (TODO: how is this represented? what are the options?)
        self.charging_events = None

        # The CO2 emissions scenario (TODO: how is this represented? what are the options?)
        self.emissions_scenario = None

        # The renewable energy usage scenario (TODO: how is this represented? what are the options?)
        self.renewables_scenario = None

        # List of charging points available at this location
        self.infrastructure = []

        # List of supported vehicle types
        self.vehicle_types = []

        # The control strategy to use for the simulation (TODO: better here or as an argument to the simulate method?)
        self.scheduling_policy = None

        # The opening hours of the parking lot
        self.opening_hours = None

        # Initial date the simulation starts off with (TODO: prob str to datetime.datetime conversion necessary)
        self.start_date = None
        # End of simulation period (TODO: prob str to datetime.datetime conversion necessary)
        self.end_date = None
        # Time in between two adjacent time steps (minutes, hours...). TODO: Define convention how to pass (hours, minutes, as datetime.timedelta object?)
        self.resolution = None

        # Number of charging events per week on average TODO: Is week still okay? or better day?
        self.num_charging_events = None

        # Maximum number of cars that can be simultaneously in the queue [0, infinity)
        self.queue_length = None

        # What is the condition to be met for disconnection at the connection point
        # time or energy or?
        self.disconnect_by_time = None

        # Transformer preload as a list. Is supposed to have the same length as the time steps.
        self.transformer_preload = None

        # Std deviation and mean of the gaussian distribution the parking time of car is generated
        # from
        self.mean_park = None
        self.std_deviation_park = None

    def build(self):
        """Create the ElvisConfig with the passed parameters."""

        err_msg = self.validate_params()
        # TODO: None is not always an error
        # if err_msg is not None:
        #     raise InvalidConfigException(err_msg)

        time_params = (self.start_date, self.end_date, self.resolution)
        config = ElvisConfig(self.charging_events, self.emissions_scenario,
                             self.renewables_scenario, self.infrastructure, self.vehicle_types,
                             self.scheduling_policy, self.opening_hours, time_params,
                             self.num_charging_events, self.transformer_preload, self.queue_length,
                             self.disconnect_by_time)
        return config

    def validate_params(self):
        # TODO: validate types + check for missing params
        if self.charging_events is None:
            return "no arrival distribution specified"
        if self.emissions_scenario is None:
            return "no emissions scenario specified"
        if self.renewables_scenario is None:
            return "no renewables scenario specified"
        if self.scheduling_policy is None:
            return "no scheduling policy specified"
        if self.opening_hours is None:
            return "no opening hours specified"
        if self.start_date is None:
            return 'no start date specified'
        if self.end_date is None:
            return 'no end date specified'
        if self.resolution is None:
            return 'no time resolution specified'
        if self.num_charging_events is None:
            return 'no number of charging events per week specified'
        # queue_length == None means no queue used
        # if self.queue_length is None:
        #     return 'no queue length specified'
        if self.disconnect_by_time is None:
            return 'no disconnect by time specified'

        if not isinstance(self.scheduling_policy, schedulers.SchedulingPolicy):
            return "scheduling policy must be a subclass of elvis.sched.SchedulingPolicy"

        return None

    def to_dict(self):
        dictionary = dict()
        dictionary['charging_events'] = [ce.to_dict() for ce in self.charging_events]
        dictionary['infrastructure'] = self.infrastructure
        dictionary['scheduling_policy'] = str(self.scheduling_policy)
        dictionary['time_params'] = (str(self.start_date.isoformat()),
                                     str(self.end_date.isoformat()),
                                     str(self.resolution))
        dictionary['mean_park'] = self.mean_park
        dictionary['std_deviation_park'] = self.std_deviation_park
        dictionary['num_charging_events'] = self.num_charging_events
        dictionary['queue_length'] = self.queue_length
        dictionary['disconnect_by_time'] = self.disconnect_by_time
        dictionary['transformer_preload'] = self.transformer_preload
        dictionary['vehicle_types'] = [vehicle.to_dict() for vehicle in self.vehicle_types]

        return dictionary

    def to_yaml(self, yaml_file):
        """Serialize this ElvisConfig to a yaml string."""
        data_to_store = self.to_dict()

        with open(yaml_file, 'w') as file:
            yaml.dump(data_to_store, file)

        return

    def from_yaml(self, yaml_str):
        """Create an ElvisConfig from a yaml string."""

        self.infrastructure = yaml_str['infrastructure']
        self.with_scheduling_policy(yaml_str['scheduling_policy'])
        self.with_time_params(yaml_str['time_params'])
        self.with_mean_park(yaml_str['mean_park'])
        self.with_std_deviation_park(yaml_str['std_deviation_park'])
        self.with_num_charging_events(yaml_str['num_charging_events'])
        self.with_queue_length(yaml_str['queue_length'])
        self.with_disconnect_by_time(yaml_str['disconnect_by_time'])
        if 'resolution_preload' in yaml_str.keys():
            if 'repeat_preload' in yaml_str.keys():
                self.with_transformer_preload(yaml_str['transformer_preload'],
                                              res_data=yaml_str['resolution_preload'],
                                              repeat=yaml_str['repeat_preload'])
            else:
                self.with_transformer_preload(yaml_str['transformer_preload'],
                                              res_data=yaml_str['resolution_preload'])
        elif 'repeat_preload' in yaml_str.keys():
            self.with_transformer_preload(yaml_str['transformer_preload'],
                                          repeat=yaml_str['repeat_preload'])
        else:
            self.with_transformer_preload(yaml_str['transformer_preload'])
        vehicle_types = yaml_str['vehicle_types']
        self.with_vehicle_types(vehicle_types=yaml_str['vehicle_types'])
        self.with_charging_events(yaml_str['charging_events'])

        return self

    def with_charging_events(self, charging_events):
        """Update the arrival distribution to use.
        TODO: Should setting up charging_events with an arrival distribution as list should be
        a different method?
        TODO: only type list with 168 values for now if setting events up with arrival distribution.
        """

        if isinstance(charging_events[0], ChargingEvent):
            self.charging_events = charging_events

        elif type(charging_events[0]) is float or type(charging_events[0]) is int:
            msg_params_missing = 'Please assign builder.num_charging_events and ' \
                                 'builder.time_params, builder.mean_park, builder.std_deviation_' \
                                 'park before using builder.with_charging_events with an ' \
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
                'Builder.resolution not initialised. ' + msg_params_missing
            assert type(self.std_deviation_park) is not None, \
                'Builder.resolution not initialised. ' + msg_params_missing

            time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)

            # call elvis.charging_event_generator.create_charging_events_from_distribution
            self.charging_events = create_events(charging_events, time_steps,
                                                 self.num_charging_events, self.mean_park,
                                                 self.std_deviation_park, self.vehicle_types)

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

                transformer_preload = adjust_resolution(transformer_preload, res_data, self.resolution)

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
                    self.add_vehicle_type(vehicle_type=vehicle_type)
                elif isinstance(vehicle_type, dict):
                    self.add_vehicle_type(**vehicle_type)
                else:
                    # TODO: List relevant information.
                    raise TypeError('Using with_vehicle_types with a list: All list entries '
                                    'must either be of type ElectricVehicle or dict, containing'
                                    'all relevant information.')

            return self
        else:
            self.add_vehicle_type(**kwargs)
            return self

    def add_vehicle_type(self, vehicle_type=None, **kwargs):
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

        assert 'brand' in kwargs.keys()
        assert 'model' in kwargs.keys()
        assert 'probability' in kwargs.keys()
        assert 'battery' in kwargs.keys()

        brand = str(kwargs['brand'])
        model = str(kwargs['model'])
        probability = kwargs['probability']

        # if all fields of ElectricVehicle are passed and an instance of EVBattery is already made
        if isinstance(kwargs['battery'], EVBattery):
            battery = kwargs['battery']
            self.vehicle_types.append(ElectricVehicle(brand, model, battery))
            return

        # if there is no instance of EVBattery check if all parameters are passed.
        assert 'capacity' in kwargs['battery'].keys()
        assert 'max_charge_power' in kwargs['battery'].keys()
        assert 'min_charge_power' in kwargs['battery'].keys()
        assert 'efficiency' in kwargs['battery'].keys()

        capacity = kwargs['battery']['capacity']
        max_charge_power = kwargs['battery']['max_charge_power']
        min_charge_power = kwargs['battery']['min_charge_power']
        efficiency = kwargs['battery']['efficiency']

        # get instance of battery
        battery = EVBattery(capacity=capacity, max_charge_power=max_charge_power,
                            min_charge_power=min_charge_power, efficiency=efficiency,)

        # get instance of ElectricVehicle with initialized battery
        self.vehicle_types.append(ElectricVehicle(brand, model, battery, probability))
        return self

    def with_opening_hours(self, opening_hours):
        """Update the opening hours to use."""

        self.opening_hours = opening_hours
        return self

    def with_time_params(self, time_params):
        """Update the start date to use.

        Args:
            time_params: (tuple): (Start date, end date, resolution). Start and end date can either
                be of type :obj: `datetime.datetime` or str. Resolution can be of type
                :obj: `datetime.timedelta` or of type str.

        Format:
            Date format for str:        %y-%m-%d %H:%M:%S
            Resolution format for str:  %H:%M:%S

        Raises:
            TypeError: If the variables are neither of type str or datetime for start and end
                date or timedelta for resolution.
            ValueError: If any of the variables is of type str and does not conform to formatting.

        TODO: Should time_params rather be split into its 3 components?
            """

        date_format = '%y-%m-%d %H:%M:%S'

        # start date
        if type(time_params[0]) is datetime.datetime:
            self.start_date = time_params[0]
        elif type(time_params[0]) is str:
            try:
                self.start_date = datetime.datetime.fromisoformat(time_params[0])
            except ValueError:
                logging.error('"%s" is of incorrect format. Please use %s',
                              time_params[0], date_format)
                raise ValueError
        else:
            logging.error('Start date must be of type datetime or of type str in following '
                          'notation: %s', date_format)
            raise TypeError

        # end date
        if type(time_params[1]) is datetime.datetime:
            self.end_date = time_params[1]
        elif type(time_params[1]) is str:
            try:
                self.end_date = datetime.datetime.fromisoformat(time_params[1])
            except ValueError:
                logging.error('"%s" is of incorrect format. Please use %s',
                              time_params[1], date_format)
                raise ValueError
        else:
            logging.error('End date must be of type datetime or of type str in following '
                          'notation: %s', date_format)
            raise TypeError

        # Check if start date < end date

        if self.start_date > self.end_date:
            logging.error('Start date is after end date. The dates have been swapped for this '
                          'simulation.')
            start_date = self.start_date
            self.start_date = self.end_date
            self.end_date = start_date

        # resolution
        time_format = '%H:%M:%S'
        if type(time_params[2]) is datetime.timedelta:
            self.start_date = time_params[2]
        elif type(time_params[0]) is str:
            try:
                date = datetime.datetime.strptime(time_params[2], time_format)
                self.resolution = datetime.timedelta(hours=date.hour, minutes=date.minute,
                                                     seconds=date.second)
            except ValueError:
                logging.error('%s is of incorrect format. Please use %s',
                              time_params[2], time_format)
                raise ValueError
        else:
            logging.error('Resolution must be of type timedelta or of type str in following '
                          'notation: %s', date_format)
            raise TypeError
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
        assert isinstance(std_deviation_park, (int, float))
        self.std_deviation_park = std_deviation_park
        return self
