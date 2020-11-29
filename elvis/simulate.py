"""Simulation of the behavior of the charging infrastructure.

- TODO: What if connection points/charging points are not type manual but type automated."""

import datetime
import logging

from elvis.utility.elvis_general import create_time_steps
from elvis.set_up_infrastructure import set_up_infrastructure
from elvis.sched.schedulers import Uncontrolled, FCFS
from elvis.waiting_queue import WaitingQueue
from elvis.result import ElvisResult
from elvis.config import ScenarioRealisation, ScenarioConfig


def handle_car_arrival(free_cps, busy_cps, event, waiting_queue):
    """Connects car to charging point, to the queue or send it off.

    Args:
        free_cps: (set): Containing all :obj: `charging_poitns.ChargingPoint`
            of the infrastructure that are currently available.
        busy_cps: (set): Containing all :obj: `charging_poitns.ChargingPoint`
            of the infrastructure that are currently busy.
        event: (:obj: `charging_event.ChargingEvent`): Arriving charging event.
        waiting_queue: (:obj: `queue.WaitingQueue`): Containing the waiting vehicles
    """

    # connect the arrival to an available charging point if possible
    if len(free_cps) > 0:
        # Get random free charging point and remove it from set
        cp = free_cps.pop()
        cp.connect_vehicle(event)
        logging.info(' Connect: %s', cp)
        # Put charging point to busy set
        busy_cps.add(cp)
        return waiting_queue

    # if no free charging point available put arrival to queue
    # if not full and queue is considered in simulation (maxsize > 0)
    if not waiting_queue.size() == waiting_queue.maxsize and waiting_queue.maxsize > 0:
        waiting_queue.enqueue(event)
        logging.info(' Put %s to queue.', event)
    else:
        logging.info(' WaitingQueue is full -> Reject: %s', event)
    return waiting_queue


def update_queue(waiting_queue, current_time_step, by_time):
    """Removes cars that have spent their total parking time in the waiting queue and
        therefore must leave.

    Args:
        waiting_queue: (:obj: `queue.WaitingQueue`): Charging events waiting for available
        charging point.
        current_time_step (:obj: `datetime.datetime`): current time step of the simulation.
        by_time: (bool): True if cars shall be disconnected with respect to their parking time.
        False if cars shall be disconnected due to their SOC target.

    Returns:
        updated_queue: (:obj: `queue.WaitingQueue`): WaitingQueue without removed cars
            that are overdue.
    """

    if by_time is True and current_time_step >= waiting_queue.next_leave:
        to_delete = []
        for i in range(waiting_queue.size()):
            event = waiting_queue.queue[i]

            # If waiting time is not longer than parking time remain in queue
            if event.leaving_time <= current_time_step:
                to_delete.insert(0, i)

        if len(to_delete) > 0:
            for i in to_delete:
                logging.info(' Remove: %s from queue.', waiting_queue.queue.pop(i))

        waiting_queue.determine_next_leaving_time()


