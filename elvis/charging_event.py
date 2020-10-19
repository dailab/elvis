"""A charging event represents the event of a vehicle charging. It is described in its:
- arrival time: Time the vehicle arrives at the infrastructure.
- parking time: The time the car parks at the infrastructure before it is being driven away.
- """
import datetime
import numpy as np

from elvis.vehicle import ElectricVehicle
from elvis.battery import EVBattery


class ChargingEvent:
    # static field incremented by 1 for every __init__
    counter = 1
    """This class contains relevant parameters to describe a charging event.
    """
    def __init__(self, arrival_time, parking_time, vehicle_type):
        """

        Args:
            arrival_time: Date and time the vehicle arrives at the infrastructure.
            mean_park: (float): Mean of the gaussian distribution the parking time is generated
                from.
            std_deviation_park: (float): Standard deviation of the gaussian distribution the parking
                time is generated from.
        """
        assert isinstance(arrival_time, datetime.datetime)
        assert isinstance(parking_time, (float, int))
        assert isinstance(vehicle_type, ElectricVehicle)

        # TODO: Implement variable values.
        self.id = 'Charging event: ' + str(ChargingEvent.counter)
        ChargingEvent.counter += 1
        self.arrival_time = arrival_time
        self.parking_time = parking_time
        self.leaving_time = self.arrival_time + datetime.timedelta(hours=self.parking_time)
        self.soc = 0.8
        self.soc_target = 1.0
        self.vehicle_type = vehicle_type

    def __str__(self):
        print_out = self.id + ', '
        print_out += 'Arrival time: ' + str(self.arrival_time) + ', '
        print_out += 'Parking_time: ' + str(self.parking_time) + ', '
        print_out += 'Leaving_time: ' + str(self.leaving_time) + ', '
        print_out += 'SOC: ' + str(self.soc) + ', '
        print_out += 'SOC target: ' + str(self.soc_target) + ', '
        print_out += 'Connected car: ' + str(self.vehicle_type)
        return print_out

    def to_dict(self):
        dictionary = dict()
        dictionary['arrival_time'] = self.arrival_time
        dictionary['parking_time'] = self.parking_time
        dictionary['leaving_time'] = self.leaving_time
        dictionary['soc'] = self.soc
        dictionary['soc_target'] = self.soc_target
        dictionary['vehicle_type'] = self.vehicle_type.to_dict()
        return dictionary

    def to_dict(self):
        """Make dict of the instance of :obj: `charging_event.ChargingEvent`
            to speed up simulation.

        Returns:
            dictionary: (dict)"""

        dictionary = {'arrival_time': self.arrival_time,
                      'parking_time': self.parking_time,
                      'leaving_time': self.leaving_time,
                      'soc': self.soc,
                      'soc_target': self.soc_target,
                      'vehicle_type': self.vehicle_type}

        return dictionary
