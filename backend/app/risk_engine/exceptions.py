class RiskEngineError(Exception):
    pass

class SolverError(RiskEngineError):
    pass

class InvalidInputError(RiskEngineError):
    pass

class MaturedBondError(RiskEngineError):
    pass
