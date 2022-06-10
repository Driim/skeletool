import pytest
from src.module import MetaModule, Module


@pytest.fixture
def decorated_class_instance():
    @Module()
    class DecoratedClass:
        pass

    return DecoratedClass()


class TestModule:
    def test_decorated_class_has_meta(self, decorated_class_instance):
        assert isinstance(decorated_class_instance.__meta_module__, MetaModule)

    def test_decorated_class_has_correct_name(self, decorated_class_instance):
        assert decorated_class_instance.__class__.__name__ == "DecoratedClass"
