from enum import Enum
from functools import wraps
from typing import Callable


# TODO: подумать над скоупами и названиями
class Scope(Enum):
    SINGLETON = 1
    REQUEST = 2


class Injectable:
    def __init__(self, scope: Scope = Scope.SINGLETON) -> None:
        self.__meta_scope__ = scope

    def __call__(self, cls: Callable):
        cls.__meta_scope__ = self.__meta_scope__

        @wraps(cls)
        def injectable_wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        return injectable_wrapper
