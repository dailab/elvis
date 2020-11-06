"""Methods that are elvis related and used in multiple times inside elvis."""


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

