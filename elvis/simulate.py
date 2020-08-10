import datetime
import math
import numpy as np

import distribution


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
    charging_events = config.charging_events

    # Rearrange arrival distribution so it starts with first hour of simulation time
    start = time_steps[0]
    beginning_hour = start.weekday() * 24 + start.hour
    arrival_distribution = (arrival_distribution[beginning_hour:] +
                            arrival_distribution[:beginning_hour])

    # Calculate position of each time step at arrival distribution
    offset = start + datetime.timedelta(minutes=start.minute)
    corr_position = [(x - offset) / datetime.timedelta(weeks=1) for x in time_steps]
    weeks = math.ceil(corr_position[-1])

    # Create distribution based on reordered arrival distribution
    dist = distribution.InterpolatedDistribution.linear(
        list(zip(list(range(len(arrival_distribution))), arrival_distribution)) * weeks, None)

    # Get arrival probablity for each time step of the simulation
    arrival_probability = []
    for pos in corr_position:
        arrival_probability.append(dist[pos])
    cumsum = sum(arrival_probability)
    arrival_probability = [x / cumsum for x in arrival_probability]

    # Get on average charging_events arrivals per week

    np.random.seed(4)
    arrivals = []
    corr_times = np.random.choice(corr_position, p=arrival_probability,
                                  size=math.ceil(charging_events * corr_position[-1]))
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
        self.resolution = datetime.timedelta(minutes=45)

        self.charging_events = 5

        self.arrival_distribution = [np.random.uniform(0, 1) for x in range(168)]
        self.arrival_distribution.sort()
        self.charging_events = 2


if __name__ == '__main__':
    conf = TestConfig()
    simulate(conf)
