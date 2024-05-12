import uuid

import fastapi
import httpx

from app import models
from app.repository.db import DB
from app.transport.http.api.public import bets


async def test_make_bet_negative_amount(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
) -> None:
    resp = await auth_client.post(
        app.url_path_for(bets.make_bet.__name__),
        json={
            "event_id": str(uuid.uuid4()),
            "amount": -100.1,
        },
    )
    assert resp.status_code == fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json() == {
        "detail": "[{'type': 'greater_than_equal', 'loc': ('body', 'amount'), 'msg': 'Input should be greater than or equal to 0', 'input': -100.1, 'ctx': {'ge': Decimal('0')}}]",
        "code": "validation_error",
    }


async def test_make_bet_no_more_than_two_decimal_places(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
) -> None:
    resp = await auth_client.post(
        app.url_path_for(bets.make_bet.__name__),
        json={
            "event_id": str(uuid.uuid4()),
            "amount": 100.123,
        },
    )
    assert resp.status_code == fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json() == {
        "detail": "[{'type': 'decimal_max_places', 'loc': ('body', 'amount'), 'msg': 'Decimal input should have no more than 2 decimal places', 'input': 100.123, 'ctx': {'decimal_places': 2}}]",
        "code": "validation_error",
    }


async def test_make_bet(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
    db: DB,
    user: models.User,
) -> None:
    event_id = str(uuid.uuid4())
    resp = await auth_client.post(
        app.url_path_for(bets.make_bet.__name__),
        json={
            "event_id": event_id,
            "amount": 100.12,
        },
    )
    assert resp.status_code == fastapi.status.HTTP_201_CREATED

    _bets = await db.get_user_bets(user=user)

    assert len(_bets) == 1

    [bet] = _bets

    assert resp.json() == {
        "id": str(bet.id),
        "eventId": event_id,
        "amount": "100.12",
        "createdAt": str(bet.created_at),
        "updatedAt": str(bet.updated_at),
        "status": "pending",
        "value": "1",
        "type": "result",
    }
