import pytest
from src.injectable import Injectable, Scope


@pytest.fixture
def injectable_class():
    @Injectable()
    class InjectableClass:
        pass

    return InjectableClass()


class TestInjectable:
    def test_decorated_class_has_scope(self, injectable_class):
        assert isinstance(injectable_class.__meta_scope__, Scope)

    def test_decorated_class_has_correct_name(self, injectable_class):
        assert injectable_class.__class__.__name__ == "InjectableClass"
