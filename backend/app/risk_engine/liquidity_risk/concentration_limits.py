from .types import LimitStatus


def evaluate_limit(actual_value: float, warning_threshold: float, breach_threshold: float) -> LimitStatus:
    if actual_value >= breach_threshold:
        return LimitStatus.BREACH
    elif actual_value >= warning_threshold:
        return LimitStatus.WARNING
    else:
        return LimitStatus.OK
