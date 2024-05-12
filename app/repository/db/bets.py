import decimal
import uuid

import sqlmodel

from app import models
from app.dto import enums
from app.dto.exceptions import ClientError
from app.repository.db.base import BaseDB, Filters


class BetsDB(BaseDB):
    async def create_bet(
        self,
        user: models.User,
        event_id: uuid.UUID,
        amount: decimal.Decimal,
    ) -> models.Bets:
        return await self.create(
            models.Bets(
                event_id=event_id,
                user_id=user.id,
                amount=amount,
                status=enums.BetStatus.PENDING,
            )
        )

    async def get_user_bets(
        self,
        user: models.User,
        **filters: Filters,
    ) -> list[models.Bets]:
        """Get all bets made by a user."""
        filters["user_id"] = user.id
        return await self.get_many(models.Bets, **filters)

    async def update_bet_status(
        self,
        bet_id: uuid.UUID,
        status: enums.BetStatus,
    ) -> models.Bets:
        """Update the status of a bet."""
        bet = await self.get(models.Bets, id=bet_id)
        if bet.status.is_final():
            raise ClientError("Cannot update the status of a final bet.")
        bet.status = status
        return await self.update(bet)

    async def update_event(
        self,
        event_id: uuid.UUID,
        status: enums.EventStatus,
    ) -> None:
        """Update the status of all bets of an event."""
        await self.session.execute(
            sqlmodel.update(models.Bets).where(sqlmodel.col(models.Bets.event_id) == event_id).values(status=status)
        )
