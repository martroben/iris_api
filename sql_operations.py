
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


def parse_where_parameter(statement: str) -> tuple:
    operators = ["=", "!=", "<", ">", r"\sin\s"]
    operators_pattern = '|'.join(operators)
    statement = statement.strip()

    column_pattern = re.compile(rf"^.+?(?=({operators_pattern}))", re.IGNORECASE)
    column_match = column_pattern.search(statement)
    if column_match:
        column = column_match.group(0).strip()
    else:
        raise ValueError(f"Can't parse the column name from the where statement. "
                         f"Problematic statement: '{statement}'")

    operator_pattern = re.compile(operators_pattern, re.IGNORECASE)
    operator_match = operator_pattern.search(statement)
    if operator_match:
        operator_raw = operator_match.group(0)
        operator = operator_raw.strip()
    else:
        raise ValueError(f"Can't parse the operator part from the where statement. "
                         f"Problematic statement: '{statement}'")

    value_pattern = re.compile(rf"^.+?{operator_raw}(.+$)", re.IGNORECASE)
    value_match = value_pattern.search(statement)
    if value_match:
        value = value_match.group(1).strip()
    else:
        raise ValueError(f"Can't parse a searchable value from the where statement. "
                         f"Problematic statement: '{statement}'")

    return column, operator, value


def typecast_input_value(value: str):
    """
    Typecast where string input value from string to a more proper type
    :param value:
    :return:
    """
    # Convert to float if no error
    try:
        value = float(value)
    except ValueError:
        pass
    # Convert to int, if value doesn't change upon conversion
    if isinstance(value, float) and value == int(value):
        value = int(value)
    return value


def parse_in_values(value: str) -> list:
    """
    Parses arguments for sql "IN" statement.
    E.g. '("virginica","setosa")' -> ['virginica', 'setosa']
    :param value: Values for sql "IN" statement
    :return: A list of parsed parameters
    """
    return [string.strip(r"'\"()") for string in value.split(",")]


def compile_where_statement(parsed_inputs: list[tuple]) -> tuple[str, list]:
    statement_strings = list()
    values = list()
    for statement in parsed_inputs:
        print(statement)
        if statement[1].lower() == "in":
            in_values = [typecast_input_value(value) for value in parse_in_values(statement[2])]
            placeholders = ','.join(['?'] * len(in_values))          # String in the form ?,?,?,...
            statement_strings += [f"{statement[0]} {statement[1]} ({placeholders})"]
            values += in_values
        else:
            statement_strings += [f"{statement[0]} {statement[1]} ?"]
            values += [typecast_input_value(statement[2])]
    where_string = f" WHERE {' AND '.join(statement_strings)}"
    return where_string, values


def read_table(table: str, connection: sqlite3.Connection, where: tuple = None) -> list[dict]:
    """
    If no where argument is supplied, returns all data.
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
    """
    sql_cursor = connection.cursor()
    if isinstance(where, tuple) and len(where) > 1:     # Use parsed where statement if provided
        sql_statement = f"DELETE FROM {table} {where[0]};"
        where_values = where[1]
    elif where:                                         # If where = True, delete all
        sql_statement = f"DELETE FROM {table};"
        where_values = tuple()
    else:                                               # Default input 0: no action
        sql_statement = f"DELETE FROM {table} WHERE 0;"
        where_values = tuple()
    # Execute query
    response = sql_cursor.execute(sql_statement, where_values)
    n_deleted_rows = response.rowcount
    connection.commit()
    return n_deleted_rows


def get_columns(table: str, connection: sqlite3.Connection) -> list:
    sql_cursor = connection.cursor()
    sql_statement = f"SELECT * FROM {table} WHERE 0;"
    response = sql_cursor.execute(sql_statement)
    column_names = [item[0] for item in response.description]
    return column_names


def get_table_summary(rows: list) -> dict[dict]:
    """
    Get summary of each column in a table (list of rows).
    Always gives type of variable and the number of total values and unique values.
    If the variable is numeric, includes minimum, maximum and median.
    """
    if not rows:
        return dict()
    reference_object = rows[0]
    instance_variables = vars(reference_object)
    # Use class annotations to handle reference objects where some variables are not set.
    class_annotations = list(reference_object.__class__.__annotations__.items())
    # Handle tables with only column names and empty values
    null_table = len(rows) == 1 and not any([bool(value) for value in instance_variables.values()])

    summary = dict()
    for column_name, column_type in class_annotations:
        column_summary = dict()
        column_summary["type"] = column_type.__name__
        column_summary["n_total_values"] = 0        # Assume zero and overwrite if not
        column_summary["n_unique_values"] = 0       # Assume zero and overwrite if not
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

    def insert(self, **kwargs) -> int:
        n_rows_inserted = insert_row(
            table=self.name,
            connection=self.connection,
            **kwargs)
        return n_rows_inserted

    def select(self, where: (str | list[str]) = None) -> list[dict]:
        # Parse where inputs
        if where:
            where = [where] if not isinstance(where, list) else where  # Make sure where variable is a list
            where_parsed = [parse_where_parameter(parameter) for parameter in where]
            where_statement, where_values = compile_where_statement(where_parsed)
            where = (where_statement, where_values)

        result = read_table(
            table=self.name,
            connection=self.connection,
            where=where)
        return result

    def delete(self, where: (str | list[str]) = 0):
        # Parse where inputs
        if where:
            where = [where] if not isinstance(where, list) else where  # Make sure where variable is a list
            where_parsed = [parse_where_parameter(parameter) for parameter in where]
            where_statement, where_values = compile_where_statement(where_parsed)
            where = (where_statement, where_values)

        result = delete_rows(
            table=self.name,
            connection=self.connection,
            where=where)
        return result


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

    def select_iris(self, where: (str | list[str]) = None) -> list[Iris]:
        """
        Get sql data with items formatted to the Iris class.
        :param where:
        :return:
        """
        data_raw = self.select(where=where)
        # Typecast data to class Iris
        data_iris = list()
        for row in data_raw:
            data_iris += [self.type_class(**row)]
        return data_iris

    def insert_iris(self, data: list[Iris], unique: bool = False):
        """
        Inserts Iris objects to sql only if it is not yet present in the table.
        Uses list input to avoid redundant comparisons for every insertion.
        Returns total number of rows inserted.
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
        # Return a nested dict with summary of data in the table.
        data = self.select_iris()
        if not data:                                                       # Handle cases where table has no content
            columns = get_columns(
                table=self.name,
                connection=self.connection)
            data = [self.type_class(**{column: str() for column in columns})]     # Include variable type info
        summary = get_table_summary(data)
        return summary
