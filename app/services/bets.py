import typing

import attrs

from app import models
from app.dto import commands
from app.dto.exceptions import ClientError, PermissionScopeError
from app.repository.db import DB


@typing.final
@attrs.define(slots=True, frozen=True, kw_only=True)
class BetsService:
    _bets_storage: DB

    async def make_bet(
        self,
        *,
        command: commands.MakeBet,
    ) -> models.Bets:
        if command.user.is_superuser:
            raise PermissionScopeError("Superusers are not allowed to make bets.")
        if command.amount < 0:
            raise ClientError("Amount must be a positive number.")
        return await self._bets_storage.create_bet(
            user=command.user,
            event_id=command.event_id,
            amount=command.amount,
        )
