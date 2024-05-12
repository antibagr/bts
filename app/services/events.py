import typing

import attrs

from app.dto import commands
from app.repository.db import DB


@typing.final
@attrs.define(slots=True, frozen=True, kw_only=True)
class EventsService:
    _events_storage: DB

    async def update_event(
        self,
        *,
        command: commands.UpdateEvent,
    ) -> None:
        # TODO (rudiemeant@gmail.com): Make sure the event is not already closed
        # When events are actually stored in the database
        # https://jira.example.com/browse/FOOBAR-123

        await self._events_storage.update_event(
            event_id=command.event_id,
            status=command.status,
        )
