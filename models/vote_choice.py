from enum import Enum


class VoteChoice(Enum):
    """Possible voting choices for one deputy."""

    IN_FAVOR = "in_favor"
    AGAINST = "against"
    ABSTENTION = "abstention"
    ABSENT = "absent"
