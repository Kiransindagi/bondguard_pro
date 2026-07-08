class StressTestingError(Exception):
    pass

class ScenarioNotFoundError(StressTestingError):
    pass

class InvalidScenarioDefinitionError(StressTestingError):
    pass

class StressCalculationError(StressTestingError):
    pass
