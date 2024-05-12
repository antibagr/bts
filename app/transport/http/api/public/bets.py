import typing

import fastapi

from app import models
from app.dto import commands
from app.dto.entities.base import Page
from app.services.bets import BetsService
from app.transport.http import dependencies, schema

router = fastapi.APIRouter(tags=["bets"])


@router.post(
    path="/v1/bets",
    summary="Make a bet",
    responses=schema.error.Responses,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def make_bet(
    req: schema.bets.MakeBetRequest,
    user: typing.Annotated[
        models.User,
        fastapi.Depends(dependencies.get_current_user),
    ],
    bets_service: typing.Annotated[
        BetsService,
        fastapi.Depends(dependencies.bets_service),
    ],
) -> schema.bets.MakeBetResponse:
    command = commands.MakeBet(
        user=user,
        event_id=req.event_id,
        amount=req.amount,
    )
    bet = await bets_service.make_bet(command=command)
    return schema.bets.MakeBetResponse.model_validate(bet, from_attributes=True)


@router.get(
    path="/v1/bets",
    summary="Get all bets",
    responses=schema.error.Responses,
)
async def get_bets(
    user: typing.Annotated[
        models.User,
        fastapi.Depends(dependencies.get_current_user),
    ],
    bets_service: typing.Annotated[
        BetsService,
        fastapi.Depends(dependencies.bets_service),
    ],
) -> Page[schema.bets.Bet]:
    bets = await bets_service.get_user_bets(user=user)
    items = [schema.bets.Bet.model_validate(bet, from_attributes=True) for bet in bets]
    return Page[schema.bets.Bet].create(items)
