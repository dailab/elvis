
class Power:
    """Unit for electrical power."""

    def __init__(self, watts):
        self.watts = watts

    @property
    def kilowatts(self):
        return self.watts / 1000.0

class Current:
    """Unit for electrical current."""

    def __init__(self, amps):
        self.amps = amps

    @property
    def milliamps(self):
        return self.amps * 1000.0

    def __mul__(self, hours):
        return Charge(self.amps * hours)

class Charge:
    """Unit for electrical charge."""

    def __init__(self, amp_hours):
        self.amp_hours = amp_hours

    def energy(self, voltage):
        return Energy(amp_hours * voltage)

class Energy:
    """Unit for electrical energy."""

    def __init__(self, kwh):
        self.kwh = kwh

    def charge(self, voltage):
        return Charge(kwh / voltage)
