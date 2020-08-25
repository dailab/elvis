"""Simulation of the behavior of the charging infrastructure.

TODO:
- Should the waiting queue rather be a public variable instead of always passing
    and returning it from function to function?
- Faster way to find available conneciton_points necessary? Currently loop over all until one
     that is available is found."""

import datetime
import queue
import logging

from elvis.charging_event_generator import create_charging_events
from elvis.set_up_infrastructure import set_up_charging_points


def set_up_time_steps(config):
    """Create list from start, end date and resolution of the simulation period with all individual
    time steps.

    Args:
        config: (:obj: `config`): Configuration class containing the time/date parameters

    Returns:
        time_steps: (list): Contains time_steps in `datetime.datetime` format

    """
    start_date = config.start_date
    end_date = config.end_date
    resolution = config.resolution

    # Create list containing all time steps as datetime.datetime object
    time_step = start_date
    time_steps = []
    while time_step <= end_date:
        time_steps.append(time_step)
        time_step += resolution

    return time_steps


def handle_car_arrival(free_connection_points, busy_connection_points, event, waiting_queue):
    """Connects car to charging point, to the queue or send it off.

    Args:
        free_connection_points: (set): Containing all :obj: `connection_points.ConnectionPoint`
            of the infrastructure that are currently available.
        busy_connection_points: (set): Containing all :obj: `connection_points.ConnectionPoint`
            of the infrastructure that are currently busy.
        event: (:obj: `charging_event.ChargingEvent`): Arriving charging event.
        waiting_queue: (:obj: `queue.Queue`): Containing the waiting vehicles
    """

    # connect the arrival to an available connection point if possible
    if len(free_connection_points) > 0:
        # Get random free connection point and remove it from set
        connection_point = free_connection_points.pop()
        connection_point.connect_vehicle(event)
        logging.info(' Connect: %s', connection_point)
        # Put connection point to busy set
        busy_connection_points.add(connection_point)
        return waiting_queue

    # if no free connection point available put arrival to queue
    # if not full and queue is considered in simulation (maxsize > 0)
    if not waiting_queue.size() == waiting_queue.maxsize and waiting_queue.maxsize > 0:
        waiting_queue.enqueue(event)
        logging.info(' Put %s to queue.', event)
    else:
        logging.info(' Queue is full -> Reject: %s', event)
    return waiting_queue


def update_queue(waiting_queue, current_time_step, by_time):
    """Removes cars that have spent their total parking time in the waiting queue and
        therefore must leave.

    Args:
        waiting_queue: (:obj: `queue.Queue`): Charging events waiting for available
        connection point.
        current_time_step (:obj: `datetime.datetime`): current time step of the simulation.
        by_time: (bool): True if cars shall be disconnected with respect to their parking time.
        False if cars shall be disconnected due to their SOC target.

    Returns:
        updated_queue: (:obj: `queue.Queue`): Queue with removed cars that are overdue.
    """

    if by_time is True and current_time_step >= waiting_queue.next_leave:
        to_delete = []
        for i in range(waiting_queue.size()):
            event = waiting_queue.queue[i]
            arrival_time = event.arrival_time
            parking_time = datetime.timedelta(hours=event.parking_time)

            # If waiting time is not longer than parking time remain in queue
            if arrival_time + parking_time <= current_time_step:
                to_delete.insert(0, i)

        if len(to_delete) > 0:
            for i in to_delete:
                logging.info(' Remove: %s from queue.', waiting_queue.queue.pop(i))

        waiting_queue.get_next_leaving_time()


