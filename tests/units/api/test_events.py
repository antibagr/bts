import decimal
import uuid

import fastapi
import httpx

from app import models
from app.dto import enums
from app.repository.db import DB
from app.transport.http.api.public import events


async def test_users_cant_update_events(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
) -> None:
    resp = await auth_client.put(
        app.url_path_for(events.update_event.__name__, event_id=str(uuid.uuid4())),
        json={"status": enums.EventStatus.WON},
    )
    assert resp.status_code == fastapi.status.HTTP_403_FORBIDDEN
    assert resp.json() == {
        "code": "permission_scope_error",
        "detail": "Only superusers can update events.",
    }


async def test_superusers_can_update_events(
    app: fastapi.FastAPI,
    superuser_auth_client: httpx.AsyncClient,
) -> None:
    event_id = str(uuid.uuid4())
    resp = await superuser_auth_client.put(
        app.url_path_for(events.update_event.__name__, event_id=event_id),
        json={"status": enums.EventStatus.WON},
    )
    assert resp.status_code == fastapi.status.HTTP_201_CREATED
    assert resp.json() == {
        "id": event_id,
        "status": "won",
    }


async def test_update_event_bets(
    app: fastapi.FastAPI,
    superuser_auth_client: httpx.AsyncClient,
    user: models.User,
    db: DB,
) -> None:
    event_id = uuid.uuid4()
    event_id_2 = uuid.uuid4()
    event_id_3 = uuid.uuid4()

    bets_count = 4

    await db.create_bet(user=user, event_id=event_id, amount=decimal.Decimal("10.00"))
    await db.create_bet(user=user, event_id=event_id, amount=decimal.Decimal("20.00"))
    await db.create_bet(user=user, event_id=event_id_2, amount=decimal.Decimal("15.00"))
    await db.create_bet(user=user, event_id=event_id_3, amount=decimal.Decimal("30.00"))

    resp = await superuser_auth_client.put(
        app.url_path_for(events.update_event.__name__, event_id=event_id),
        json={"status": enums.EventStatus.WON},
    )
    assert resp.status_code == fastapi.status.HTTP_201_CREATED
    resp = await superuser_auth_client.put(
        app.url_path_for(events.update_event.__name__, event_id=event_id_2),
        json={"status": enums.EventStatus.LOST},
    )
    assert resp.status_code == fastapi.status.HTTP_201_CREATED

    bets = await db.get_user_bets(user=user)
    assert len(bets) == bets_count

    for bet in bets:
        if bet.event_id == event_id:
            assert bet.status == enums.BetStatus.WON
        elif bet.event_id == event_id_2:
            assert bet.status == enums.BetStatus.LOST
        elif bet.event_id == event_id_3:
            assert bet.status == enums.BetStatus.PENDING
