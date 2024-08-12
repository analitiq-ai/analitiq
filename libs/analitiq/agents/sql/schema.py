from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


class Column(BaseModel):
    ColumnName: str = Field(description="The name of the column.")
    DataType: str = Field(description="Data type of the column.")


class Table(BaseModel):
    SchemaName: str = Field(description="The schema where this table resides.")
    TableName: str = Field(description="The name of the table.")
    Columns: List[Column] = Field(description="A list of relevant columns in the table.")

    def to_json(self):
        # Convert model to JSON string
        return self.json()


class Tables(BaseModel):
    TableList: List[Table] = Field(
        description="A list of relevant tables from the list of all tables in a database"
    )

    def to_json(self):
        # Convert model to JSON string
        return self.json()


class SQL(BaseModel):
    SQL_Code: str = Field(description="Only SQL code goes in here.")
    Explanation: str = Field(description="Any text or explanation other than SQL code.")


class TableCheck(BaseModel):
    Required: bool = Field(description="Is this table necessary to answer users query?")
