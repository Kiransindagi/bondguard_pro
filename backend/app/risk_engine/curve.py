from decimal import Decimal

from .exceptions import InvalidInputError


class YieldCurve:
    def __init__(self, points: dict[float, Decimal]):
        """
        Initialize with points mapping tenor in years to decimal yield.
        Example: {2.0: Decimal('0.0425'), 10.0: Decimal('0.0450')}
        """
        if not points:
            raise InvalidInputError("Yield curve must have at least one point.")
        self.points = sorted(points.items())

    def get_yield(self, tenor_years: float) -> Decimal:
        """
        Get linearly interpolated yield for a given tenor.
        Flat extrapolation outside available tenor boundaries.
        Returns yield as Decimal.
        """
        if tenor_years <= self.points[0][0]:
            return self.points[0][1]
        if tenor_years >= self.points[-1][0]:
            return self.points[-1][1]

        for i in range(len(self.points) - 1):
            t1, y1 = self.points[i]
            t2, y2 = self.points[i + 1]
            if t1 <= tenor_years <= t2:
                # Linear interpolation
                weight = Decimal(str((tenor_years - t1) / (t2 - t1)))
                return y1 + (y2 - y1) * weight

        return self.points[-1][1]
