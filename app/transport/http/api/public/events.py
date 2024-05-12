import typing
import uuid

import fastapi

from app import models
from app.dto import commands
from app.dto.exceptions import PermissionScopeError
from app.services.events import EventsService
from app.transport.http import dependencies, schema

router = fastapi.APIRouter(tags=["events"])


@router.put(
    path="/v1/events/{event_id}",
    summary="Update an event",
    responses=schema.error.Responses,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def update_event(
    event_id: typing.Annotated[uuid.UUID, fastapi.Path(..., description="Event ID")],
    req: schema.events.UpdateEventRequest,
    user: typing.Annotated[models.User, fastapi.Depends(dependencies.get_current_user)],
    events_service: typing.Annotated[EventsService, fastapi.Depends(dependencies.events_service)],
) -> schema.events.Event:
    if not user.is_superuser:
        raise PermissionScopeError("Only superusers can update events.")
    command = commands.UpdateEvent(event_id=event_id, status=req.status)
    await events_service.update_event(command=command)
    return schema.events.Event(id=event_id, status=req.status)
