
from datetime import datetime
from uuid import uuid4


class ChargingEvent:
    """This class contains relevant parameters to describe a charging event.

    """
    def __init__(self, arrival_time):
        self.id = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
        self.arrival_time = arrival_time
        self.parking_time = 5
        self.soc = 0.8
        self.soc_target = 1.0
        self.vehicle_type = 'this should be the car'

    def __str__(self):
        print_out = '----------' + '\n'
        print_out += 'Charging_event: ' + self.id + '\n'
        print_out += 'Arrival time: ' + str(self.arrival_time) + '\n'
        print_out += 'Parking_time: ' + str(self.parking_time) + '\n'
        print_out += 'SOC: ' + str(self.soc) + '\n'
        print_out += 'SOC target: ' + str(self.soc_target) + '\n'
        print_out += 'Connected car: ' + str(self.vehicle_type) + '\n'
        print_out += '----------'

        return print_out

    def to_dict(self):
        """Make dict of the instance of :obj: charging_event.ChargingEvent
            to speed up simulation.

        Returns:
            dictionary: (dict)"""

        dictionary = {'arrival_time': self.arrival_time,
                      'parking_time': self.parking_time,
                      'soc': self.soc,
                      'soc_target': self.soc_target,
                      'vehicle_type': self.vehicle_type}

        return dictionary
