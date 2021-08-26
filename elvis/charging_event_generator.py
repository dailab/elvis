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

from elvis.utility.walker import WalkerRandomSampling
from sklearn.mixture import GaussianMixture


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


def create_charging_events_from_weekly_distribution(
        arrival_distribution, time_steps, num_charging_events, mean_park, std_deviation_park,
        mean_soc, std_deviation_soc, vehicle_types, max_parking_time):

    """Create all charging events for the simulation period.

    Args:
        arrival_distribution: (list): Containing hourly data for the arrival probabilities for one
        week.
        time_steps: (list): Contains time_steps in `datetime.datetime` format
        num_charging_events: (int): Number of charging events to be generated.
        mean_park: (float): Mean of the gaussian distribution the parking time is generated from.
        std_deviation_park: (float): Standard deviation of the gaussian distribution the parking
            time is generated from.
        mean_park: (float): Mean of the gaussian distribution the SOC is generated from.
        std_deviation_park: (float): Standard deviation of the gaussian distribution the SOC
            is generated from.
        mean_soc: (float): Limits: [0, 1]. State of charge of the cars when arriving on average.
        std_deviation_soc: (float): Standard deviation of the arrival SOC.
        vehicle_types: (list): Containing all instances of :obj: `elvis.vehicle.ElectricVehicle`
        max_parking_time: (float): Maximum time a car is allowed to stay at the charging
            infrastructure in hours.

    Returns:
        (list): containing num_charging_events instances of `ChargingEvent`.

    """
    msg_no_vehicles = 'At least one vehicle type is necessary to generate charging events.'
    assert len(vehicle_types) > 0, msg_no_vehicles

    arrivals = create_vehicle_arrivals(arrival_distribution, num_charging_events, time_steps)
    weights = [vehicle_type.probability for vehicle_type in vehicle_types]

    walker = WalkerRandomSampling(weights, keys=vehicle_types)

    charging_events = []
    parking_time_samples = np.random.normal(mean_park, std_deviation_park, len(arrivals)).tolist()
    soc_samples = np.random.normal(mean_soc, std_deviation_soc, len(arrivals)).tolist()
    vehicle_type_samples = walker.random(count=len(arrivals)).tolist()
    for arrival in arrivals:
        parking_time = min(max(0, parking_time_samples.pop()), max_parking_time)
        soc = min(max(0, soc_samples.pop()), 1)
        vehicle_type = vehicle_type_samples.pop()
        charging_events.append(charging_event.ChargingEvent(arrival, parking_time, soc,
                                                            vehicle_type))

    return charging_events


def init_gmm(means, weights, covariances):
    """
        Initialise the GMM.

    Args:
        means: (list): Mean value for each mixture component.
        weights: (list): Mixing weights for each mixture component.
        covariances: (list): Covariance for mixture component. In the used scikit-learn model
            a covariance_type of "full" is used.

    Returns:
        gmm: (:obj:): Scikit-learn gaussian mixture model.
    """

    assert 0.99 < sum(weights) < 1.01, 'GMM weights must add up to 1 (1 % tolerance)'
    assert len(weights) == len(means) == len(covariances), 'Parameters for GMM must be of same ' \
                                                           'length'
    assert all(0 < x[0] < 168 for x in means), 'The first dimension of the means is expected to ' \
                                               'be the arrival time in hours counting from ' \
                                               'Monday 0:00. Values should therefore be >0 and <168'

    # 2 dimensions: arrival time, parking time -> 2x2 covariance matrices
    for i in covariances:
        for j in i:
            assert len(i) == len(j) == 2, 'GMM covariances must be quadratic with 2 rows and 2 cols'

    # numpy arrays of parameters
    means_np = np.asarray(means)
    weights_np = np.asarray(weights)
    covariances_np = np.asarray(covariances)

    # scikit-learn GMM
    gmm = GaussianMixture()

    # initialise parameters
    gmm.means_ = means_np
    gmm.weights_ = weights_np
    gmm.covariances_ = covariances_np

    return gmm


def weeks_to_sample(time_steps):
    """
    Calculates the weeks to sample for a GMM model based on the time steps of the simulation.

    Args:
        time_steps: (list): Contains time_steps in `datetime.datetime` format

    Returns:
        num_weeks: (int): # weeks to sample
    """
    # Total duration of simulation period in hours
    last = time_steps[-1]
    first = time_steps[0]
    total_hours = (last - first).total_seconds() / 3600

    num_weeks = math.ceil(total_hours / 168)

    # If the first time stamp is later in the week add one week to sample
    if first.weekday() > last.weekday():
        num_weeks += 1
    elif first.weekday() == last.weekday():
        if first.time() > last.time():
            num_weeks += 1

    return num_weeks


def reset_offset_hours(samples, cut_off_hour):
    assert isinstance(samples, np.ndarray)
    for sample in samples:
        time = sample[0]
        for i in range(7):
            if (i + 1) * 24 > time > ((i + 1) * 24 - cut_off_hour):
                time -= 24 - cut_off_hour
                sample[0] = time
                break
            elif (i + 1) * 24 > time < ((i + 1) * 24 - cut_off_hour):
                time += cut_off_hour
                sample[0] = time
                break

    return samples

