
import sqlite3


class SqlTableInterface:
    """
    Interface class for SQL operations on a single table.
    """
    def __init__(self, name: str, columns: dict, connection: sqlite3.Connection):
        self.name = name
        self.columns = columns
        self.connection = connection
        self.setup()

    def setup(self):
        # Check if table exists and create if it doesn't.
        if not table_exists(self.name, self.connection):
            create_table(
                table=self.name,
                columns=self.columns,
                connection=self.connection)

    def insert(self, **kwargs) -> None:
        insert_row(
            table=self.name,
            connection=self.connection,
            **kwargs)


def table_exists(table: str, connection: sqlite3.Connection) -> bool:
    """
    Check if table exists in SQLite.
    :param table: Table name to search.
    :param connection: SQL connection object.
    :return: True/False whether the table exists
    """
    check_table_query = f"SELECT EXISTS (SELECT name FROM sqlite_master WHERE type='table' AND name='{table}');"
    sql_cursor = connection.cursor()
    query_result = sql_cursor.execute(check_table_query)
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
    column_typenames = {key: get_sqlite_data_type(value) for key, value in columns.items()}
    columns_string = ",\n\t".join([f"{key} {value}" for key, value in column_typenames.items()])
    create_table_command = f"CREATE TABLE {table} (\n\t{columns_string}\n);"
    sql_cursor = connection.cursor()
    sql_cursor.execute(create_table_command)
    connection.commit()
    return


def insert_row(table: str, connection: sqlite3.Connection, **kwargs) -> None:
    """
    Inserts a Listing to SQL table.
    :param table: Name of SQL table where the data should be inserted to.
    :param connection: SQL connection object.
    :param kwargs: Key-value pairs to insert.
    :return: None
    """
    column_names = list()
    values = list()
    for column_name, value in kwargs.items():
        column_names += [column_name]
        if isinstance(value, str):
            value = value.replace("'", "''")            # Change single quotes to double single quotes
            value = f"'{value}'"                        # Add quotes to string variables
        values += [str(value)]
    column_names_string = ",".join(column_names)
    values_string = ",".join(values)
    insert_data_command = f"INSERT INTO {table} ({column_names_string})\n" \
                          f"VALUES\n\t({values_string});"
    sql_cursor = connection.cursor()
    sql_cursor.execute(insert_data_command)
    connection.commit()
    return


def get_sqlite_data_type(python_type: type) -> str:
    """
    Get SQLite data type by python type name.
    :param python_type: Class type object (from class __annotations__).
    :return: SQLite data type of that corresponds to Python class.
    """
    type_name = python_type.__name__
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
