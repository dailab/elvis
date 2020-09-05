
import math


class Distribution:
    """Represents a distribution of some x value to a y value."""

    def __getitem__(self, key):
        raise NotImplementedError()

    @property
    def bounds(self):
        raise NotImplementedError()

    @property
    def min_x(self):
        return bounds["x"]["min"]

    @property
    def max_x(self):
        return bounds["x"]["max"]

    @property
    def min_y(self):
        return bounds["y"]["min"]

    @property
    def max_y(self):
        return bounds["y"]["max"]


class NormalDistribution(Distribution):
    """A normal distribution."""

    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

        # 1 / (sigma*sqrt(2*pi))
        self.fac = 1.0 / (sigma * math.sqrt(2.0 * math.pi)) 

    def __getitem__(self, key):
        # ((x-mu)/sigma)^2
        exp = math.pow((key - self.mu) / self.sigma, 2.0)

        # fac * e^(-.5*exp)
        return self.fac * math.exp(-0.5 * exp)

    @property
    def bounds(self):
        return {
            "x": {
                "min": -math.inf,
                "max": math.inf
            },
            "y": {
                "min": 0,
                "max": 1,
            }
        }


class InterpolatedDistribution(Distribution):
    """A distribution that generates new values using some form of interpolation of a set of given points."""

    def __init__(self, points, bounds, interpolate):
        self.points = points
        self._bounds = bounds
        self.interpolate = interpolate

    @staticmethod
    def linear(points, bounds):
        return InterpolatedDistribution(points, bounds, InterpolatedDistribution._linear_interpolation)

    @staticmethod
    def _linear_interpolation(y0, y1, offset):
        return y0 + (y1 - y0) * offset

    def __getitem__(self, key):
        if key < self.points[0][0]:
            return self.points[0][1]

        if key >= self.points[-1][0]:
            return self.points[-1][1]

        # find the closest point we have.
        min_i = 0

        for i, pt in enumerate(self.points):
            if pt[0] >= key:
                min_i = i
                break

        p0 = self.points[min_i - 1]
        p1 = self.points[min_i]
        offset = (key - p0[0]) / (p1[0] - p0[0])

        return self.interpolate(p0[1], p1[1], offset)

    @property
    def bounds(self):
        return self._bounds


class EquallySpacedInterpolatedDistribution(Distribution):
    """A distribution that generates new values using some form of interpolation of a set of given points,
     whose x values are the same distance apart."""

    def __init__(self, points, bounds, interpolate):
        self.points = points
        self._bounds = bounds
        self.interpolate = interpolate
        self.distance_between_points = abs(points[1][0] - points[0][0])

    @staticmethod
    def linear(points, bounds):
        return EquallySpacedInterpolatedDistribution(points, bounds, InterpolatedDistribution._linear_interpolation)

    @staticmethod
    def _linear_interpolation(y0, y1, offset):
        return y0 + (y1 - y0) * offset

    def __getitem__(self, key):
        if key < self.points[0][0]:
            return self.points[0][1]

        if key >= self.points[-1][0]:
            return self.points[-1][1]

        # find the closest point we have.
        min_i = math.ceil((key - self.points[0][0]) / self.distance_between_points)

        p0 = self.points[min_i - 1]
        p1 = self.points[min_i]
        offset = (key - p0[0]) / (p1[0] - p0[0])

        return self.interpolate(p0[1], p1[1], offset)

    @property
    def bounds(self):
        return self._bounds
