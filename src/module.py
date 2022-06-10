from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, List


@dataclass
class MetaModule:
    # TODO: улучшить Typing, List[Module], List[Injectable]
    #  имееть смысл вынести в отдельный файл
    imports: List = field(default_factory=list)
    providers: List = field(default_factory=list)
    exports: List = field(default_factory=list)
    is_global: bool = field(default=False)


class Module:
    # TODO: Так же хотелось бы иметь возможность передать сюда конфиг модуля,
    #       нужно подумать как это сделать лучше, через inject или imports?
    def __init__(self, meta: MetaModule = MetaModule()) -> None:
        self.__meta_module__ = meta

    # TODO: улучшить typing
    def __call__(self, cls: Callable):
        cls.__meta_module__ = self.__meta_module__

        @wraps(cls)
        def module_wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        return module_wrapper
