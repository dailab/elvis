"""Representation of a charging point of the infrastructure.

A charging point is the point of coupling between connection point (connection to the car)
and the grid. In LV grids the charging point immediately connects to the grid in MV grids a
transformer is needed in between.
- The charging point may consist of multiple connection points.
- It may be automated: After a car is charged it automatically connects itself to another car if
    available.
- It may be inductive: No physical connection between car and connection point is needed:
    lower efficiency.
- Or manual: User have to connect and disconnect their vehicle by hand: Longer phases of inactivity.
- It can be operated with direct current or alternating current where different efficiencies
    have to be considered.
- Its power is the sum over the power of its connection points.
- It is limited by its power limits where the lower limit has to be understood as at least the
    lower limit or zero.
"""

import connection_point


class ChargingPoint:
    """Models a charging point of the charging ingrastructure.

    TODO:
        - Get values from config.
    """

    def __init__(self, num_connection_points):
        # power limits
        self.min_charging_power = 10
        self.max_charging_power = 20

        self.connection_points = self.set_connection_points_static(num_connection_points)

        # working princibple
        self.manual = True
        self.automated = False
        self.inductive = False

        # power type AC = True, DC = False
        self.ac_power_supply = True

        self.efficiency = 1

    def set_connection_points_static(self, n):
        """Create n connection points.
        With static values for power limits

        Args:
            n: (int): Number of connection points to be created.

        Returns:
            connection_points: (list): Containing the connection points as instances from
            :obj: `ConnectionPoint`.
        """
        connection_points = []

        while n > 0:
            n -= 1
            connection_points.append(connection_point.ConnectionPoint((2, 5), self))
        return connection_points


# def defineChargingPower(cp, powerAvailable):
#     ev = cp.connectedEv
#     min = max(ev.powerMin, cp.powerMin)
#     max = min(ev.powerMax, cp.powerMax)
#     # The power must not exceed any limits
#     if powerAvailable > max:
#         power = max
#     elif powerAvailable < min:
#         power = 0
#     else:
#         power = powerAvailable
#
#     # The power can't overload the EVBattery
#     # Integral of power over time = Energy
#     if convertPowerToEnergy(power, timeStepOfSimulation) + ev.currentEnergy > ev.capacity:
#         power = convertEnergyToPower(EnergyNeededInEV, timeStep)
#
#     return power
#
#
# # Give maximum or maximum possible with what is left in battery but not less than minimum.
# def getPowerFromStationaryBattery():
#     power = min(battery.maxPower, convertEnergyToPower(battery.currentEnergy, timeStep)
#     if power < battery.minPower:
#         power = 0
#     return power
#
#
# # This is the same procedure for every charging process (stationary or mobile battery) we could use a charging function
# # working for both
# def chargeStationaryBattery(power):
#     if power < battery.minPower:
#     # do not charge
#     elif power > battery.maxPower:
#     # charge with max power
#     else:
#
#
# # charge with available power
#
#
# arrivals = arrivalsDistribution(amountOfArrivals)
#
# for t in simulation time:
#     if t in arrivals:
#         ev = create_ev(evDistribution)
#         for cp in chargingPoints:
#             if cp.connectedEV is not None:
#                 connect
#                 ev
#         else ev to queue if queue has empty spot
#     # Usually no stationary battery with UC control strategy, but would be easily possible
#     powerAvailable = transformerLimit[t] - preload[t] + getPowerFromStationaryBattery()
#
#     # Loop over chargingpoints
#     for cp in chargingPoints:
#         if cp.connectedEV == None
#             ev = cp.connectedEV
#         if ev.parkingTime < t - ev.arrivalTime:
#             ev.disconnect()
#         else:  # (charge vehicle)
#             power = defineChargingPower(cp, powerAvailable)
#             powerAvailable -= power
#             ev.battery.SOC += convertPowerToEnergy(power * ev.efficiency / ev.battery.capacity)
#
#             # Store Time Series Data:
#             powerCp = power
#             powerBattery = power * ev.efficiency
#             SOCEV = ev.battery.SOC
#
#     # If not all power possible from transformer is needed the stationary battery if available can be charged
#     If
#     powerAvailable > 0:
#     chargeStationaryBattery(powerAvailable)