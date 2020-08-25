
import sched


class ElvisConfig:
    """This class contains the relevant parameters to execute the charging simulation.

    Users of Elvis should not create instances of ElvisConfig directly but rather use 
    the ElvisConfigBuilder class, which sets sensible defaults and prevents incoherent
    configurations.
    """

    def __init__(self, arrival_distribution, emissions_scenario, renewables_scenario,
                 charging_points, vehicle_types, scheduling_policy, opening_hours, time_params,
                 num_charging_events, queue_length=0, disconnect_by_time=True):
        """Create an ElvisConfig given all parameters.

        Args:
            time_params: (tuple): start date as :obj: `datetime.datetime`,
                end date as :obj: `datetime.datetime`,
                step size as :obj: `datetime.timedelta`.
            num_charging_events: (int): Total amount of charging events per week.
            queue_length: (int): Max length of waiting queue for vehicles.
            disconnect_by_time: (bool): True if cars are disconnected due to their parking time.
            False if cars are disconnected due to their SOC limit.


        """

        self.arrival_distribution = arrival_distribution
        self.emissions_scenario = emissions_scenario
        self.renewables_scenario = renewables_scenario
        self.charging_points = charging_points
        self.vehicle_types = vehicle_types
        self.scheduling_policy = scheduling_policy
        self.opening_hours = opening_hours

        self.start_date = time_params[0]
        self.end_date = time_params[1]
        self.resolution = time_params[2]

        self.num_charging_events = num_charging_events
        self.queue_length = queue_length
        self.disconnect_by_time = disconnect_by_time

        # The cached results
        self._result = None

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
    """Helper class to simplify the creation of ElvisConfig objects."""

    def __init__(self):
        # The distribution of vehicle arrivals (TODO: how is this represented? what are the options?)
        self.arrival_distribution = None

        # The CO2 emissions scenario (TODO: how is this represented? what are the options?)
        self.emissions_scenario = None

        # The renewable energy usage scenario (TODO: how is this represented? what are the options?)
        self.renewables_scenario = None

        # List of charging points available at this location
        self.charging_points = []

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

    def build(self):
        """Create the ElvisConfig with the passed parameters."""

        err_msg = self.validate_params()
        if err_msg is not None:
            raise InvalidConfigException(err_msg)

    def validate_params(self):
        # TODO: validate types + check for missing params
        if self.arrival_distribution is None:
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
        if self.queue_length is None:
            return 'no queue length specified'
        if self.disconnect_by_time is None:
            return 'no disconnect by time specified'

        if not isinstance(self.scheduling_policy, sched.SchedulingPolicy):
            return "scheduling policy must be a subclass of elvis.sched.SchedulingPolicy"

        return None

    def with_arrival_distribution(self, arrival_distribution):
        """Update the arrival distribution to use."""

        self.arrival_distribution = arrival_distribution

    def with_emissions_scenario(self, emissions_scenario):
        """Update the emissions scenario to use."""

        self.emissions_scenario = emissions_scenario

    def with_renewables_scenario(self, renewables_scenario):
        """Update the renewable energy scenario to use."""

        self.renewables_scenario = renewables_scenario

    def with_scheduling_policy(self, scheduling_policy):
        """Update the scheduling policy to use."""

        self.scheduling_policy = scheduling_policy

    def with_charging_points(self, charging_points):
        """Update the charging points to use."""

        self.charging_points = charging_points

    def add_charging_point(self, charging_point):
        """Add a charging point to this configuration."""

        self.charging_points.append(charging_point)

    def with_vehicle_types(self, vehicle_types):
        """Update the vehicle types to use."""

        self.vehicle_types = vehicle_types

    def add_vehicle_type(self, vehicle_type):
        """Add a supported vehicle type to this configuration."""

        self.vehicle_types.append(vehicle_type)

    def with_opening_hours(self, opening_hours):
        """Update the opening hours to use."""

        self.opening_hours = opening_hours

    def with_time_params(self, time_params):
        """Update the start date to use
        TODO: Check if start date <= end date - resolution"""
        self.start_date = time_params[0]
        self.end_date = time_params[1]
        self.resolution = time_params[2]

    def with_num_charging_events(self, num_charging_events):
        """Update the number of charging events to use."""
        self.num_charging_events = num_charging_events

    def with_queue_length(self, queue_length):
        """Update maximal length of queue."""
        self.queue_length = queue_length

    def with_disconnect_by_time(self, disconnect_by_time):
        """Update decision variable on how to disconnect cars."""
        self.disconnect_by_time = disconnect_by_time
