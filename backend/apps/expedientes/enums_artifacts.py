from enum import Enum

class ArtifactStatusEnum(str, Enum):
    DRAFT      = 'DRAFT'
    COMPLETED  = 'COMPLETED'
    SUPERSEDED = 'SUPERSEDED'
    VOID       = 'VOID'

    @classmethod
    def choices(cls):
        return [
            (cls.DRAFT.value, 'Draft'),
            (cls.COMPLETED.value, 'Completed'),
            (cls.SUPERSEDED.value, 'Superseded'),
            (cls.VOID.value, 'Void'),
        ]
