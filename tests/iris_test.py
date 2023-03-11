
import csv
import json
import pytest
import iris

null_iris = iris.Iris()

partial_iris = iris.Iris(
    sepal_length=111,
    species="Iris species name")

full_iris = iris.Iris(
    sepal_length=111,
    sepal_width=222,
    petal_length=333,
    petal_width=444,
    species="Iris species name")

full_iris_dict = {
    "sepal_length": 111,
    "sepal_width": 222,
    "petal_length": 333,
    "petal_width": 444,
    "species": "Iris species name"}

full_iris_dict2 = {
    "sepal_length": 1111,
    "sepal_width": 2222,
    "petal_length": 3333,
    "petal_width": 4444,
    "species": "Iris species name2"}

partial_iris_dict = {
    "sepal_length": 111,
    "petal_width": 444,
    "species": "Iris species name"}

forbidden_iris_dict = {
    "sepal_length": 1111,
    "sepal_width": 2222,
    "petal_length": 3333,
    "petal_width": 4444,
    "species": "Iris species name",
    "forbidden_attribute": 555}

full_iris_csv = """\
sepal_length,sepal_width,petal_length,petal_width,species
111,222,333,444,Iris species name
1111,2222,3333,4444,Iris species name2\
"""

partial_iris_csv = """\
sepal_length,petal_length,species
111,333,Iris species name
1111,3333,Iris species name2\
"""

forbidden_iris_csv = """\
sepal_length,sepal_width,petal_length,petal_width,species,forbidden_column
111,222,333,444,Iris species name,Forbidden value1
1111,2222,3333,4444,Iris species name2,Forbidden value2\
"""


def test_null_initiation():
    assert null_iris.petal_length == 0
    assert isinstance(null_iris.petal_length, float)


def test_partial_initiation():
    assert partial_iris.sepal_length == 111
    assert isinstance(partial_iris.sepal_length, float)
    assert partial_iris.petal_length == 0
    assert isinstance(partial_iris.petal_length, float)
    assert partial_iris.species == "Iris species name"
    assert isinstance(partial_iris.species, str)


def test_full_initiation():
    assert full_iris.sepal_length == 111
    assert full_iris.sepal_width == 222
    assert full_iris.petal_length == 333
    assert full_iris.petal_width == 444
    assert full_iris.species == "Iris species name"


def test_forbidden_initiation_warning():
    with pytest.warns(Warning):
        iris.Iris(
            sepal_length=111,
            sepal_width=222,
            petal_length=333,
            petal_width=444,
            species="Iris species name",
            forbidden_attribute=555)


def test_forbidden_initiation_ignore():
    with pytest.warns(Warning):
        forbidden_iris = iris.Iris(
            sepal_length=111,
            sepal_width=222,
            petal_length=333,
            petal_width=444,
            species="Iris species name",
            forbidden_attribute=555)
        assert len(forbidden_iris.__annotations__) == 5


def test_forbidden_assignment():
    with pytest.raises(ValueError):
        null_iris.forbidden_attribute = 111


def test_dict_representation():
    full_iris_parsed = iris.Iris(**full_iris_dict)
    assert full_iris_parsed.as_dict() == full_iris_dict


def test_equality():
    iris1 = iris.Iris(**full_iris_dict)
    iris2 = iris.Iris(
        sepal_length="111",
        sepal_width=222.0,
        petal_length=333,
        petal_width=444,
        species="Iris species name")
    assert iris1 == iris2


def test_load_from_csv():
    iris_list = iris.from_csv(full_iris_csv)
    iris1_reference = {
        "sepal_length": 111,
        "sepal_width": 222,
        "petal_length": 333,
        "petal_width": 444,
        "species": "Iris species name"}
    iris2_reference = {
        "sepal_length": 1111,
        "sepal_width": 2222,
        "petal_length": 3333,
        "petal_width": 4444,
        "species": "Iris species name2"}
    assert iris_list[0].as_dict() == iris1_reference
    assert iris_list[1].as_dict() == iris2_reference


def test_load_from_csv_partial():
    iris_list = iris.from_csv(partial_iris_csv)
    iris1_reference = {
        "sepal_length": 111,
        "sepal_width": float(),
        "petal_length": 333,
        "petal_width": float(),
        "species": "Iris species name"}
    iris2_reference = {
        "sepal_length": 1111,
        "sepal_width": float(),
        "petal_length": 3333,
        "petal_width": float(),
        "species": "Iris species name2"}
    assert iris_list[0].as_dict() == iris1_reference
    assert iris_list[1].as_dict() == iris2_reference


def test_load_from_csv_forbidden():
    with pytest.warns(Warning):
        iris_list = iris.from_csv(forbidden_iris_csv)
        assert len(iris_list) == 2


def test_load_from_json():
    test_json_string = json.dumps([full_iris_dict, full_iris_dict2])
    iris_list = iris.from_json(test_json_string)
    assert iris_list[0].as_dict() == full_iris_dict
    assert iris_list[1].as_dict() == full_iris_dict2


def test_load_from_json_partial():
    test_json_string = json.dumps([full_iris_dict, partial_iris_dict])
    iris_list = iris.from_json(test_json_string)
    partial_iris_dict_dump = {key: value for key, value in iris_list[1].as_dict().items() if value}
    assert iris_list[0].as_dict() == full_iris_dict
    assert partial_iris_dict_dump == partial_iris_dict


def test_load_from_json_forbidden():
    with pytest.warns(Warning):
        test_json_string = json.dumps([full_iris_dict, forbidden_iris_dict])
        iris_list = iris.from_json(test_json_string)
        assert len(iris_list) == 2
