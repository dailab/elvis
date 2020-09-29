import logging
import datetime

import elvis.sched.schedulers as schedulers
from elvis.charging_event_generator import create_charging_events_from_distribution as create_events
from elvis.charging_event_generator import create_time_steps
from elvis.battery import EVBattery
from elvis.vehicle import ElectricVehicle
from elvis.charging_event import ChargingEvent


class ElvisConfig:
    """This class contains the relevant parameters to execute the charging simulation.

    Users of Elvis should not create instances of ElvisConfig directly but rather use 
    the ElvisConfigBuilder class, which sets sensible defaults and prevents incoherent
    configurations.
    """

    def __init__(self, charging_events, emissions_scenario, renewables_scenario,
                 infrastructure, vehicle_types, scheduling_policy, opening_hours, time_params,
                 num_charging_events, transformer_preload, queue_length=0, disconnect_by_time=True):
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

        self.num_charging_events = num_charging_events
        self.queue_length = queue_length
        self.disconnect_by_time = disconnect_by_time

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
                                 'builder.time_params before using ' \
                                 'builder.with_charging_events with an arrival distribution.'

            assert type(self.num_charging_events) is int, \
                'Builder.num_charging_events not initialised. ' + msg_params_missing
            assert type(self.start_date) is not None, \
                'Builder.start_date not initialised. ' + msg_params_missing
            assert type(self.end_date) is not None, \
                'Builder.end_date not initialised. ' + msg_params_missing
            assert type(self.resolution) is not None, \
                'Builder.resolution not initialised. ' + msg_params_missing

            time_steps = create_time_steps(self.start_date, self.end_date, self.resolution)

            # call elvis.charging_event_generator.create_charging_events_from_distribution
            self.charging_events = create_events(charging_events, time_steps,
                                                 self.num_charging_events)

        return self

    def with_emissions_scenario(self, emissions_scenario):
        """Update the emissions scenario to use."""

        self.emissions_scenario = emissions_scenario
        return self

    def with_renewables_scenario(self, renewables_scenario):
        """Update the renewable energy scenario to use."""

        self.renewables_scenario = renewables_scenario
        return self

    def with_transformer_preload(self, transformer_preload):
        """Update the renewable energy scenario to use."""
        # TODO: if trafo preload has another resolution than simulation or an offset a correct list
        # must be created
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
        if scheduling_policy_input == 'Uncontrolled':
            scheduling_policy = schedulers.Uncontrolled()

        elif scheduling_policy_input == 'Discrimination Free':
            scheduling_policy = schedulers.DiscriminationFree()

        elif scheduling_policy_input == 'FCFS':
            scheduling_policy = schedulers.FCFS()

        elif scheduling_policy_input == 'With Storage':
            scheduling_policy = schedulers.WithStorage()

        elif scheduling_policy_input == 'Optimized':
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

    def with_vehicle_types(self, vehicle_types):
        """Update the vehicle types to use."""
        for vehicle_type in vehicle_types:
            assert isinstance(vehicle_type, ElectricVehicle)

        self.vehicle_types = vehicle_types
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
        brand = str(kwargs['brand'])
        model = str(kwargs['model'])

        # if all fields of ElectricVehicle are passed and an instance of EVBattery is already made
        if 'battery' in kwargs.keys():
            assert isinstance(kwargs['battery'], EVBattery)
            battery = kwargs['battery']
            self.vehicle_types.append(ElectricVehicle(brand, model, battery))

        # if no instance of EVBattery is already made check if all parameters are passed.
        assert 'capacity' in kwargs.keys()
        assert 'max_charge_power' in kwargs.keys()
        assert 'min_charge_power' in kwargs.keys()
        assert 'efficiency' in kwargs.keys()

        capacity = kwargs['capacity']
        max_charge_power = kwargs['max_charge_power']
        min_charge_power = kwargs['min_charge_power']
        efficiency = kwargs['efficiency']

        # get instance of battery
        battery = EVBattery(capacity=capacity, max_charge_power=max_charge_power,
                            min_charge_power=min_charge_power, efficiency=efficiency)

        # get instance of ElectricVehicle with initialized battery
        self.vehicle_types.append(ElectricVehicle(brand, model, battery))
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
