class RecoveryError(Exception):
    pass


class CollectionMissingError(RecoveryError):
    pass


class CollectionCorruptedError(RecoveryError):
    pass


class EmbeddingVersionMismatchError(RecoveryError):
    pass


class SchemaVersionMismatchError(RecoveryError):
    pass


class RebuildInterruptedError(RecoveryError):
    pass


class RebuildFailedError(RecoveryError):
    pass
