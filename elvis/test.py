import elvis.config
import elvis.simulate
import yaml
import datetime
import logging

from elvis.config import ElvisConfigBuilder
from elvis.charging_event_generator import create_time_steps
from elvis.sched.schedulers import Uncontrolled, FCFS


builder = ElvisConfigBuilder()

with open('../data/config_builder/tankstelle_city.yaml') as file:
    yaml_str = yaml.full_load(file)

builder.from_yaml(yaml_str)

config = builder.build()

result = elvis.simulate.simulate(config)
print(result.power_connection_points)
load_profile = result.aggregate_load_profile(config.num_simulation_steps())
print(list(zip(load_profile, create_time_steps(config.start_date, config.end_date, config.resolution))))

builder.to_yaml('../data/config_builder/test.yaml')





