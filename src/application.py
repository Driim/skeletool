from typing import Callable, Protocol, TypeVar

from .container import Container
from .exception import SkeletoolException
from .module import MetaModule


T = TypeVar("T")


class ApplicationException(SkeletoolException):
    ...


class ApplicationModule(Protocol):
    __meta_module__: MetaModule


class Application:
    def __init__(self, root_module: ApplicationModule) -> None:
        if not hasattr(root_module, "__meta_module__") or not isinstance(
            root_module.__meta_module__,
            MetaModule,
        ):
            raise ApplicationException(
                f"{str(root_module)} does not implement {ApplicationModule} protocol",
            )

        self._container = Container(root_module)

    def resolve(self, cls: Callable[..., T]) -> T:
        self._container.build_container()
        return self._container.get_provider_instance(cls)
