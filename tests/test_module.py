import pytest
from src.module import MetaModule, Module


@pytest.fixture
def decorated_class():
    @Module()
    class DecoratedClass:
        pass

    return DecoratedClass()


class TestModule:
    def test_decorated_class_has_meta(self, decorated_class):
        assert isinstance(decorated_class.__meta_module__, MetaModule)

    def test_decorated_class_has_correct_name(self, decorated_class):
        assert decorated_class.__class__.__name__ == 'DecoratedClass'