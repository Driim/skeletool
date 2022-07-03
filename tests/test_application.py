import pytest
from src.application import Application, ApplicationException
from src.injectable import Injectable
from src.module import MetaModule, Module


class TestApplication:
    def test_raise_if_not_module(self):
        with pytest.raises(ApplicationException):

            def func():
                pass

            Application(func)

    def test_should_resolve_providers(self):
        @Injectable()
        class ExampleProvider:
            def check(self) -> bool:
                return True

        @Module(MetaModule(providers=[ExampleProvider], exports=[ExampleProvider]))
        class ExampleModule:
            pass

        app = Application(ExampleModule)
        provider = app.resolve(ExampleProvider)

        assert provider
        assert isinstance(provider, ExampleProvider)
