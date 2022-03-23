import pytest
from abc import ABC

from junifer.api.registry import register, get_step_names, get, build


def test_register_error():
    """Test register error"""
    with pytest.raises(ValueError, match='Invalid ste'):
        register('foo', 'bar', 'baz')


def test_gets():
    """Test get"""
    with pytest.raises(ValueError, match='Invalid ste'):
        get_step_names('foo')

    datagrabbers = get_step_names('datagrabber')
    assert 'bar' not in datagrabbers
    register('datagrabber', 'bar', 'baz')
    datagrabbers = get_step_names('datagrabber')
    assert 'bar' in datagrabbers

    with pytest.raises(ValueError, match='Invalid ste'):
        get('foo', 'bar')

    with pytest.raises(ValueError, match='Invalid name'):
        get('datagrabber', 'foo')

    obj = get('datagrabber', 'bar')
    assert obj == 'baz'


def test_build():
    """Test building objects from names"""
    import numpy as np

    class SuperClass(ABC):
        pass

    class ConcreteClass(SuperClass):
        def __init__(self, value=1):
            self.value = value

    register('datagrabber', 'concrete', ConcreteClass)

    obj = build('datagrabber', 'concrete', SuperClass)
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 1

    obj = build('datagrabber', 'concrete', SuperClass, {'value': 2})
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 2

    with pytest.raises(ValueError, match='Must inherit'):
        build('datagrabber', 'concrete', np.ndarray)
