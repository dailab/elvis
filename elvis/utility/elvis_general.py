"""Methods that are elvis related and used in multiple times inside elvis."""

import datetime
import math
import pandas as pd

from elvis.distribution import EquallySpacedInterpolatedDistribution


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


def num_time_steps(start_date, end_date, resolution):
    """Returns the number of time steps given a period described by its start and end date
    and the resolution.

    Args:
        start_date: (:obj: `datetime.datetime`): First time stamp.
        end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
        resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

    Returns:
        num_time_steps: (int): Number of time steps to be simulated.
    """

    return int((end_date - start_date) / resolution) + 1


def transform_data(input_df, resolution, start_date, end_date):
    assert len(input_df) >= 2, "must provide more than two datapoints"
    assert resolution.seconds >= 60, "resolutions lower than one minute not supported"

    # convert to a list of dates and corresponding values
    if isinstance(input_df, pd.DataFrame):
        input_data = []
        for idx, value in input_df.iteritems():
            input_data.append((idx, value))
    else:
        assert isinstance(input_df, list), "input must be list or pandas.DataFrame"
        input_data = input_df

    # get resolution and time frame of input data
    input_start_date = input_data[0][0]
    input_resolution = input_data[1][0] - input_start_date
    input_resolution_seconds = input_resolution.seconds

    # linearly interpolate missing values in input data
    interp_input_data = [input_data[0], input_data[1]]
    for i in range(2, len(input_data)):
        prev = input_data[i - 1]
        curr = input_data[i]
        dist = curr[0] - prev[0]

        # distance between data points is equal to resolution
        if dist == input_resolution:
            interp_input_data.append(curr)
            continue

        # check if distance is evenly divisible by resolution
        rem = dist.seconds % input_resolution_seconds
        if rem != 0:
            raise Exception("inconsistent distance between data points")

        steps = math.floor(dist.seconds / input_resolution_seconds)
        if steps > 0:
            step = (curr[1] - prev[1]) / steps

            for j in range(1, steps):
                interp_input_data.append((prev[0] + (j * input_resolution), prev[1] + (j * step)))

        interp_input_data.append(curr)

    # transform input data to minute resolution
    input_data_minute_res = []

    if input_resolution_seconds > 60:
        # interpolate datapoints to get minute resolution
        interp_steps = math.floor(input_resolution_seconds / 60)
        minute_res = datetime.timedelta(seconds=60)

        for j in range(1, len(interp_input_data)):
            prev = interp_input_data[j - 1][1]
            curr = interp_input_data[j][1]
            step = (curr - prev) / interp_steps

            input_data_minute_res.append(interp_input_data[j - 1])
            for k in range(1, interp_steps):
                input_data_minute_res.append(
                    (interp_input_data[j - 1][0] + (k * minute_res), prev + (k * step)))

    elif input_resolution_seconds < 60:
        # take the average of datapoints within a minute
        curr_sum = interp_input_data[0][1]
        curr_cnt = 1

        curr_date = input_start_date
        curr_start_date = curr_date

        for j in range(1, len(interp_input_data)):
            next_date = interp_input_data[j][0]

            # check if we're at the next minute
            if next_date.minute != curr_date.minute:
                input_data_minute_res.append((curr_start_date, curr_sum / curr_cnt))
                curr_sum = 0
                curr_cnt = 0
                curr_start_date = next_date

            curr_sum += interp_input_data[j][1]
            curr_cnt += 1
            curr_date = next_date

        if curr_sum > 0:
            input_data_minute_res.append((curr_start_date, curr_sum / curr_cnt))
    else:
        input_data_minute_res = interp_input_data

    # now calculate averages for every unique (weekday, month) pair that we have available
    available_datapoints = dict()
    for date, value in input_data_minute_res:
        weekday = date.weekday()
        month = date.month
        key = (weekday, month)

        if key not in available_datapoints:
            available_datapoints[key] = (
                [0 for _ in range(0, 24 * 60)], [0 for _ in range(0, 24 * 60)])

        minute_of_day = date.hour * 60 + date.minute
        available_datapoints[key][0][minute_of_day] += value
        available_datapoints[key][1][minute_of_day] += 1

    for value in available_datapoints.values():
        for j in range(0, len(value[0])):
            if value[1][j] <= 1:
                continue

            value[0][j] /= value[1][j]

    # uncomment to export data for all (weekday, month) pairs
    # for key, value in available_datapoints.items():
    #    export_csv(value[0], "./input_data_averaged/" + str(key[0]) + "_" + str(key[1]) + ".csv")

    # build the result by finding the closest (weekday, month) pair for every required day
    result_data = []

    curr_date = start_date
    curr_day_data = None
    prev_weekday = None

    while curr_date < end_date:
        curr_weekday = curr_date.weekday()
        if prev_weekday is None or curr_weekday != prev_weekday:
            curr_month = curr_date.month
            prev_weekday = curr_weekday

            if (curr_weekday, curr_month) in available_datapoints:
                # use the available data for the day
                curr_day_data = available_datapoints[(curr_weekday, curr_month)]
            else:
                # find the closest available data point
                min_dist = math.inf
                for key, value in available_datapoints.items():
                    dist = abs(key[0] - curr_weekday) + abs(key[1] - curr_month)
                    if dist >= min_dist:
                        continue

                    min_dist = dist
                    curr_day_data = value

        minute_of_day = curr_date.hour * 60 + curr_date.minute
        result_data.append((curr_date, curr_day_data[0][minute_of_day]))

        curr_date += resolution

    return result_data


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


def floor(value, decimals=3):
    """Floors a value to 3 decimals."""

    assert isinstance(decimals, int), 'Decimals must be of type int'

    coeff = 10**decimals
    value = math.floor(value * coeff) / coeff

    return value
