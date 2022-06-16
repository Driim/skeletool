from enum import Enum


# TODO: подумать над скоупами и названиями
class Scope(Enum):
    SINGLETON = 1
    REQUEST = 2


class Injectable:
    def __init__(self, scope: Scope = Scope.SINGLETON) -> None:
        self.__meta_scope__ = scope

    def __call__(self, cls: type):
        cls.__meta_scope__ = self.__meta_scope__

        return cls
