
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

    def __eq__(self, other):
        """
        Two instances of Iris are equal if they have the same columns and the valus of all columns are equal.
        """
        if not isinstance(other, Iris):
            return False
        if len(self.__annotations__) != len(other.__annotations__):
            return False
        if not all(column in other.__annotations__ for column in self.__annotations__):
            return False
        if not all(self.__getattribute__(column) == other.__getattribute__(column) for column in self.__annotations__):
            return False
        return True

    def as_dict(self):
        return {column: self.__getattribute__(column) for column in self.__annotations__}

    def __hash__(self):
        # Hash function to get unique instances by converting to set
        return hash(json.dumps(self.as_dict(), sort_keys=True))
