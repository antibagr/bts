import typing

import fastapi
import pydantic

from app.dto.exceptions import NotFoundError
from app.services.liveness_probe import LivenessProbeSrv
from app.transport.http import dependencies

router: typing.Final = fastapi.APIRouter()


@typing.final
class StatusResponse(pydantic.BaseModel):
    status: typing.Literal["OK", "ERROR"]


@router.get(
    "/health",
    response_model=StatusResponse,
    response_class=fastapi.responses.ORJSONResponse,
    responses={
        fastapi.status.HTTP_200_OK: {"description": "Service is healthy"},
        fastapi.status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service is not healthy"},
    },
)
async def get_api_status(
    liveness_probe_service: typing.Annotated[LivenessProbeSrv, fastapi.Depends(dependencies.liveness_probe_service)],
) -> fastapi.responses.ORJSONResponse:
    if await liveness_probe_service.all_alive():
        return fastapi.responses.ORJSONResponse({"status": "ok"})
    return fastapi.responses.ORJSONResponse(
        {"status": "error"},
        status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@router.get(
    "/health/{service}",
    response_model=StatusResponse,
    response_class=fastapi.responses.ORJSONResponse,
    responses={
        fastapi.status.HTTP_200_OK: {"description": "Service is healthy"},
        fastapi.status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service is not healthy"},
    },
)
async def get_service_status(
    service: typing.Annotated[str, fastapi.Path(..., title="The service to check the status of")],
    liveness_probe_service: typing.Annotated[LivenessProbeSrv, fastapi.Depends(dependencies.liveness_probe_service)],
) -> fastapi.responses.ORJSONResponse:
    if service not in liveness_probe_service:
        raise NotFoundError(f"Service {service} not found")
    if await liveness_probe_service.is_alive(service=service):
        return fastapi.responses.ORJSONResponse({"status": "ok"})
    return fastapi.responses.ORJSONResponse(
        {"status": "error"},
        status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
    )
