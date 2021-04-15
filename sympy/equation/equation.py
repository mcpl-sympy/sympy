
from sympy.core import Basic
from sympy.core.sympify import _sympify

from .sideproxy import SideProxy


class SymbolicRelation(Basic):

    is_Relational = True

    def __new__(cls, lhs, rhs, **kwargs):
        lhs = _sympify(lhs)
        rhs = _sympify(rhs)
        return super().__new__(cls, lhs, rhs)

    @property
    def lhs(self):
        """The left-hand side of the relation."""
        return self.args[0]

    @property
    def rhs(self):
        """The right-hand side of the relation."""
        return self.args[1]

    @property
    def apply(self):
        """Proxy object to apply operation on both sides."""
        return SideProxy(self, "both")

    @property
    def applylhs(self):
        """Proxy object to apply operation on left hand sides."""
        return SideProxy(self, "lhs")

    @property
    def applyrhs(self):
        """Proxy object to apply operation on right hand sides."""
        return SideProxy(self, "rhs")


class Equation(SymbolicRelation):
    rel_op = "=="

Eqn = Equation
