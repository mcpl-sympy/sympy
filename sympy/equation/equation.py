
from sympy.core import Basic
from sympy.core.sympify import _sympify


class Equation(Basic):
    def __new__(cls, lhs, rhs, **kwargs):
        lhs = _sympify(lhs)
        rhs = _sympify(rhs)
        return super().__new__(cls, lhs, rhs)

    @property
    def lhs(self):
        return self.args[0]

    @property
    def rhs(self):
        return self.args[0]

Eqn = Equation
