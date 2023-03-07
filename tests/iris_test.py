
import pytest
import iris


def test_null_initiation():
    null_iris = iris.Iris()
    assert null_iris.petal_length == 0
    assert isinstance(null_iris.petal_length, float)


def test_partial_initiation():
    partial_iris = iris.Iris(
        sepal_length=111,
        species="Iris species name")
    assert partial_iris.sepal_length == 111
    assert isinstance(partial_iris.sepal_length, float)
    assert partial_iris.petal_length == 0
    assert isinstance(partial_iris.petal_length, float)
    assert partial_iris.species == "Iris species name"
    assert isinstance(partial_iris.species, str)


def test_full_initiation():
    full_iris = iris.Iris(
        sepal_length=111,
        sepal_width=222,
        petal_length=333,
        petal_width=444,
        species="Iris species name")
    assert full_iris.sepal_length == 111
    assert full_iris.sepal_width == 222
    assert full_iris.petal_length == 333
    assert full_iris.petal_width == 444
    assert full_iris.species == "Iris species name"


def test_forbidden_initiation_warning():
    with pytest.raises(Warning):
        iris.Iris(
            sepal_length=111,
            sepal_width=222,
            petal_length=333,
            petal_width=444,
            species="Iris species name",
            forbidden_attribute=555)


def test_forbidden_initiation_ignore():
    with pytest.raises(Warning):
        full_iris = iris.Iris(
            sepal_length=111,
            sepal_width=222,
            petal_length=333,
            petal_width=444,
            species="Iris species name",
            forbidden_attribute=555)
        assert len(full_iris.__annotations__) == 5


def test_forbidden_assignment():
    null_iris = iris.Iris()
    with pytest.raises(ValueError):
        null_iris.forbidden_attribute = 111


def test_dict_representation():
    full_iris_dict = {
        "sepal_length": 111,
        "sepal_width": 222,
        "petal_length": 333,
        "petal_width": 444,
        "species": "Iris species name"}
    full_iris = iris.Iris(**full_iris_dict)
    assert full_iris.as_dict() == full_iris_dict


def test_equality():
    full_iris_dict = {
        "sepal_length": 111,
        "sepal_width": 222,
        "petal_length": 333,
        "petal_width": 444,
        "species": "Iris species name"}
    iris1 = iris.Iris(**full_iris_dict)

    iris2 = iris.Iris(
        sepal_length="111",
        sepal_width=222.0,
        petal_length=333,
        petal_width=444,
        species="Iris species name")
    assert iris1 == iris2
