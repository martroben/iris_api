
# standard
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
    column_typenames = {column_name: get_sqlite_data_type(column_type.__name__)
                        for column_name, column_type in columns.items()}
    columns_string = ",\n\t".join([f"{key} {value}" for key, value in column_typenames.items()])
    create_table_command = f"CREATE TABLE {table} (\n\t{columns_string}\n);"
    sql_cursor = connection.cursor()
    sql_cursor.execute(create_table_command)
    connection.commit()
    return


def read_table(table: str, connection: sqlite3.Connection, where: str = "") -> list[dict]:
    """
    Get data from a SQL table.
    :param table: SQL table name.
    :param connection: SQL connection.
    :param where: Optional SQL WHERE filtering clause: e.g. "column = value" or "column IN (1,2,3)".
    :return: A list of column_name:value dicts.
    """
    where_statement = f" WHERE {where}" if where else ""
    get_data_command = f"SELECT * FROM {table}{where_statement};"
    sql_cursor = connection.cursor()
    response = sql_cursor.execute(get_data_command)
    data = response.fetchall()
    data_column_names = [item[0] for item in response.description]

    data_rows = list()
    for row in data:
        data_row = {key: value for key, value in zip(data_column_names, row)}
        data_rows += [data_row]
    return data_rows


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
        self.setup()

    def setup(self):
        # Check if table exists and create if it doesn't.
        if not table_exists(self.name, self.connection):
            create_table(
                table=self.name,
                columns=self.columns,
                connection=self.connection)

    def select(self, where: str = "") -> list[dict]:
        result = read_table(
            table=self.name,
            connection=self.connection,
            where=where)
        return result

    def insert(self, **kwargs) -> None:
        insert_row(
            table=self.name,
            connection=self.connection,
            **kwargs)


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

    def select_iris(self, where: str = "") -> list[Iris]:
        """
        Returns sql data with items formatted to the Iris class.
        """
        data_raw = self.select(where=where)
        data_iris = list()
        for row in data_raw:
            data_iris += [self.type_class(row)]
        return data_iris

    def insert_unique(self, data: list[Iris]):
        """
        Inserts Iris objects to sql only if it's not already present in the table.
        Uses list input to avoid duplicative comparisons for every insertion.
        """
        existing_data = self.select_iris()
        # deduplicate input data and insert rows that are not yet present.
        for row in set(data):
            if row not in existing_data:
                self.insert(**row.as_dict())



