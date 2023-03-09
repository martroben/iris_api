
# standard
import csv
import json


###########
# Classes #
###########

class Iris:
    # Allowed attributes for class
    # accessed by self.__class__.annotations__ in code
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def __init__(self, **kwargs):
        """Extract class attributes from input. If attribute not found, assign empty value with correct type."""
        allowed_attributes = self.__class__.__annotations__
        for attribute, attribute_type in allowed_attributes.items():
            self.__setattr__(attribute, kwargs.pop(attribute, attribute_type()))
        if len(kwargs):
            raise Warning(f"Forbidden attributes were not assigned to an instance of class {self.__class__.__name__}. "
                          f"Forbidden attributes: {', '.join(list(kwargs.keys()))}. "
                          f"Only the following attributes are allowed: "
                          f"{', '.join(list(allowed_attributes.keys()))}.")

    def __setattr__(self, key, value):
        """Only allow attributes defined in class variables."""
        allowed_attributes = self.__class__.__annotations__
        if key in allowed_attributes:
            # Type the assigned value according to the type of attribute (float, int etc.)
            super().__setattr__(key, allowed_attributes[key](value))
        else:
            raise ValueError(f"Can't assign attribute '{key}' to class {self.__class__.__name__}. "
                             f"Only the following attributes are allowed: "
                             f"{', '.join(allowed_attributes)}")

    def __hash__(self):
        """Hash function to compare and get unique instances by converting to set"""
        return hash(json.dumps(self.as_dict(), sort_keys=True))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def as_dict(self):
        """Return all class attributes and values as dict."""
        return {attribute: self.__getattribute__(attribute)
                for attribute in self.__class__.__annotations__}


#############
# Functions #
#############

def parse_data(csv_data: str) -> list[Iris]:
    data_raw = csv.DictReader(csv_data.splitlines())
    data = list()
    for row in data_raw:
        data += [Iris(**row)]
    return data
