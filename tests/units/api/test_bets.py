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


async def test_make_bet_superuser(
    app: fastapi.FastAPI,
    superuser_auth_client: httpx.AsyncClient,
) -> None:
    resp = await superuser_auth_client.post(
        app.url_path_for(bets.make_bet.__name__),
        json={
            "event_id": str(uuid.uuid4()),
            "amount": 100.12,
        },
    )
    assert resp.status_code == fastapi.status.HTTP_403_FORBIDDEN
    assert resp.json() == {
        "detail": "Superusers are not allowed to make bets.",
        "code": "permission_scope_error",
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


async def test_get_bets_empty(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
) -> None:
    resp = await auth_client.get(app.url_path_for(bets.get_bets.__name__))
    assert resp.status_code == fastapi.status.HTTP_200_OK
    assert resp.json() == {"items": [], "total": 0}


async def test_get_bets(
    app: fastapi.FastAPI,
    auth_client: httpx.AsyncClient,
    db: DB,
    user: models.User,
) -> None:
    event_id_1 = str(uuid.uuid4())
    event_id_2 = str(uuid.uuid4())
    for event_id in (event_id_1, event_id_2):
        resp = await auth_client.post(
            app.url_path_for(bets.make_bet.__name__),
            json={
                "event_id": event_id,
                "amount": 100.12,
            },
        )
        assert resp.status_code == fastapi.status.HTTP_201_CREATED

    resp = await auth_client.get(app.url_path_for(bets.get_bets.__name__))
    assert resp.status_code == fastapi.status.HTTP_200_OK

    _bets = await db.get_user_bets(user=user)

    assert resp.json() == {
        "items": [
            {"id": str(_bets[0].id), "status": "pending"},
            {"id": str(_bets[1].id), "status": "pending"},
        ],
        "total": 2,
    }
