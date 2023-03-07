
import pytest
import iris


def null_initiation():
    iris.Iris({})


def partial_initiation():
    iris.Iris({
        "sepal_length": 111,
        "species": "Iris species name"})



