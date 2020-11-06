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
    def __init__(self, arrival_time, parking_time, soc, vehicle_type):
        """

        Args:
            arrival_time: (datetime.datetime): Date and time the vehicle arrives at the
                infrastructure.
            parking_time: (float): Number of hours the vehicle is parking.
            soc: (float): SOC of the vehicle at arrival.
            vehicle_type: (:obj: `elvis.vehicle.VehicleType`): Instance of the vehicle describing
                class VehicleType.
        """
        assert isinstance(arrival_time, datetime.datetime)
        assert isinstance(parking_time, (float, int))
        assert isinstance(soc, (float, int)) and (0 <= soc <= 1.0)
        assert isinstance(vehicle_type, ElectricVehicle)

        # TODO: Implement variable values.
        self.id = 'Charging event: ' + str(ChargingEvent.counter)
        ChargingEvent.counter += 1
        self.arrival_time = arrival_time
        self.parking_time = parking_time
        self.leaving_time = self.arrival_time + datetime.timedelta(hours=self.parking_time)
        self.soc = soc
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

    @staticmethod
    def from_dict(**kwargs):
        """Initialise an instance of ChargingEvent with values stored in a dict.

        Args:

            **kwargs: Arbitrary keyword arguments.
        """

        necessary_keys = ['arrival_time', 'parking_time', 'soc', 'vehicle_type']

        for key in necessary_keys:
            assert key in kwargs, 'Not all necessary keys are included to create a ChargingEvent ' \
                                  'from dict.'

        arrival_time = kwargs['arrival_time']
        parking_time = kwargs['parking_time']
        soc = kwargs['soc']
        vehicle_type = ElectricVehicle.from_dict(**kwargs['vehicle_type'])

        return ChargingEvent(arrival_time, parking_time, soc, vehicle_type)
