from src.container import Container
from src.injectable import Injectable
from src.module import MetaModule, Module


class TestContainer:
    def test_should_instance_provider_without_deps(self):
        @Injectable()
        class ExampleProvider:
            pass

        @Module(MetaModule(providers=[ExampleProvider], exports=[ExampleProvider]))
        class ExampleModule:
            pass

        container = Container(ExampleModule())
        container.build_container()
        instance = container.get_instance(ExampleProvider)

        assert instance
        assert isinstance(instance, ExampleProvider)

    def test_should_instance_providers_with_local_dep_sorted(self):
        @Injectable()
        class ExampleDependency:
            def __init__(self) -> None:
                pass

        @Injectable()
        class ExampleDependant:  # noqa: B903
            def __init__(self, provider: ExampleDependency) -> None:
                self.provider = provider

        @Module(
            MetaModule(
                providers=[ExampleDependency, ExampleDependant],
                exports=[ExampleDependant],
            ),
        )
        class ExampleModule:
            pass

        container = Container(ExampleModule())
        container.build_container()
        instance = container.get_instance(ExampleDependant)

        assert instance
        assert isinstance(instance, ExampleDependant)
        assert isinstance(instance.provider, ExampleDependency)

    # @pytest.mark.skip
    def test_should_instance_providers_with_local_deps_unsorted(self):
        @Injectable()
        class A:
            def __init__(self) -> None:
                pass

        @Injectable()
        class B:
            def __init__(self, provider: A) -> None:
                pass

        @Injectable()
        class C:
            def __init__(self, provider: B) -> None:
                pass

        @Module(MetaModule(providers=[A, C, B], exports=[C]))
        class ExampleModule:
            pass

        container = Container(ExampleModule())
        container.build_container()
        instance = container.get_instance(C)

        assert instance
        assert isinstance(instance, C)
