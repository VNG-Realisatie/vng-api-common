"""
Define scopes to manage authorizations on API resources.

Scope objects hold their own definition and documentation. Public scopes get
added to the scope registry, which can be introspected for automatic
documentation.
"""

from typing import List

OPERATOR_OR = "OR"
OPERATOR_AND = "AND"


SCOPE_REGISTRY = set()


class Scope:
    """
    Define a single scope object.

    A scope is characterized by a label, whereas the actual permissions related
    to it are implemented in the view(set)s. Scopes can be OR-ed together:

        >>> Scope("foo") | Scope("bar")
        Scope("foo | bar")

    this is interpreted as: you have permission if you have one of either
    scopes in your authorization configuration.

    :arg label: A label identifying the scope. Labels must be unique.
    :arg description: An optional description of what the scope allows/means.
    :arg private: Private scopes are not added to the registry.
    """

    def __init__(self, label: str, description: str = None, private: bool = False):
        self.label = label
        self.description = description

        # combined scopes
        self.children = []
        self.operator = None

        # add to registry
        if not private:
            SCOPE_REGISTRY.add(self)

    def __repr__(self) -> str:
        if self.children:
            return "<%s: %r" % (self.operator, self.children)

        cls_name = self.__class__.__name__
        return "<%s: label=%r>" % (cls_name, self.label)

    def __str__(self):
        return f"({self.label})" if self.children else self.label

    def __or__(self, other):
        new = type(self)(label=f"{self.label} | {other.label}")
        new.children = [self, other]
        new.operator = OPERATOR_OR
        return new

    def is_contained_in(self, scope_set: List[str]) -> bool:
        """
        Test if the flat ``scope_set`` encapsulate this scope.
        """
        if not self.children:
            return self.label in scope_set

        children_contained = (
            child.is_contained_in(scope_set) for child in self.children
        )

        if self.operator == OPERATOR_OR:
            return any(children_contained)
        elif self.operator == OPERATOR_AND:
            return all(children_contained)
        else:
            raise ValueError(f"Unkonwn operator '{self.operator}'")