def update_cps(free_cps, busy_cps,
               waiting_queue, current_time_step, by_time):
    """Removes cars due to their parking time or their SOC limit and updates the charging points
    respectively.

    Args:
        free_cps: (set): Containing all :obj: `charging_point.ChargingPoint`
            of the infrastructure that are currently available.
        busy_cps: (set): Containing all :obj: `charging_point.ChargingPoint`
            of the infrastructure that are currently busy.
        waiting_queue: (:obj: `queue.WaitingQueue`): waiting vehicles/charging events.
        current_time_step: (:obj: `datetime.datetime`): current time step.
        by_time: (bool): Configuration class instance.
    """
    # if parking time is overdue: disconnect vehicle
    if by_time is True:
        for cp in busy_cps.copy():
            connected_vehicle = cp.connected_vehicle

            if connected_vehicle['leaving_time'] <= current_time_step:
                logging.info(' Disconnect: %s', cp)
                cp.disconnect_vehicle()
                # Put charging point from busy list to available list
                free_cps.add(cp)
                busy_cps.remove(cp)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    cp.connect_vehicle(waiting_queue.dequeue())
                    # Put charging point from available to busy
                    busy_cps.add(cp)
                    free_cps.remove(cp)

                    logging.info(' Connect: %s from queue.', cp)

    # if SOC limit is reached: disconnect vehicle
    # TODO: Test once power assignment is done.
    else:
        for cp in busy_cps.copy():
            connected_vehicle = cp.connected_vehicle

            soc = connected_vehicle['soc']
            soc_target = connected_vehicle['soc_target']

            if soc >= soc_target:
                logging.info(' Disconnect: %s', cp)
                cp.disconnect_vehicle()

                # Put charging point from busy list to available list
                free_cps.add(cp)
                busy_cps.remove(cp)

                # immediately connect next waiting car
                if waiting_queue.size() > 0:
                    cp.connect_vehicle(waiting_queue.dequeue())
                    logging.info(' Connect: %s from queue.', cp)

                    # Put charging point from available to busy
                    busy_cps.add(cp)
                    free_cps.remove(cp)


def charge_connected_vehicles(assign_power, busy_cps, res):
    """Change SOC of connected vehicles based on power assigned by scheduling policy.

    Args:
        assign_power: (dict): keys=charging points, values=power to be assigned.
        busy_cps: list of all charging points that currently have a connected
            vehicle.
        res: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

    Returns: None
    """

    for cp in busy_cps:
        power = assign_power[cp]
        vehicle = cp.connected_vehicle
        soc_before = vehicle['soc']
        if vehicle is None:
            raise TypeError

        cp.charge_vehicle(power, res)
        logging.info('At charging point %s the vehicle SOC has been charged from %s to %s. '
                     'The power assigned is: %s', cp, soc_before, vehicle['soc'],
                     str(power))


def simulate(scenario, start_date=None, end_date=None, resolution=None, realisation_file_name=None):
    """Main simulation loop.
    Iterates over simulation period and simulates the infrastructure.

    Args:
        scenario: (:obj: `elvis.scenario.ScenarioRealisation`): Scenario to be simulated.
        start_date: (:obj: `datetime.datetime`): First time stamp.
        end_date: (:obj: `datetime.datetime`): Upper bound for time stamps.
        resolution: (:obj: `datetime.timedelta`): Time in between two adjacent time stamps.

    Returns:
        result: (:obj: `elvis.result.ElvisResult`): Contains the results of the simulation.
    """
    # ---------------------Initialisation---------------------------
    # if input is instance of ScenarioConfig transform to ScenarioRealisation

    if isinstance(scenario, ScenarioConfig):
        scenario = scenario.create_realisation(start_date, end_date, resolution)

    assert isinstance(scenario, ScenarioRealisation), 'Realisation must be of type ' \
                                                      'ScenarioRealisation or ScenarioConfig.'

    # empty log file
    with open('log.log', 'w'):
        pass
    logging.basicConfig(filename='log.log', level=logging.INFO)
    # get list with all time_steps as datetime.datetime
    time_steps = create_time_steps(scenario.start_date, scenario.end_date, scenario.resolution)
    # Initialize waiting queue for cars at the infrastructure
    waiting_queue = WaitingQueue(maxsize=scenario.queue_length)
    # copy charging_events from scenario
    charging_events = scenario.charging_events
    # set up infrastructure and get all charging points
    free_cps = set(set_up_infrastructure(scenario.infrastructure))
    busy_cps = set()

    # set up charging points in result to store assigned powers
    if realisation_file_name is None:
        results = ElvisResult()
    else:
        results = ElvisResult(scenario, realisation_file_name)

    # ---------------------  Main Loop  ---------------------------
    # loop over every time step
    for time_step_pos in range(len(time_steps)):
        time_step = time_steps[time_step_pos]
        logging.info(' %s', time_step)
        # check if cars must be disconnected, if yes immediately connect car from queue if possible
        update_queue(waiting_queue, time_step, scenario.disconnect_by_time)

        update_cps(free_cps, busy_cps, waiting_queue,
                   time_step, scenario.disconnect_by_time)

        # in case of multiple charging events in the same time step: handle one after the other
        while len(charging_events) > 0 and time_step == charging_events[0].arrival_time:
            waiting_queue = handle_car_arrival(free_cps, busy_cps,
                                               charging_events[0], waiting_queue)
            # remove the arrival from the list
            charging_events = charging_events[1:]

        # assign power
        assign_power = scenario.scheduling_policy.schedule(scenario, free_cps,
                                                           busy_cps, time_step_pos)

        charge_connected_vehicles(assign_power, busy_cps, scenario.resolution)
        results.store_power_charging_points(assign_power, time_step_pos)
    return results


