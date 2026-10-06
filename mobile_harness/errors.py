class HarnessError(Exception):
    """Expected error that should be presented without a traceback."""


class ConfigurationError(HarnessError):
    """Configuration or contract is invalid."""


class GateError(HarnessError):
    """A workflow gate prevented progress."""

