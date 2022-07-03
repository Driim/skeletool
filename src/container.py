from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, List, TypeVar, cast, get_type_hints

from src.module import MetaModule, Module

from .exception import SkeletoolException


T = TypeVar("T")


class ContainerException(SkeletoolException):
    pass


@dataclass
class ProviderParams:
    constructor: type
    dependencies: list[str] = field(default_factory=list)
    is_visited: bool = field(default=False)


class AbstractContainer(ABC):
    @abstractmethod
    def build_container(self) -> None:
        ...

    @abstractmethod
    def get_provider_instance(self, cls: str | Callable[..., T]) -> T:
        ...

    @abstractmethod
    def get_exported_providers(self) -> dict[str, Any]:
        ...


class SingletonContainer(AbstractContainer):
    # Вещи на которые нужно будет обратить внимание:
    #  - в дереве могут образоваться циклы
    #  - не забыть про разные scope провайдеров
    #  - глобавльные провайдеры
    def __init__(
        self,
        module: Module,
        globals: dict[str, Any],
        initialized_modules: dict[str, AbstractContainer],
    ):
        self._exported: dict[str, Any] = dict()
        self._globals = globals
        self._module = module
        self._providers: dict[str, Any] = None
        self._initialized_modules = initialized_modules

    def build_container(self) -> None:
        module_meta = self._module.__meta_module__

        obj_graph = self._build_obj_graph(module_meta.providers)

        sorted_obj_graph = self._topological_sort(obj_graph)

        imported_providers = self.get_imported_providers(module_meta.imports)

        self._providers = self._instantiate_providers(
            sorted_obj_graph,
            imported_providers,
        )

        self._exported = self._get_exported_list(module_meta)

        self._initialized_modules[self._module.__name__] = self

    def _build_obj_graph(self, providers: List[type]) -> dict[str, ProviderParams]:
        obj_graph: dict[str, ProviderParams] = dict()

        for provider in providers:
            # TODO: добавить проверки что бы __init__ точно был
            constr_params = get_type_hints(provider.__init__)
            constr_params.pop("return", None)

            provider_deps = []
            obj_graph[provider.__name__] = ProviderParams(provider, provider_deps)

            for param in constr_params.values():
                if param.__name__ == provider.__name__:
                    raise ContainerException(
                        f"Provider {provider.__name__} cyclic dependency",
                    )

                provider_deps.append(param.__name__)

            # TODO: нужно убедиться что граф не содержит
            #  циклов, т.е. является Directed Acyclic Graph

        return obj_graph

    def _topological_sort(
        self,
        dep_graph: dict[str, ProviderParams],
    ) -> dict[str, ProviderParams]:
        result_graph: dict[str, ProviderParams] = OrderedDict()

        for name, params in dep_graph.items():
            if params.is_visited is False:
                self._topological_sort_recursive(name, dep_graph, result_graph)

        return result_graph

    def _topological_sort_recursive(
        self,
        name: str,
        dep_graph: dict[str, ProviderParams],
        result_graph: dict[str, ProviderParams],
    ):
        params = dep_graph.get(name)
        if params is None:
            return  # external dep

        params.is_visited = True

        for dep in params.dependencies:
            dep_params = dep_graph.get(dep)
            if dep_params is None:
                continue  # external dep

            if dep_params.is_visited is False:
                self._topological_sort_recursive(dep, dep_graph, result_graph)

        result_graph[name] = dep_graph[name]

    def get_imported_providers(self, imports: List[type]) -> dict[str, Any]:
        providers: dict[str, Any] = dict()
        providers_names: set[str] = set()

        for imported_module in imports:
            container = self._get_imported_container(imported_module)

            exported_providers = container.get_exported_providers()

            for name, provider in exported_providers.items():
                if name in providers_names:
                    raise ContainerException(
                        f"The provider {name} is exported from two different modules",
                    )
                providers[name] = provider
                providers_names.add(name)

        return providers

    def _get_imported_container(self, imported_module: Module) -> AbstractContainer:
        if imported_module.__name__ in self._initialized_modules:
            return self._initialized_modules[imported_module.__name__]

        container = SingletonContainer(
            imported_module,
            self._globals,
            self._initialized_modules,
        )
        container.build_container()
        return container

    def _instantiate_providers(
        self,
        obj_graph: dict[str, ProviderParams],
        imported: dict[str, Any],
    ) -> dict[str, Any]:
        providers: dict[str, Any] = imported

        for name, params in obj_graph.items():
            deps = params.dependencies
            constructor = params.constructor

            if len(deps) == 0:
                providers[name] = constructor()
                continue

            args = []
            for dep_name in deps:
                instance = providers.get(dep_name)
                if not instance:
                    raise ContainerException(
                        f"Instantiation error of the {name} class, the {dep_name} class is missing",
                    )

                args.append(instance)

            providers[name] = constructor(*args)

        return providers

    def _get_exported_list(self, module_meta: MetaModule) -> None:
        exported_providers_names = set([exp.__name__ for exp in module_meta.exports])

        exported: dict[str, Any] = dict()

        for name, value in self._providers.items():
            if name in exported_providers_names:
                exported[name] = value

        return exported

    # TODO: сделать так что бы работали typing
    def get_provider_instance(self, cls: str | Callable[..., T]) -> T:
        instance = None
        cls_name = None

        if isinstance(cls, Callable):
            cls_name = cls.__name__
        else:
            cls_name = cls

        instance = self._exported.get(cls_name)

        if instance is None:
            instance = self._globals.get(cls_name)

        if instance is None:
            raise ContainerException(f"{cls_name} is missing")

        return cast(T, instance)

    def get_exported_providers(self) -> dict[str, Any]:
        return self._exported


class Container:
    def __init__(self, module: Module) -> None:
        self._globals: dict[str, Any] = dict()
        self._initialized_modules: dict[str, AbstractContainer] = dict()
        self._container_impl = SingletonContainer(
            module,
            self._globals,
            self._initialized_modules,
        )

    def build_container(self) -> None:
        return self._container_impl.build_container()

    def get_provider_instance(self, cls: str | Callable[..., T]) -> T:
        return self._container_impl.get_provider_instance(cls)
