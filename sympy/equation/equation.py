
from sympy.core import Basic
from sympy.core.sympify import _sympify


class SymbolicRelation(Basic):

    is_Relational = True

    def __new__(cls, lhs, rhs, **kwargs):
        lhs = _sympify(lhs)
        rhs = _sympify(rhs)
        return super().__new__(cls, lhs, rhs)

    @property
    def lhs(self):
        return self.args[0]

    @property
    def rhs(self):
        return self.args[1]


class Equation(SymbolicRelation):
    rel_op = "=="

Eqn = Equation