def update_charging_points(free_connection_points, busy_connection_points,
                           waiting_queue, current_time_step, by_time):
    """Removes cars due to their parking time or their SOC limit and updates the connection points
    respectively.

    Args:
        free_connection_points: (set): Containing all :obj: `connection_points.ConnectionPoint`
            of the infrastructure that are currently available.
        busy_connection_points: (set): Containing all :obj: `connection_points.ConnectionPoint`
            of the infrastructure that are currently busy.
        waiting_queue: (:obj: `queue.Queue`): waiting vehicles/charging events.
        current_time_step: (:obj: `datetime.datetime`): current time step.
        by_time: (bool): Configuration class instance.
    """
    # if parking time is overdue: disconnect vehicle
    if by_time is True:
        for connection_point in busy_connection_points.copy():
            connected_vehicle = connection_point.connected_vehicle

            arrival_time = connected_vehicle['arrival_time']
            parking_time = datetime.timedelta(hours=connected_vehicle['parking_time'])

            if arrival_time + parking_time <= current_time_step:
                logging.info(' Disconnect: %s', connection_point)
                connection_point.disconnect_vehicle()
                # Put connection point from busy list to available list
                free_connection_points.add(connection_point)
                busy_connection_points.remove(connection_point)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    connection_point.connect_vehicle(waiting_queue.dequeue())
                    # Put connection point from available to busy
                    busy_connection_points.add(connection_point)
                    free_connection_points.remove(connection_point)

                    logging.info(' Connect: %s from queue.', connection_point)

    # if SOC limit is reached: disconnect vehicle
    # TODO: Test once power assignment is done.
    else:
        for connection_point in busy_connection_points.copy():
            connected_vehicle = connection_point.connected_vehicle

            soc = connected_vehicle.soc
            soc_target = connected_vehicle.soc_target

            if soc >= soc_target:
                logging.info(' Disconnect: %s', connection_point)
                connection_point.disconnect_vehicle()

                # Put connection point from busy list to available list
                free_connection_points.add(connection_point)
                busy_connection_points.remove(connection_point)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    connection_point.connect_vehicle(waiting_queue.dequeue())
                    logging.info(' Connect: %s from queue.', connection_point)

                    # Put connection point from available to busy
                    busy_connection_points.add(connection_point)
                    free_connection_points.remove(connection_point)


def simulate(config):
    """Main simulation loop.
    Iterates over simulation period and simulates the infrastructure.

    Args:
        config (:obj: `ElvisConfig`): User input.
    """
    # empty log file
    with open('log.log', 'w'):
        pass
    logging.basicConfig(filename='log.log', level=logging.INFO)
    # get list with all time_steps as datetime.datetime
    time_steps = set_up_time_steps(config)
    # create arrival times as sorted list of datetime.datetime
    charging_events = create_charging_events(config, time_steps)
    # Initialize waiting queue for cars at the infrastructure
    waiting_queue = queue.Queue(maxsize=config.queue_length)
    # set up charging points and their connection points
    charging_points = set_up_charging_points(config.charging_points)
    # Put all connection points (all available in the beginning) to list
    free_connection_points = set()
    for charging_point in charging_points:
        for connection_point in charging_point.connection_points:
            free_connection_points.add(connection_point)

    busy_connection_points = set()

    # loop over every time step
    for time_step in time_steps:
        logging.info(' %s', time_step)
        # check if cars must be disconnected, if yes immediately connect car from queue if possible
        update_queue(waiting_queue, time_step, config.disconnect_by_time)

        update_charging_points(free_connection_points, busy_connection_points, waiting_queue,
                               time_step, config.disconnect_by_time)

        # in case of multiple charging events in the same time step: handle one after the other
        while len(charging_events) > 0 and time_step == charging_events[0].arrival_time:
            waiting_queue = handle_car_arrival(free_connection_points, busy_connection_points,
                                               charging_events[0], waiting_queue)
            # remove the arrival from the list
            charging_events = charging_events[1:]

    # TODO: assign power to every component


class TestConfig:
    def __init__(self):
        self.start_date = datetime.datetime(2020, 1, 1)
        self.end_date = datetime.datetime(2020, 1, 7, 23, 59)
        self.resolution = datetime.timedelta(minutes=60)

        self.num_charging_events = 5

        self.arrival_distribution = [0 for x in range(168)] #[np.random.uniform(0, 1) for x in range(168)]
        self.arrival_distribution[8] = 1
        self.arrival_distribution[10] = 1
        self.charging_events = 2
        self.queue_length = 2
        self.charging_points = [1, 1]
        self.disconnect_by_time = True


if __name__ == '__main__':
    conf = TestConfig()
    simulate(conf)
