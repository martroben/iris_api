# standard
import os
import re
import sqlite3
# local
from iris import Iris


#############
# Functions #
#############

def table_exists(table: str, connection: sqlite3.Connection) -> bool:
    """
    Check if table exists in SQLite.
    :param table: Table name to search.
    :param connection: SQL connection object.
    :return: True/False whether the table exists
    """
    sql_cursor = connection.cursor()
    query_result = sql_cursor.execute(
        f"""
        SELECT EXISTS
            (SELECT name FROM sqlite_master
            WHERE type='table' AND name='{table}');
        """)
    table_found = bool(query_result.fetchone()[0])
    return table_found


def create_table(table: str, columns: dict, connection: sqlite3.Connection) -> None:
    """
    Creates table in SQLite
    :param table: table name
    :param columns: A dict in the form of {column name: column type}
    :param connection: SQL connection object.
    :return: None
    """
    sql_cursor = connection.cursor()
    column_typenames = {column_name: get_sqlite_data_type(column_type)
                        for column_name, column_type in columns.items()}
    columns_string = ",".join([f"{key} {value}" for key, value in column_typenames.items()])
    sql_cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            {columns_string})
        """)
    connection.commit()
    return


def read_table(table: str, connection: sqlite3.Connection,
               where: (tuple|list[tuple]) = ("", "", "")) -> list[dict]:
    """
    Get data from a SQL table.
    :param table: SQL table name.
    :param connection: SQL connection.
    :param where: Optional SQL WHERE filtering clause: e.g. column = value or column IN (1,2,3).
    Input has to be a 3-tuple: (column_name, operator, value). E.g. ("year", "in", "(1985, 1986)")
    :return: A list of column_name:value dicts.
    """
    sql_cursor = connection.cursor()
    sql_statement = f"SELECT * FROM {table}"
    ####################### Parse multiple where statements and join by AND
    if all(where):                      # Add where statement if it's included in input
        sql_statement.replace(";", f" WHERE {where[0]} {where[1]} :where;")
    response = sql_cursor.execute(sql_statement, {"where": where[2]})

    data = response.fetchall()
    data_column_names = [item[0] for item in response.description]
    data_rows = list()
    for row in data:
        data_row = {key: value for key, value in zip(data_column_names, row)}
        data_rows += [data_row]
    return data_rows


def insert_row(table: str, connection: sqlite3.Connection, **kwargs) -> int:
    """
    Inserts a Listing to SQL table.
    :param table: Name of SQL table where the data should be inserted to.
    :param connection: SQL connection object.
    :param kwargs: Key-value pairs to insert.
    :return: Number of rows inserted (1 or 0)
    """
    sql_cursor = connection.cursor()
    column_names = list()
    values = tuple()
    for column_name, value in kwargs.items():
        column_names += [column_name]
        values += (value,)
    column_names_string = ",".join(column_names)
    placeholder_string = ", ".join(["?"] * len(column_names))  # As many placeholders as columns. E.g (?, ?, ?, ?)

    sql_cursor.execute(
        f"""
        INSERT INTO {table}
            ({column_names_string})
        VALUES
            ({placeholder_string});
        """,
        values)
    connection.commit()
    return sql_cursor.rowcount


def get_table_summary(rows: list) -> dict[dict]:
    """
    Get summary of each column in a table (list of rows).
    Always gives type of variable and the number of total values and unique values.
    If the variable is numeric, includes minimum, maximum and median.
    """
    summary = dict()
    reference_object = rows[0]
    # Use class annotations to account for reference objects where some variables are not set.
    for column_name, column_type in reference_object.__class__.__annotations__.items():
        column_summary = dict()
        values = [row.__getattribute__(column_name) for row in rows]
        column_summary["type"] = column_type.__name__
        column_summary["n_total_values"] = len([value for value in values if value is not None])
        column_summary["n_unique_values"] = len(set(values))
        if column_type in (int, float):
            column_summary["minimum"] = sorted(values)[0]
            column_summary["maximum"] = sorted(values)[-1]
            column_summary["median"] = (sorted(values)[len(values) // 2] + sorted(values)[~len(values) // 2]) / 2
        summary[column_name] = column_summary
    return summary


def get_sqlite_data_type(type_name: str) -> str:
    """
    Get SQLite data type by python type name.
    :param type_name: Class type object (from class __annotations__).
    :return: SQLite data type of that corresponds to Python class.
    """
    type_name = type_name
    if type_name == "int":
        return "INTEGER"
    elif type_name == "float":
        return "REAL"
    elif type_name == "str":
        return "TEXT"
    elif type_name == "NoneType":
        return "NULL"
    else:
        return "BLOB"


def get_connection(path: str) -> sqlite3.Connection:
    # Create directories for database if they don't exist
    if path != ":memory:":
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    connection = sqlite3.connect(path)
    return connection


def parse_where_statement(statement: str) -> tuple:
    operators = ["=", "!=", "<", ">", r"\sin\s"]
    operators_pattern = '|'.join(operators)
    statement = statement.strip()

    column_pattern = re.compile(rf"^.+?(?=({operators_pattern}))", re.IGNORECASE)
    column_match = column_pattern.search(statement)
    if column_match:
        column = column_match.group(0).strip()
    else:
        raise ValueError(f"Couldn't parse column name from sql where statement! Statement: {statement}")

    operator_pattern = re.compile(operators_pattern, re.IGNORECASE)
    operator_match = operator_pattern.search(statement)
    if operator_match:
        operator_raw = operator_match.group(0)
        operator = operator_raw.strip()
    else:
        raise ValueError(f"Couldn't parse operator from sql where statement! Statement: {statement}")

    value_pattern = re.compile(rf"^.+?{operator_raw}(.+$)", re.IGNORECASE)
    value_match = value_pattern.search(statement)
    if value_match:
        value = value_match.group(1).strip()
    else:
        raise ValueError(f"Couldn't parse search value from sql where statement! Statement: {statement}")

    return column, operator, value


###########
# Classes #
###########

class SqlTableInterface:
    """
    Interface class for SQL operations on a single table.
    """

    def __init__(self, name: str, columns: dict, connection: sqlite3.Connection) -> None:
        self.name = name
        self.columns = columns
        self.connection = connection

        create_table(
            table=self.name,
            columns=self.columns,
            connection=self.connection)

    def select(self, where: tuple = ("", "", "")) -> list[dict]:
        result = read_table(
            table=self.name,
            connection=self.connection,
            where=where)
        return result

    def insert(self, **kwargs) -> int:
        n_rows_inserted = insert_row(
            table=self.name,
            connection=self.connection,
            **kwargs)
        return n_rows_inserted


class SqlIrisInterface(SqlTableInterface):
    name = "Iris"
    type_class = Iris
    columns = {key: get_sqlite_data_type(column_type.__name__)
               for key, column_type in type_class.__annotations__.items()}

    def __init__(self, connection: sqlite3.Connection) -> None:
        SqlTableInterface.__init__(
            self,
            name=self.name,
            columns=self.columns,
            connection=connection)

    def select_iris(self, where: tuple = ("", "", "")) -> list[Iris]:
        # Returns sql data with items formatted as the Iris class.
        data_raw = self.select(where=where)
        data_iris = list()
        for row in data_raw:
            data_iris += [self.type_class(**row)]
        return data_iris

    def insert_unique(self, data: list[Iris]):
        """
        Inserts Iris objects to sql only if it is not yet present in the table.
        Uses list input to avoid redundant comparisons for every insertion.
        Returns total number of rows inserted.
        """
        existing_data = self.select_iris()
        # deduplicate input data and insert rows that are not yet present.
        n_rows_inserted = 0
        for row in set(data):
            if row not in existing_data:
                n_rows_inserted += self.insert(**row.as_dict())
        return n_rows_inserted

    def summary(self) -> dict[dict]:
        # Return a nested dict with summary of data in the table.
        return get_table_summary(self.select_iris())
