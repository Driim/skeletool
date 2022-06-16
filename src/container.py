from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, List, TypeVar, cast, get_type_hints

from .exception import SkeletoolException

if TYPE_CHECKING:
    from .application import ApplicationModule


T = TypeVar("T")


class ContainerException(SkeletoolException):
    pass


class Container:
    # Что мы должны сделать:
    #  - сходить в imports и оттуда забрать map доступных провайдеров
    #  - попутно нужно построить map глобальных провайдеров
    #  - пройтись по провайдерам текущего модуля, построив дерево зависимостей
    #  - проверить что у нас не осталось неудовлетворенных зависимостей

    # Вещи на которые нужно будет обратить внимание:
    #  - в дереве могут образоваться циклы
    #  - не забыть про разные scope провайдеров
    def __init__(self, module: "ApplicationModule", globals: dict = None):
        self._exported: dict[str, Any] = dict()
        self._globals = globals or dict()
        self._module = module
        self._imported = set()
        self._providers: dict[str, Any] = None

    def build_container(self) -> None:
        # С чего начать?
        #  - Просканировать providers и создать карту зависимостей
        #  - написать сортировку работающую только с текущеми провайдерами

        module_meta = self._module.__meta_module__

        # TODO: работа с импортируемыми провайдерами
        # imported_providers = self.get_imported_providers(module_meta.imports)

        obj_graph = self.build_obj_graph(module_meta.providers)

        sorted_obj_graph = self.topological_sort(obj_graph)

        self._providers = self.instantiate_providers(sorted_obj_graph)

        exported_providers_names = set()
        for exported in module_meta.exports:
            exported_providers_names.add(exported.__name__)

        for name, value in self._providers.items():
            if name in exported_providers_names:
                self._exported[name] = value

    def get_imported_providers(self, imports: List) -> dict[str, Any]:
        providers: dict[str, Any] = dict()
        providers_names: set[str] = set()

        for imported_module in imports:
            container = Container(imported_module, self._globals)
            container.build_container()
            self._imported.add(container)

            exported_providers = container.get_exported()
            exported_providers_names = set(exported_providers.keys())

            duplicates = providers_names.union(exported_providers_names)
            if len(duplicates):
                raise ContainerException(duplicates)

            for name, provider in exported_providers.items():
                providers[name] = provider
                providers_names.add(name)

        return providers

    def build_obj_graph(self, providers: List[type]) -> dict[str, dict]:
        obj_graph: dict[str, dict] = dict()

        for provider in providers:
            # TODO: добавить проверки что бы __init__ точно был
            constr_params = get_type_hints(provider.__init__)
            constr_params.pop("return", None)

            provider_deps = set()
            obj_graph[provider.__name__] = {
                "deps": provider_deps,
                "constr": provider,
                "visited": False,
            }

            for param in constr_params.values():
                if param.__name__ == provider.__name__:
                    # Циклическая зависимость
                    raise ContainerException("Циклическая зависимость")

                provider_deps.add(param.__name__)

            # TODO: нужно убедиться что граф не содержит
            #  циклов, т.е. является Directed Acyclic Graph

        return obj_graph

    def topological_sort(self, dep_graph: dict[str, dict]) -> dict[str, dict]:
        result_graph: dict[str, dict] = OrderedDict()

        for name, params in dep_graph.items():
            if params["visited"] is False:
                self.topological_sort_recursive(name, dep_graph, result_graph)

        return result_graph

    def topological_sort_recursive(
        self,
        name: str,
        dep_graph: dict[str, dict],
        result_graph: dict[str, dict],
    ):
        params = dep_graph.get(name)
        params["visited"] = True

        for dep in params["deps"]:
            dep_params = dep_graph.get(dep)
            if dep_params["visited"] is False:
                self.topological_sort_recursive(dep, dep_graph, result_graph)

        result_graph[name] = dep_graph[name]

    def instantiate_providers(self, obj_graph: dict[str, dict]) -> dict[str, Any]:
        providers: dict[str, Any] = dict()

        for name, params in obj_graph.items():
            deps: set = params["deps"]
            constructor = params["constr"]

            if len(deps) == 0:
                providers[name] = constructor()
                continue

            # TODO: инициализация с внешними зависимостями
            args = []
            for dep_name in deps:
                instance = providers.get(dep_name)
                if not instance:
                    raise ContainerException("Не хватает зависимости")

                args.append(instance)

            providers[name] = constructor(*args)

        return providers

    # TODO: сделать так что бы работали typing
    def get_instance(self, cls: str | Callable[..., T]) -> T:
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
            raise ContainerException()

        return cast(T, instance)

    def get_exported(self) -> dict[str, Any]:
        return self._exported
