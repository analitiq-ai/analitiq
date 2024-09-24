from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


class Column(BaseModel):
    """Represents a column in a table.

    Attributes
    ----------
        ColumnName (str): The name of the column.
        DataType (str): Data type of the column.

    """

    ColumnName: str = Field(description="The name of the column.")
    DataType: str = Field(description="Data type of the column.")


class Table(BaseModel):
    """:class: Table

    The `Table` class represents a table in a database. It inherits from the `BaseModel` class.

    Attributes
    ----------
        SchemaName (str): The schema where this table resides.
        TableName (str): The name of the table.
        Columns (List[Column]): A list of relevant columns in the table.

    Methods
    -------
        to_json(): Converts the model to a JSON string.

    """

    SchemaName: str = Field(description="The schema where this table resides.")
    TableName: str = Field(description="The name of the table.")
    Columns: List[Column] = Field(description="A list of relevant columns in the table.")

    def to_json(self):
        # Convert model to JSON string
        return self.model_dump_json()


class Tables(BaseModel):
    """Represents a list of relevant tables from the list of all tables in a database.

    :param TableList (List[Table]): A list of relevant tables.
    """

    TableList: List[Table] = Field(
        description="A list of relevant tables from the list of all tables in a database"
    )

    def to_json(self):
        # Convert model to JSON string
        return self.model_dump_json()


class SQL(BaseModel):
    """.. py:class:: SQL(BaseModel)

    Represents a class for storing SQL code and additional explanations.

    :ivar SQL_Code: The SQL code.
    :vartype SQL_Code: str

    :ivar Explanation: Additional text or explanation other than SQL code.
    :vartype Explanation: str

    """

    SQL_Code: str = Field(description="Only SQL code goes in here.")
    Explanation: str = Field(description="Any text or explanation other than SQL code.")


class TableCheck(BaseModel):
    """A class representing a table check.

    This class is used to determine whether a table is necessary to answer users' queries.

    Attributes
    ----------
        Required (bool): Indicates whether the table is necessary or not.

    """

    Required: bool = Field(description="Is this table necessary to answer users query?")
