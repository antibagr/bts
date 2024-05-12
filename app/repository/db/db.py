from .bets import BetsDB
from .users import UsersDB


class DB(
    UsersDB,
    BetsDB,
): ...
