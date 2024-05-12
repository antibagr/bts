import asyncio
import functools
import platform
import signal
import types
import typing

import click
from loguru import logger

from app.dto.annotations import P, T
from app.services.service import application_dependencies

F = typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]]


def coro(f: F[P, T]) -> F[P, T]:
    @functools.wraps(f)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger.info("run_cmd", command=f.__name__)
        _coro = f(*args, **kwargs)
        if platform.system() != "Windows":
            import uvloop  # noqa: PLC0415

            return uvloop.run(_coro)

        return asyncio.new_event_loop().run_until_complete(_coro)

    return typing.cast(F[P, T], _wrapper)


@click.group()
def cli() -> None: ...


@click.command()
@coro
async def run() -> None:
    async with application_dependencies():
        ...


def handle_exit_signal(_sig: int, _frame: types.FrameType | None) -> typing.NoReturn:
    raise SystemExit


cli.add_command(run)
signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)

if __name__ == "__main__":
    cli()
