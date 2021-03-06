from sympy.core import Basic
from sympy.core.sympify import _sympify

from .sideproxy import SideProxy


class SymbolicRelation(Basic):
    """
    Base class for all symbolic relations.

    Explanation
    ===========

    Symbolic relation includes symbolic binary relations and unevaluated
    operations between symbolic relations.
    """
    # after operations are migrated to kind dispatching system,
    # remove _op_priority.
    _op_priority = 1000

    def __add__(self, other):
        return AddSides(self, other, evaluate=True)

    def __radd__(self, other):
        return AddSides(other, self, evaluate=True)

    def __sub__(self, other):
        return SubtractSides(self, other, evaluate=True)

    def __rsub__(self, other):
        return SubtractSides(other, self, evaluate=True)

    def __mul__(self, other):
        return MultiplySides(self, other, evaluate=True)

    def __rmul__(self, other):
        return MultiplySides(other, self, evaluate=True)

    def __truediv__(self, other):
        return DivideSides(self, other, evaluate=True)

    def __rtruediv__(self, other):
        return DivideSides(other, self, evaluate=True)


class SymbolicBinRel(SymbolicRelation):
    """
    Base class for all symbolic binary relations.

    Explanation
    ===========

    Unlike boolean relation, symbolic relation behaves as a container for
    the arguments. Its truth value is never evaluated, and all features are
    aimed for symbolic manipulation of the arguments.

    See Also
    ========

    sympy.core.relational.Relational : Boolean relation

    """

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


class Equation(SymbolicBinRel):
    """
    Symbolic equation.

    Examples
    ========

    Symbolic equation is not reduced to boolean value.

    >>> from sympy import Eqn
    >>> Eqn(1, 1).simplify()
    Eqn(1, 1)

    Arguments can be manipulated by ``applylhs``, ``applyrhs``, or ``apply``
    properties.

    >>> from sympy import cos, sin, gamma, trigsimp
    >>> from sympy.abc import x
    >>> eqn = Eqn(sin(x)**2 + cos(x)**2, gamma(x)/gamma(x-2))
    >>> eqn.apply.simplify()    # apply simplify method on both sides
    Eqn(1, (x - 2)*(x - 1))
    >>> eqn.applyrhs.simplify()     # apply simplify method on right hand side
    Eqn(sin(x)**2 + cos(x)**2, (x - 2)*(x - 1))
    >>> eqn.applylhs(trigsimp)      # apply trigsimp function on left hand side
    Eqn(1, gamma(x)/gamma(x - 2))

    See Also
    ========

    sympy.core.relational.Equality : Boolean equality

    """
    rel_op = "=="

Eqn = Equation


from .relop import AddSides, SubtractSides, MultiplySides, DivideSides