def resample(gmm, min_parking_time, num_resamples, hour_offset=0):
    """If a sample is out of accepted range resample until a valid sample is found.

    Args:
        gmm: (:obj:): scikit-learn gaussian mixture model
        min_parking_time: (float): Parking time that is required as a minimum
        num_resamples: (int): Number of resamples to create
        hour_offset: (float): Used in case an offset of hours within the gmm model is used.
    Returns:
        sample: Sample of the gaussian mixture model
        """
    assert isinstance(num_resamples, int)
    parking_time = 0
    resamples, _ = gmm.sample(num_resamples)
    resamples = reset_offset_hours(resamples, hour_offset)
    resamples = resamples.tolist()

    to_delete = []
    for i in range(len(resamples)):
        sample = resamples[i]
        if sample[1] < min_parking_time:
            to_delete.append(i)

    to_delete.sort(reverse=True)

    for i in to_delete:
        del resamples[i]

    return resamples


def create_charging_events_from_gmm(time_steps, num_charging_events, means, weights,
                                    covariances, vehicle_types, max_parking_time, mean_soc,
                                    std_deviation_soc):
    """

    Args:
        time_steps: (list): Contains time_steps in `datetime.datetime` format
        num_charging_events: (int): Number of charging events to be generated.
        means: (list): Mean value for each mixture component.
        weights: (list): Mixing weights for each mixture component.
        covariances: (list): Covariance for mixture component. In the used scikit-learn model
            a covariance_type of "full" is used.
        vehicle_types:  (list): Containing all instances of :obj: `elvis.vehicle.ElectricVehicle`
        max_parking_time: (float): Maximum time a car is allowed to stay at the charging
            infrastructure in hours.
        mean_soc: (float): Limits: [0, 1]. State of charge of the cars when arriving on average.
        std_deviation_soc: (float): Standard deviation of the arrival SOC.

    Returns:
        (list): containing num_charging_events instances of `ChargingEvent`.
    """

    gmm = init_gmm(means, weights, covariances)

    num_weeks = weeks_to_sample(time_steps)

    week_offset = 0
    samples = []
    rounding_const = 1/((time_steps[1] - time_steps[0]).total_seconds() / 3600)
    min_parking_time = 0.167
    num_resamples = 100
    resamples = resample(gmm, min_parking_time, num_resamples, hour_offset=5)
    resample_counter = 0

    while num_weeks > week_offset / 168:
        temp, _ = gmm.sample(num_charging_events)
        temp = reset_offset_hours(temp, 5)
        temp = temp.tolist()
        for sample in temp:
            if sample[1] < min_parking_time:  # parking time < 1 min
                sample = resamples[resample_counter]
                resample_counter += 1
                if resample_counter == len(resamples):
                    resamples = resample(gmm, min_parking_time, num_resamples, hour_offset=5)
                    resample_counter = 0

            sample[0] += week_offset
            # to ensure arrivals fall on time stamps
            sample[0] = math.ceil(sample[0] * rounding_const) / rounding_const
            samples.append(sample)
        week_offset += 168

    samples.sort()
    # hours from monday of the first week until the beginning of the simulation
    day_offset = time_steps[0].weekday() * 24
    first_step_hours = day_offset + time_steps[0].hour + time_steps[0].minute / 60 + \
                       time_steps[0].second / 60 / 60
    # Remove samples before first simulation step
    # Ensure stop is < first_step_hours for initialisation
    stop = first_step_hours - 1
    i = 0
    while stop < first_step_hours:
        stop = samples[i][0]
        i += 1
    # Discard all samples before first time stamp
    samples = samples[i-1:]

    # simulation duration in hours
    sim_dur_hours = (time_steps[-1] - time_steps[0]).total_seconds() / 3600
    i = 0
    # ensure initial stop > sim_dur_hours
    stop = sim_dur_hours + 1
    while stop >= sim_dur_hours:
        i += 1
        stop = samples[-(i-1)][0]
    # discard all charging events after simulation period
    if i > 1:
        samples = samples[:-(i-1)]

    # transform arrival time in hours into datetime.datetime object
    # initialise reference point Monday 0:00 of first simulation week
    ref_date = time_steps[0] - datetime.timedelta(hours=first_step_hours)
    for sample in samples:
        sample_hour = sample[0]
        sample[0] = ref_date + datetime.timedelta(hours=sample_hour)
        # ensure 1 min < parking time < max_parking_time
        sample[1] = min(sample[1], max_parking_time)

    walker_weights = [vehicle_type.probability for vehicle_type in vehicle_types]
    walker = WalkerRandomSampling(walker_weights, keys=vehicle_types)

    charging_events = []
    soc_samples = np.random.normal(mean_soc, std_deviation_soc, len(samples)).tolist()
    vehicle_type_samples = walker.random(count=len(samples)).tolist()
    for sample in samples:
        soc = min(max(0, soc_samples.pop()), 1)
        vehicle_type = vehicle_type_samples.pop()
        charging_events.append(charging_event.ChargingEvent(sample[0], sample[1], soc,
                                                            vehicle_type))

    return charging_events
