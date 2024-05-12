import contextlib
import contextvars
import random
import typing
import uuid

operation_id: contextvars.ContextVar[int] = contextvars.ContextVar("operation_id")
_user_id: contextvars.ContextVar[uuid.UUID] = contextvars.ContextVar("user_id")


@contextlib.contextmanager
def user_id(value: uuid.UUID) -> typing.Generator[None, None, None]:
    token = _user_id.set(value)
    try:
        yield
    finally:
        _user_id.reset(token)


def set_new_operation_id() -> int:
    op_id = random.getrandbits(128)
    operation_id.set(op_id)
    return op_id


def get_operation_id() -> int:
    op_id: int
    try:
        op_id = operation_id.get()
    except LookupError:
        op_id = set_new_operation_id()
    return op_id