if __name__ == '__main__':

    start_date = datetime.datetime(2020, 1, 1)  # '2020-01-01 00:00:00'
    end_date = datetime.datetime(2020, 1, 7, 23, 59)
    resolution = datetime.timedelta(hours=1) # '01:0:0'
    time_params = (start_date, end_date, resolution)
    # time_params = (start_date, end_date, resolution)
    num_charging_events = 500
    #
    arrival_distribution = [0 for x in range(84)] #[np.random.uniform(0, 1) for x in range(168)]
    arrival_distribution[4] = 1
    arrival_distribution[5] = 1
    #
    queue_length = 2
    infrastructure = {'transformers': [{'id': 'transformer1', 'max_power': 100, 'min_power': 10, 'charging_stations': [{'id': 'cs1', 'max_power': 10, 'min_power': 1, 'charging_points': [{'id': 'cp1', 'max_power': 5, 'min_power': 0.5}, {'id': 'cp2', 'max_power': 5, 'min_power': 0.5}]}, {'id': 'cs2', 'max_power': 10, 'min_power': 1, 'charging_points': [{'id': 'cp3', 'max_power': 5, 'min_power': 0.5}, {'id': 'cp4', 'max_power': 5, 'min_power': 0.5}]}]}]}
    disconnect_by_time = True
    # scheduling_policy = Uncontrolled()
    #
    # conf = ElvisConfig(arrival_distribution, None, None, infrastructure, None, scheduling_policy,
    #                    None, time_params, num_charging_events, queue_length, disconnect_by_time)
    # simulate(conf)

    with open('log.log', 'w'):
        pass
    logging.basicConfig(filename='log.log', level=logging.INFO)

    config = ScenarioConfig()
    config.with_scheduling_policy('UC')
    config.with_std_deviation_soc(0.3)
    config.with_mean_soc(0.4)
    #scenario.with_scheduling_policy(FCFS())
    config.with_infrastructure(infrastructure)
    config.with_disconnect_by_time(disconnect_by_time)
    config.with_queue_length(queue_length)
    config.with_num_charging_events(num_charging_events)
    config.with_mean_park(4)
    config.with_std_deviation_park(1)
    kwargs = {'brand': 'VW', 'model': 'e-Golf', 'probability': 1, 'battery': {'capacity': 35.8,
              'min_charge_power': 0, 'max_charge_power': 150, 'efficiency': 1}}
    config.with_vehicle_types(**kwargs)
    kwargs = {'brand': 'VW', 'model': 'Up', 'probability': 1, 'battery': {'capacity': 35.8,
                                                                              'min_charge_power': 0,
                                                                              'max_charge_power': 150,
                                                                              'efficiency': 1}}
    config.with_vehicle_types(**kwargs)
    config.with_arrival_distribution(arrival_distribution)
    import random
    config.with_transformer_preload([0] * 10000)

    result = simulate(config, start_date, end_date, resolution)
    print(result.power_charging_points)
    # load_profile = result.aggregate_load_profile(scenario.num_simulation_steps())
    # print(list(zip(load_profile, create_time_steps(scenario.start_date, scenario.end_date, scenario.resolution))))

