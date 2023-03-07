
import json


class Iris:
    """
    Iris data class.
    """
    # Allowed attributes for class
    # accessed by self.__class__.annotations__ in code
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def __init__(self, row: dict):
        # Extract class attributes from input. If attribute not found, assign empty value with correct type.
        allowed_attributes = self.__class__.__annotations__
        for attribute, attribute_type in allowed_attributes.items():
            self.__setattr__(attribute, row.pop(attribute, attribute_type()))
        if len(row):
            raise Warning(f"Trying to create an instance of {self.__class__.__name__} with forbidden attributes. "
                          f"Ignored attributes: {', '.join(list(row.keys()))}. "
                          f"Only the following attributes are allowed: "
                          f"{', '.join(list(allowed_attributes.keys()))}")

    def __setattr__(self, key, value):
        # Only allow attributes defined in class variables.
        allowed_attributes = list(self.__class__.__annotations__.keys())
        if key in allowed_attributes:
            # Type the assigned value according to the type of attribute (float, int etc.)
            super().__setattr__(key, self.__class__.__annotations__[key](value))
        else:
            raise ValueError(f"Can't assign attribute '{key}' to class {self.__class__.__name__}. "
                             f"Only the following attributes are allowed: "
                             f"{', '.join(allowed_attributes)}")

    def __hash__(self):
        # Hash function to compare and get unique instances by converting to set
        return hash(json.dumps(self.as_dict(), sort_keys=True))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def as_dict(self):
        # Return all class attributes and values as dict.
        return {attribute: self.__getattribute__(attribute)
                for attribute in self.__class__.__annotations__}
