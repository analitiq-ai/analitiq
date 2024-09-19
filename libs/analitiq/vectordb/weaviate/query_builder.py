from weaviate.classes.query import Filter
from typing import Any, Dict, List, Union


class PropertyFilter:
    """
    The PropertyFilter class represents a filter on a specific property name.
    https://weaviate.io/developers/weaviate/api/graphql/filters

    :param name: The name of the property to filter on.
    """

    def __init__(self, name: str):
        self.name = name

    def like(self, value: str) -> Filter:
        return Filter.by_property(self.name).like(value)

    def equal(self, value: Any) -> Filter:
        return Filter.by_property(self.name).equal(value)


class QueryBuilder:
    """
    QueryBuilder

    A class for constructing queries using a given expression.

    Attributes:
        operators (dict): A dictionary mapping operators to their corresponding filter methods.

    Methods:
        construct_query(expression: Dict[str, Any]) -> Filter:
            Constructs a query based on the given expression.

        build_filters(expression: Dict[str, Any]) -> Filter:
            Recursively builds filter clauses based on the given expression.

    Exceptions:
        ValueError: Raised when an unsupported logical operator is encountered.

    """

    def __init__(self):
        self.operators = {"=": "equal", "!=": "notequal", "like": "like"}

    def construct_query(self, expression: Dict[str, Any]) -> Filter:
        return self.build_filters(expression)

    def build_filters(self, expression: Dict[str, Any]) -> Filter:
        # Assume the root is an "or" or "and" logical operator
        logical_op, clauses = next(iter(expression.items()))
        filters = []

        for clause in clauses:
            if "property" in clause and "operator" in clause and "value" in clause:
                prop_name = clause["property"]
                operator = clause["operator"].lower()
                value = clause["value"]

                if operator == "like":
                    filters.append(PropertyFilter(prop_name).like(value))
                elif operator == "=":
                    filters.append(PropertyFilter(prop_name).equal(value))
                elif operator == "not like":
                    filters.append(PropertyFilter(prop_name).not_like(value))
            else:
                # Recursively handle nested logical structures
                filters.append(self.build_filters(clause))

        if logical_op.lower() == "and":
            return Filter.all_of(filters)
        elif logical_op.lower() == "or":
            return Filter.any_of(filters)
        else:
            raise ValueError(f"Unsupported logical operator: {logical_op}")
