"""Domain exceptions of the merchant world builder."""


class WorldError(Exception):
    """Base exception for every error raised by the world builder.

    Debug: the message names the stage and the offending record; rerun the stage
    with the same configuration to reproduce, since every stage is deterministic.
    """


class ConfigError(WorldError):
    """Raised when the world configuration file is missing or not valid TOML."""


class DeckContractError(WorldError):
    """Raised when a deck row violates the schema the builder relies on."""


class AttributionError(WorldError):
    """Raised when tickets cannot be attached to merchants under the constraints."""


class ValidationFailure(WorldError):
    """Raised when a built world violates one of its declared invariants."""


class GenerationBudgetError(WorldError):
    """Raised before a paid call that could cross the generation budget."""


class SamplingError(WorldError):
    """Raised when a role cannot be filled from the available deck tickets."""
