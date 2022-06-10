from typing import Callable, TypeVar

from .exception import SkeletoolException
from .module import MetaModule


T = TypeVar("T")


class ApplicationException(SkeletoolException):
    pass


class Application:
    def __init__(self, root_module: Callable) -> None:
        print(root_module)
        if not hasattr(root_module, "__meta_module__") or not isinstance(
            root_module.__meta_module__,
            MetaModule,
        ):
            raise ApplicationException()

        self._build_container(root_module)

    def _build_container(self, module: Callable) -> None:
        # Что мы должны сделать:
        #  - сходить в imports и оттуда забрать map доступных провайдеров
        #  - попутно нужно построить map глобальных провайдеров
        #  - пройтись по провайдерам текущего модуля, построив дерево зависимостей
        #  - проверить что у нас не осталось неудовлетворенных зависимостей

        # Вещи на которые нужно будет обратить внимание:
        #  - в дереве могут образоваться циклы
        #  - не забыть про разные scope провайдеров

        pass

    def resolve(self, cls: Callable[..., T]) -> T:
        pass
