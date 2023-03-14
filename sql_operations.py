
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
    Check if a table by the input name exists in SQLite
    :param table: Name of table to search for
    :param connection: SQLite connection object
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
    Creates a table in SQLite
    :param table: table name
    :param columns: A dict in the form of {column name: SQLite type name}
    :param connection: SQLite connection object.
    :return: None
    """
    sql_cursor = connection.cursor()
    columns_string = ",".join([f"{key} {value}" for key, value in columns.items()])
    sql_cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            {columns_string})
        """)
    connection.commit()
    return


def insert_row(table: str, connection: sqlite3.Connection, **kwargs) -> int:
    """
    Inserts a single row to a SQLite table
    :param table: Name of the table to insert to
    :param connection: SQLite connection object
    :param kwargs: Key-value (column name: value) pairs to insert
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


def parse_where_parameter(statement: str) -> tuple:
    """
    Take a single SQL-like "where"-statement and parse it to components.
    E.g. "column_name < 99" --> ("column_name", "<", "99")
    Supported operators: =, !=, <, >, IN
    :return: A tuple with the following values: (column_name, operator, value)
    """
    operators = ["=", "!=", "<", ">", r"\sin\s"]
    operators_pattern = '|'.join(operators)
    statement = statement.strip()

    column_pattern = re.compile(rf"^.+?(?=({operators_pattern}))", re.IGNORECASE)
    column_match = column_pattern.search(statement)
    if column_match:
        column = column_match.group(0).strip()
    else:
        raise ValueError(
            f"Can't parse the column name from the where statement. "
            f"Problematic statement: '{statement}'")

    operator_pattern = re.compile(operators_pattern, re.IGNORECASE)
    operator_match = operator_pattern.search(statement)
    if operator_match:
        operator_raw = operator_match.group(0)
        operator = operator_raw.strip()
    else:
        raise ValueError(
            f"Can't parse the operator part from the where statement. "
            f"Problematic statement: '{statement}'")

    value_pattern = re.compile(rf"^.+?{operator_raw}(.+$)", re.IGNORECASE)
    value_match = value_pattern.search(statement)
    if value_match:
        value = value_match.group(1).strip()
    else:
        raise ValueError(
            f"Can't parse a searchable value from the where statement. "
            f"Problematic statement: '{statement}'")

    return column, operator, value


def typecast_input_value(value: str) -> (int | float | str):
    """
    Typecast "where"-string value component from string to a more proper type
    :param value: "where"-string value component. E.g. 99 in "column_name < 99"
    :return: Int or float if value is convertible to number. Otherwise, returns input string.
    """
    try:                                                    # Convert to float if no error
        value = float(value)
    except ValueError:
        pass
    if isinstance(value, float) and value == int(value):    # Convert to int, if value doesn't change upon conversion
        value = int(value)
    return value


def parse_in_values(value: str) -> list:
    """
    Parses arguments of sql "IN" statement.
    E.g. '("virginica","setosa")' -> ['virginica', 'setosa']
    :param value: Value component from SQL "IN" statement
    :return: A list of parsed values
    """
    return [string.strip(r"'\"()") for string in value.split(",")]


def compile_where_statement(parsed_inputs: list[tuple]) -> tuple[str, list]:
    """
    Take a list of "where"-statements. Return a tuple in the following form:
    ("where"-string formatted with placeholders, list of corresponding values).
    E.g. [("column1", "<", 99), ("column2", "IN", ["value1", "value2"])] to
    ("WHERE column1 < ? AND column2 IN (?,?)", [99, "value1", "value2"] )
    :param parsed_inputs: List of parsed "where"-statements in the form of (column, operator, value)
    """
    statement_strings = list()
    values = list()
    for statement in parsed_inputs:
        if statement[1].lower() == "in":
            in_values = [typecast_input_value(value) for value in parse_in_values(statement[2])]
            placeholders = ','.join(["?"] * len(in_values))          # String in the form ?,?,?,...
            statement_strings += [f"{statement[0]} {statement[1]} ({placeholders})"]
            values += in_values
        else:
            statement_strings += [f"{statement[0]} {statement[1]} ?"]
            values += [typecast_input_value(statement[2])]
    where_string = f" WHERE {' AND '.join(statement_strings)}"
    return where_string, values


def read_table(table: str, connection: sqlite3.Connection, where: tuple = None) -> list[dict]:
    """
    Get rows from SQLite table. If no "where" argument is supplied, returns all data from table
    :param table: Name of table
    :param connection: SQLite connection object
    :param where: SQL-like "where"-statement. See sql_operations.parse_where_parameter for supported operators
    :return: List of dicts corresponding to the rows returned in the form of {column_name: value, ...}
    """
    sql_cursor = connection.cursor()
    # Add where statement values, if given
    sql_statement = f"SELECT * FROM {table};"
    where_values = tuple()
    if where:
        sql_statement = sql_statement.replace(";", f"{where[0]};")
        where_values = where[1]
    # Execute query
    response = sql_cursor.execute(sql_statement, where_values)
    data = response.fetchall()
    # Format the response as a list of dicts
    data_column_names = [item[0] for item in response.description]
    data_rows = list()
    for row in data:
        data_row = {key: value for key, value in zip(data_column_names, row)}
        data_rows += [data_row]
    return data_rows


def delete_rows(table: str, connection: sqlite3.Connection, where: tuple = 0) -> int:
    """
    Delete rows from SQLite table. If no "where" argument is supplied, no action is taken
    :param table: Name of table
    :param connection: SQLite connection object
    :param where: SQL-like "where"-statement. See sql_operations.parse_where_parameter for supported operators
    :return: Number of rows deleted
    """
    sql_cursor = connection.cursor()
    if isinstance(where, tuple) and len(where) > 1:             # Use parsed where statement if provided
        sql_statement = f"DELETE FROM {table} {where[0]};"
        where_values = where[1]
    elif where:                                                 # If where = True, delete all
        sql_statement = f"DELETE FROM {table};"
        where_values = tuple()
    else:                                                       # Default where input 0: no action
        sql_statement = f"DELETE FROM {table} WHERE 0;"
        where_values = tuple()

    response = sql_cursor.execute(sql_statement, where_values)
    n_deleted_rows = response.rowcount
    connection.commit()
    return n_deleted_rows


def get_columns(table: str, connection: sqlite3.Connection) -> dict:
    """
    Get column names of a SQLite table
    :param table: Name of table
    :param connection: SQLite connection object
    :return: Dict in the form {column name: column SQLite type}
    """
    sql_cursor = connection.cursor()
    sql_statement = f"PRAGMA table_info({table})"
    response = sql_cursor.execute(sql_statement)     # Gives tuples where 2nd and 3rd element is column name and type
    columns = {column[1]: column[2] for column in response.fetchall()}
    # Alternative without types
    # sql_statement = f"SELECT * FROM {table} WHERE 0;"
    # response = sql_cursor.execute(sql_statement)
    # column_names = [item[0] for item in response.description]
    return columns


def get_table_summary(rows: list) -> dict[dict]:
    """
    Get summary of each column in a table.
    Always gives the type of column and the number of total values and unique values.
    If the column type is numeric, includes minimum, maximum and median
    :param rows: A table represented as a list of dicts.
    :return: A nested summary dict in the following form:
    {column1: {type: str, n_total_values: 10, ...}, column2: {type: int, n_total_values: 22, ...}, ...}
    """
    if not rows:
        return dict()
    reference_object = rows[0]
    instance_variables = vars(reference_object)
    # Use class annotations to be able to handle reference objects where some variables are not set.
    class_annotations = list(reference_object.__class__.__annotations__.items())
    # Null table: table with only column names and empty values.
    null_table = len(rows) == 1 and not any([bool(value) for value in instance_variables.values()])

    summary = dict()
    for column_name, column_type in class_annotations:
        column_summary = dict()
        column_summary["type"] = column_type.__name__
        column_summary["n_total_values"] = 0        # Assume zero and overwrite later if not
        column_summary["n_unique_values"] = 0       # Assume zero and overwrite later if not
        if not null_table:
            values = [getattr(row, column_name) for row in rows]
            column_summary["n_total_values"] = len([value for value in values if value is not None])
            column_summary["n_unique_values"] = len(set(values))
            if column_type in (int, float):
                column_summary["minimum"] = sorted(values)[0]
                column_summary["maximum"] = sorted(values)[-1]
                column_summary["median"] = (sorted(values)[len(values) // 2] + sorted(values)[~len(values) // 2]) / 2
        summary[column_name] = column_summary
    return summary


def get_sql_type(python_type: str) -> str:
    """Get SQLite data type name that corresponds to input python data type name."""
    sql_type_reference = {
        "int": "INTEGER",
        "float": "REAL",
        "str": "TEXT",
        "NoneType": "NULL"}
    return sql_type_reference.get(python_type, "BLOB")


def get_python_type(sql_type: str, blob_type: str = str) -> type:
    """
    Get python data type from SQLite type
    :param sql_type: Name of SQLite type to convert
    :param blob_type: Python type for SQLite BLOB type
    :return: Python type object corresponding to input SQLite type
    """
    python_type_reference = {
        "INTEGER": int,
        "REAL": float,
        "TEXT": str,
        "NULL": type(None)}
    return python_type_reference.get(sql_type.upper(), blob_type)


def get_connection(path: str) -> sqlite3.Connection:
    """
    Get SQLite connection to a given database path.
    If database doesn't exist, creates a new database and path directories to it (unless path is :memory:).
    :param path: Path to SQLite database
    :return: sqlite3 Connection object to input path
    """
    if path != ":memory:":
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
    connection = sqlite3.connect(path)
    return connection


############################
# SQLite interface classes #
############################

class SqlTableInterface:
    """
    Interface class for SQLite operations on a single table.
    Connects to an existing table or creates it if it doesn't exist.

    Instance attributes:
    name: Table name in SQLite
    columns: Dict with columns to initiate in the table. {column1 name: column1 python type, ...}
    connection: sqlite3 Connection object to the database
    """

    def __init__(self, name: str, columns: dict, connection: sqlite3.Connection) -> None:
        self.name = name
        self.columns = {column_name: get_sql_type(column_type) for column_name, column_type in columns.items()}
        self.connection = connection

        create_table(
            table=self.name,
            columns=self.columns,
            connection=self.connection)

    def insert(self, **kwargs) -> int:
        """Insert a row to the table. Returns the number of rows inserted (0 or 1)"""
        n_rows_inserted = insert_row(
            table=self.name,
            connection=self.connection,
            **kwargs)
        return n_rows_inserted

    def select(self, where: (str | list[str]) = None) -> list[dict]:
        """
        Get data from the table.
        Data is filtered if "where"-statements are given. Otherwise, all data from the table is returned.
        :param where: "where"-statements. A single string or a list of strings. E.g. "WHERE column1 != 'red'"
        :return: Selected data
        """
        if where:               # Parse where inputs
            where = [where] if not isinstance(where, list) else where          # Make sure where variable is a list
            where_parsed = [parse_where_parameter(parameter) for parameter in where]
            where_statement, where_values = compile_where_statement(where_parsed)
            where = (where_statement, where_values)
        # Read
        result = read_table(
            table=self.name,
            connection=self.connection,
            where=where)
        return result

    def delete(self, where: (str | list[str]) = 0):
        """
        Delete data from the table.
        Selected rows are deleted if "where"-statements are given. No action if no "where"-statement is given.
        :param where: "where"-statements. A single string or a list of strings. E.g. "WHERE column1 != 'red'"
        :return: Number of rows deleted
        """
        if where:               # Parse where inputs
            where = [where] if not isinstance(where, list) else where           # Make sure where variable is a list
            where_parsed = [parse_where_parameter(parameter) for parameter in where]
            where_statement, where_values = compile_where_statement(where_parsed)
            where = (where_statement, where_values)

        n_deleted_rows = delete_rows(
            table=self.name,
            connection=self.connection,
            where=where)
        return n_deleted_rows


class SqlIrisInterface(SqlTableInterface):
    """
    Interface class for SQLite operations on a table for data from Iris class.
    Connects to an existing table or creates it if it doesn't exist.
    """
    type_class = Iris
    name = type_class.__name__
    # Type names for class columns
    columns_python_types = {column_name: column_type.__name__ for
                            column_name, column_type in type_class.__annotations__.items()}

    def __init__(self, connection: sqlite3.Connection) -> None:
        SqlTableInterface.__init__(
            self,
            name=self.name,
            columns=self.columns_python_types,
            connection=connection)

    def select_iris(self, where: (str | list[str]) = None) -> list[Iris]:
        """
        Get sql data with items formatted to the Iris class.
        Data is filtered if "where"-statements are given. Otherwise, all data from the table is returned.
        :param where: "where"-statements. A single string or a list of strings. E.g. "WHERE species != 'virginica'"
        :return: A list of Iris objects corresponding to returned rows
        """
        data_raw = self.select(where=where)
        data_iris = list()
        for row in data_raw:        # Typecast data to Iris class
            data_iris += [self.type_class(**row)]
        return data_iris

    def insert_iris(self, data: list[Iris], unique: bool = False):
        """
        Inserts Iris objects to SQLite.
        Uses list input to avoid redundant comparisons for every insertion.
        :param data: List of Iris object corresponding to rows to insert
        :param unique: Only non-existing rows are inserted if True. Data is also deduplicated before inserting if True.
        :return: Total number of rows inserted.
        """
        n_rows_inserted = 0
        if unique:
            existing_data = self.select_iris()
            # deduplicate input data and insert rows that are not yet present.
            for row in set(data):
                if row not in existing_data:
                    n_rows_inserted += self.insert(**row.as_dict())
        else:
            for row in data:
                n_rows_inserted += self.insert(**row.as_dict())
        return n_rows_inserted

    def summary(self) -> dict[dict]:
        """Return a nested dict with summary info for each column in the SQLite table."""
        data = self.select_iris()
        if not data:          # Handle cases where table has no content - create an empty Iris object
            sql_columns = get_columns(table=self.name, connection=self.connection)
            data = [self.type_class(**{column: get_python_type(sql_type)() for column, sql_type in sql_columns.items()})]
        summary = get_table_summary(data)
        return summary
