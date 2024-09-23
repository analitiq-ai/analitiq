from weaviate.classes.query import Filter
from typing import Any, Dict


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

    def not_equal(self, value: Any) -> Filter:
        return Filter.by_property(self.name).not_equal(value)


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
        self.operator_methods = {
            "like": "like",
            "=": "equal",
            "!=": "not_equal",
            "not like": "not_like"
        }

    def construct_query(self, expression: Dict[str, Any]) -> Filter:
        return self.build_filters(expression)

    def build_filters(self, expression: Dict[str, Any]) -> Filter:
        # Check if the expression is a single filter clause
        if "property" in expression and "operator" in expression and "value" in expression:
            prop_name = expression["property"]
            operator = expression["operator"].lower()
            value = expression["value"]

            if operator == "like":
                return PropertyFilter(prop_name).like(value)
            elif operator == "=":
                return PropertyFilter(prop_name).equal(value)
            elif operator == "not like":
                return PropertyFilter(prop_name).not_like(value)
            else:
                # Handle other operators as needed
                raise ValueError(f"Unsupported operator: {operator}")
        else:
            # Assume the root is an "or" or "and" logical operator
            logical_op, clauses = next(iter(expression.items()))
            filters = []

            for clause in clauses:
                if "property" in clause and "operator" in clause and "value" in clause:
                    prop_name = clause["property"]
                    operator = clause["operator"].lower()
                    value = clause["value"]

                    if operator in self.operator_methods:
                        method_name = self.operator_methods[operator]
                        method = getattr(PropertyFilter(prop_name), method_name)
                        filters.append(method(value))
                    else:
                        raise ValueError(f"Unsupported operator: {operator}")
                else:
                    # Recursively handle nested logical structures
                    filters.append(self.build_filters(clause))

            if logical_op.lower() == "and":
                return Filter.all_of(filters)
            elif logical_op.lower() == "or":
                return Filter.any_of(filters)
            else:
                raise ValueError(f"Unsupported logical operator: {logical_op}")
