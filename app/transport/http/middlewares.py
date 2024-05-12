import time
import typing

import fastapi
import fastapi.middleware.cors
from loguru import logger


def register_middlewares(app: fastapi.FastAPI) -> None:
    app.add_middleware(
        fastapi.middleware.cors.CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(_log_request)


async def _log_request(
    request: fastapi.Request,
    call_next: typing.Callable[..., typing.Awaitable[fastapi.Response]],
) -> fastapi.Response:
    start_time = time.time()
    response: fastapi.Response = await call_next(request)
    route = request.scope.get("route")
    logger.info(
        "api_request",
        path=route.path if route else "",
        url=str(request.url),
        http_method=request.method,
        http_status=response.status_code,
        path_params=request.path_params,
        query_params=dict(request.query_params),
        process_time=time.time() - start_time,
    )
    return response
