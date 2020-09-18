"""Used to generate charging events based on distributions or datapoints
of measured charging events.

TODO:
    - Ensure other than hourly distributions work
    - Add parking time, car_type, arrival_soc, target_soc
    - Enable conversion of measured charging events to
    synthetic charging events
    - Catch and prevent errors, add raised to docstrings
"""
import math
import datetime
import numpy as np

import distribution
import charging_event


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
        hour = delta.days * 24 + delta.seconds / 3600 + delta.microseconds / 3600 / 1000 / 1000
        # add offset
        hour += start.minute / 60 + start.second / 3600 + start.microsecond / 3600 / 1000 / 1000
        hours_passed.append(hour)
    return hours_passed


def hours_to_time_stamps(hours, start):
    """Converts hour stamps to time stamps. Hour stamps measuring the time
        passed sinde the beginning of the first time stamp.

    Args:
          hours (list): Containing the hours to convert.
          start (:obj: `datetime.datetime`): First time stamp.

    Returns:
        list: Time stamps.
    """
    # Define the corresponding time stamp to hour = 0.
    # Hour = 0 is the beginning of the hour of the first time stamp.
    hour0_corr = datetime.datetime(start.year, start.month, start.day, start.hour)

    time_stamps = []
    for hour in hours:
        time_stamps.append(hour0_corr + datetime.timedelta(hours=hour))

    return time_stamps


def align_distribution(distr, first_time_stamp, last_time_stamp):
    """Receives weekly distribution in hourly resolution besides a starting and an
    ending time_stamp. Shifts and multiplies distribution to allign it to the
     period of the time_stamps.

    Args:
        distr (list): Containing hourly probabilities.
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
        config (:obj: `distribution`): Represents the arrival distribution.
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
    arrival_distribution = align_distribution(arrival_distribution, time_steps[0], time_steps[-1])

    # Create distribution based on reordered arrival distribution
    dist = distribution.EquallySpacedInterpolatedDistribution.linear(
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
    corr_times = np.random.choice(corr_position, p=arrival_probability,
                                  size=math.ceil(num_charging_events * num_weeks))

    # Convert hours back to time_stamps
    arrivals = hours_to_time_stamps(corr_times, time_steps[0])

    return sorted(arrivals)


def create_charging_events(config, time_steps):
    """Create all charging events for the simulation period.

    Args:
        config (:obj: `distribution`): Represents the arrival distribution.
        time_steps (list): List containing all time steps as :obj: `datetime.datetime` object.

    Returns:
        (list): containing instances of `ChargingEvent`.

    """
    arrivals = create_vehicle_arrivals(config, time_steps)

    charging_events = []
    for arrival in arrivals:
        charging_events.append(charging_event.ChargingEvent(arrival))

    return charging_events
