
# standard
import csv
import json
# local
import log


###########
# Classes #
###########

class Iris:
    """Data class for iris objects - i.e. for rows from iris data."""

    # Allowed attributes for class
    # accessed by self.__class__.annotations__ in code
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def __init__(self, **kwargs):
        """Extract class attributes from input. If attribute is not found, assign empty value with correct type."""
        allowed_attributes = self.__class__.__annotations__
        for attribute, attribute_type in allowed_attributes.items():
            self.__setattr__(attribute, kwargs.pop(attribute, attribute_type()))
        if len(kwargs):
            log_entry = log.ForbiddenAttributes(
                exception=Warning(),
                class_name=self.__class__.__name__,
                received_attributes=list(kwargs.keys()),
                allowed_attributes=allowed_attributes)
            log_entry.record("WARNING")

    def __setattr__(self, key, value):
        """Only allow attributes defined in class variables."""
        allowed_attributes = self.__class__.__annotations__
        problem_keys = list()
        if key in allowed_attributes:
            # Typecast the assigned value according to the type of the class attribute (float, int etc.)
            typed_value = allowed_attributes[key](value) if value else allowed_attributes[key]()
            super().__setattr__(key, typed_value)
        else:
            problem_keys += [key]
        if len(problem_keys):
            log_entry = log.ForbiddenAttributes(
                exception=Warning(),
                class_name=self.__class__.__name__,
                received_attributes=problem_keys,
                allowed_attributes=allowed_attributes)
            log_entry.record("WARNING")

    def __hash__(self):
        """Hash function to compare and get unique instances of Iris by using a set"""
        return hash(json.dumps(self.as_dict(), sort_keys=True))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        values = [f"{attribute}: {self.__getattribute__(attribute)}" for attribute in self.__class__.__annotations__]
        return ", ".join(values)

    def as_dict(self) -> dict:
        """Return all class attributes (i.e. columns) and their values as a dict."""
        return {attribute: self.__getattribute__(attribute)
                for attribute in self.__class__.__annotations__}


#############
# Functions #
#############

def from_csv(data: str) -> list[Iris]:
    """
    Parse Iris objects from csv data
    :param data: Iris data in csv format
    :return: List of Iris objects, representing the rows of the data.
    """
    data_raw = csv.DictReader(data.splitlines())
    iris_data = list()
    for row in data_raw:
        iris_data += [Iris(**row)]
    return iris_data


def from_json(data: list) -> list[Iris]:
    """
    Parse Iris objects from json data
    :param data: Iris data in json (i.e. dict) format
    :return: List of Iris objects, representing the rows of the data.
    """
    return [Iris(**row) for row in data]
