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

import elvis.distribution as distribution
import elvis.charging_event as charging_event


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
        aligned_distribution: (list): Containing the probabilities alligned to period.
        difference: Difference between first used 'time stamp' of the distribution and first
            time stamp of the simulation in hours.
    """
    hours = first_time_stamp.weekday() * 24 + first_time_stamp.hour
    minutes = first_time_stamp.minute
    seconds = first_time_stamp.second
    microseconds = first_time_stamp.microsecond

    offset = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds,
                                microseconds=microseconds)

    seconds_per_week = 7 * 24 * 3600
    num_values = len(distr)
    seconds_per_value = seconds_per_week/num_values

    starting_pos = math.floor(offset.total_seconds()/seconds_per_value)
    difference = (offset.total_seconds()/seconds_per_value - starting_pos) / 3600


    period = last_time_stamp - first_time_stamp
    # Upward estimate of the needed length of the distribution
    total_weeks = math.ceil(period.total_seconds() / seconds_per_week)

    aligned_distribution = distr[starting_pos:] + distr * total_weeks
    return aligned_distribution, difference


def create_vehicle_arrivals(arrival_distribution, num_charging_events, time_steps):
    """Creates vehicle arrival times.

    Args:
        arrival_distribution (list): Containing hourly arrival probabilities for one week.
        num_charging_events: (int): Number of charging events per week.
        time_steps (list): List containing all time steps as :obj: `datetime.datetime` object.

    Returns:
        list: Arrival times.

    ToDo:
        seeding seems to not work properly. With fixed seed small changes are still there,
        changing the seed has a huge impact though.
    """

    coefficient = 168 / len(arrival_distribution)

    # Rearrange arrival distribution so it starts with first hour of simulation time
    arrival_distribution, difference = align_distribution(arrival_distribution, time_steps[0],
                                                          time_steps[-1])

    # generate x-values (hours away from first time step) of the distribution
    hour_stamps = [x * coefficient - difference for x in range(len(arrival_distribution))]
    # Create distribution based on reordered arrival distribution
    dist = distribution.EquallySpacedInterpolatedDistribution.linear(
        list(zip(hour_stamps, arrival_distribution)), None)

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


def create_time_steps(start_date, end_date, resolution):
    """Create list from start, end date and resolution of the simulation period with all individual
    time steps.

    Args:
        start_date: (:obj: `datetime.datetime`): First time stamp.
        end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
        resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

    Returns:
        time_steps: (list): Contains time_steps in `datetime.datetime` format

    """
    # Create list containing all time steps as datetime.datetime object
    time_step = start_date
    time_steps = []
    while time_step <= end_date:
        time_steps.append(time_step)
        time_step += resolution

    return time_steps


def create_charging_events_from_distribution(arrival_distribution, time_steps, num_charging_events):
    """Create all charging events for the simulation period.

    Args:
        arrival_distribution: (list): Containing hourly data for the arrival probabilities for one
        week.
        time_steps: (list): Contains time_steps in `datetime.datetime` format
        num_charging_events: (int): Number of charging events to be generated.

    Returns:
        (list): containing num_charging_events instances of `ChargingEvent`.

    """

    arrivals = create_vehicle_arrivals(arrival_distribution, num_charging_events, time_steps)

    charging_events = []
    for arrival in arrivals:
        charging_events.append(charging_event.ChargingEvent(arrival))

    return charging_events