
import json


class Iris:
    """
    Data class for iris data.
    """
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def __init__(self, row):
        self.sepal_length = float(row["sepal_length"])
        self.sepal_width = float(row["sepal_width"])
        self.petal_length = float(row["petal_length"])
        self.petal_width = float(row["petal_width"])
        self.species = str(row["species"])

    def __setattr__(self, key, value):
        # Only allow variables defined in class variables.
        allowed_variables = [column_name for column_name in self.__class__.__annotations__.keys()]
        if key in allowed_variables:
            super().__setattr__(key, value)
        else:
            raise ValueError(f"Can't assign attribute {key} to class {self.__class__.__name__}. "
                             f"Only the following attributes are allowed: "
                             f"{', '.join(allowed_variables)}")

    def __hash__(self):
        # Hash function to compare and get unique instances by converting to set
        return hash(json.dumps(self.as_dict(), sort_keys=True))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def as_dict(self):
        return {column: self.__getattribute__(column) for column in self.__annotations__}
