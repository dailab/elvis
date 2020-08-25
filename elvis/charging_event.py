
from datetime import datetime


class ChargingEvent:
    # static field incremented by 1 for every __init__
    counter = 1
    """This class contains relevant parameters to describe a charging event.

    """
    def __init__(self, arrival_time):
        self.id = str(ChargingEvent.counter)
        ChargingEvent.counter += 1
        self.arrival_time = arrival_time
        self.parking_time = 5
        self.soc = 0.8
        self.soc_target = 1.0
        self.vehicle_type = 'this should be the car'

    def __str__(self):
        print_out = 'Charging_event: ' + self.id + ', '
        print_out += 'Arrival time: ' + str(self.arrival_time) + ', '
        print_out += 'Parking_time: ' + str(self.parking_time) + ', '
        print_out += 'SOC: ' + str(self.soc) + ', '
        print_out += 'SOC target: ' + str(self.soc_target) + ', '
        print_out += 'Connected car: ' + str(self.vehicle_type)

        return print_out

    def to_dict(self):
        """Make dict of the instance of :obj: `charging_event.ChargingEvent`
            to speed up simulation.

        Returns:
            dictionary: (dict)"""

        dictionary = {'arrival_time': self.arrival_time,
                      'parking_time': self.parking_time,
                      'soc': self.soc,
                      'soc_target': self.soc_target,
                      'vehicle_type': self.vehicle_type}

        return dictionary
