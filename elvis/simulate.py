import datetime
import math
import numpy as np

import distribution


def time_stamp_to_hours(time_stamps):
    """Calculates for each time stamp in a list the amount of hours passed
        since the beginning of the hour of the first time stamp.

    Args:
        time_stamps (list): Containing the time stamps as :obj: `datetime.datetime`.

    Returns:
        list: Hours passed.
    """
    start = time_stamps[0]
    hours_passed = []
    for time_stamp in time_stamps:
        delta = time_stamp - start
        hour = delta.days * 24 + delta.seconds / 3600 + delta.microseconds / 3600 / 1000
        # add offset
        hour += start.minute / 60 + start.second / 3600 + start.microsecond / 3600 / 1000
        hours_passed.append(hour)
    return hours_passed


def allign_distribution(distr, first_time_stamp, last_time_stamp):
    """Receives weekly distribution in hourly resolution besides a starting and an
    ending time_stamp. Shifts and multiplies distribution to allign it to the
     period of the time_stamps.

    Args:
        distribution (list): Containing hourly probabilities.
        first_time_stamp (:obj: `datetime.datetime`): Start of period.
        last_time_stamp (:obj: `datetime.datetime`): End of period.

    Returns:
        list: Containing the probabilities alligned to period.
    """
    starting_hour = first_time_stamp.weekday() * 24 + first_time_stamp.hour
    period = last_time_stamp - first_time_stamp
    # Upward estimate of the needed length of the distribution
    total_hours = period.total_seconds() / 3600
    total_weeks = math.ceil(total_hours / 168)

    alligned_distribution = distr[starting_hour:] + distr * total_weeks
    return alligned_distribution


def create_vehicle_arrivals(config, time_steps):
    """Creates vehicle arrival times.

    Args:
          time_steps (list): List containing all time steps as :obj: `datetime.datetime` object.

    Returns:
        list: Arrival times.

    ToDo:
        seeding seems to not work properly. With fixed seed small changes are still there,
        changing the seed has a huge impact though.
    """
    arrival_distribution = config.arrival_distribution
    num_charging_events = config.num_charging_events

    # Rearrange arrival distribution so it starts with first hour of simulation time
    arrival_distribution = allign_distribution(arrival_distribution, time_steps[0], time_steps[-1])

    # Create distribution based on reordered arrival distribution
    dist = distribution.InterpolatedDistribution.linear(
        list(zip(list(range(len(arrival_distribution))), arrival_distribution)), None)

    # Calculate position of each time step at arrival distribution
    corr_position = time_stamp_to_hours(time_steps)

    # Get arrival probablity for each time step of the simulation
    arrival_probability = []
    for pos in corr_position:
        arrival_probability.append(dist[pos])
    # Normalize probability
    cumsum = sum(arrival_probability)
    arrival_probability = [x / cumsum for x in arrival_probability]

    # Get on average num_charging_events arrivals per week
    period = time_steps[-1] - time_steps[0]
    num_weeks = period.total_seconds() / 7 / 24 / 3600
    arrivals = []
    corr_times = np.random.choice(corr_position, p=arrival_probability,
                                  size=math.ceil(num_charging_events * num_weeks))
    for corr_time in corr_times:
        arrivals.append(time_steps[corr_position.index(corr_time)])

    return sorted(arrivals)


def simulate(config):
    """Iterates over time and simulates the infrastructure.

    Args:
        config (:obj: `ElvisConfig`): User input.
    """
    start_date = config.start_date
    end_date = config.end_date
    resolution = config.resolution

    # Create list containing all time steps as datetime object
    time_step = start_date
    time_steps = []
    while time_step <= end_date:
        time_steps.append(time_step)
        time_step += resolution

    arrivals = create_vehicle_arrivals(config, time_steps)
    print(arrivals)


class TestConfig:
    def __init__(self):
        self.start_date = datetime.datetime(2020, 1, 1, 22)
        self.end_date = datetime.datetime(2020, 1, 18, 1, 15)
        self.resolution = datetime.timedelta(minutes=30)

        self.num_charging_events = 5

        self.arrival_distribution = [0 for x in range(168)] #[np.random.uniform(0, 1) for x in range(168)]
        self.arrival_distribution[8] = 1
        self.charging_events = 2


if __name__ == '__main__':
    conf = TestConfig()
    simulate(conf)
