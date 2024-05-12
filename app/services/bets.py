import typing

import attrs

from app import models
from app.dto import commands
from app.dto.exceptions import PermissionScopeError
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
        return await self._bets_storage.create_bet(
            user=command.user,
            event_id=command.event_id,
            amount=command.amount,
        )

    async def get_user_bets(
        self,
        *,
        user: models.User,
    ) -> list[models.Bets]:
        return await self._bets_storage.get_user_bets(user=user)
