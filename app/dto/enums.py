from __future__ import annotations

import enum
import typing


@typing.final
@enum.unique
class BetStatus(enum.StrEnum):
    """Represent the status of a bet."""

    PENDING = "pending"
    WON = "won"
    LOST = "lost"

    def is_final(self) -> bool:
        return self in {BetStatus.WON, BetStatus.LOST}


EventStatus = BetStatus


@typing.final
@enum.unique
class BetType(enum.StrEnum):
    RESULT = "result"
    TOTALS = "totals"
    HANDICAP = "handicap"


@typing.final
@enum.unique
class ResultValue(enum.StrEnum):
    """Represent the possible values of a result."""

    HOME = "1"
    DRAW = "X"
    AWAY = "2"
