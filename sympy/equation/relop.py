from sympy.core import Basic
from sympy.multipledispatch import Dispatcher
from .equation import SymbolicRelation, Equation


class RelOp(SymbolicRelation):
    """
    Base class for every unevaluated operation between symbolic relations.

    """
    def __new__(cls, arg1, arg2, evaluate=False):
        if all(not isinstance(arg, SymbolicRelation) for arg in [arg1, arg2]):
            raise TypeError("At least one argument must be SymbolicRelation.")

        if not isinstance(arg1, SymbolicRelation):
            arg1 = Equation(arg1, arg1)
        if not isinstance(arg2, SymbolicRelation):
            arg2 = Equation(arg2, arg2)

        if evaluate:
            obj = cls.eval(arg1, arg2)
            if obj is not None:
                return obj
        return super().__new__(cls, arg1, arg2)

    @classmethod
    def eval(cls, arg1, arg2, assumptions=None):
        try:
            ret = cls.eval_dispatcher(arg1, arg2, assumptions=None)
        except NotImplementedError:
            ret = None
        return ret

    @classmethod
    def register(cls, type1, type2):
        return cls.eval_dispatcher.register(type1, type2)

    def doit(self, **options):
        if hints.get('deep', True):
            args = [arg.doit(**hints) for arg in self.args]
        else:
            args = self.args
        return self.func(*arg, evaluate=True)

    def _eval_refine(self, assumptions=True):
        if assumptions == True:
            assumptions = None
        return self.eval(*self.args, assumptions=assumptions)


class AddSides(RelOp):
    """
    Add each side of two binary relations.

    Examples
    ========

    >>> from sympy import Eqn
    >>> from sympy.equation.relop import AddSides
    >>> from sympy.abc import x, y, z

    ``AddSides`` can add two relations.

    >>> AddSides(Eqn(x, y), Eqn(y, z), evaluate=True)
    Eqn(x + y, y + z)

    ``AddSides`` can add an expression to each side of the relation.

    >>> AddSides(Eqn(x, y), z, evaluate=True)
    Eqn(x + z, y + z)
    """
    eval_dispatcher = Dispatcher('AddSides_dispatcher')

@AddSides.register(Equation, Equation)
def _(eqn1, eqn2, assumptions=None):
    lhs = eqn1.lhs + eqn2.lhs
    rhs = eqn1.rhs + eqn2.rhs
    return Equation(lhs, rhs)


class SubtractSides(RelOp):
    """
    Subtract each side of two binary relations.

    Examples
    ========

    >>> from sympy import Eqn
    >>> from sympy.equation.relop import SubtractSides
    >>> from sympy.abc import x, y, z

    ``SubtractSides`` can subtract two relations.

    >>> SubtractSides(Eqn(x, y), Eqn(y, z), evaluate=True)
    Eqn(x - y, y - z)

    ``SubtractSides`` can subtract an expression to each side of the relation.

    >>> SubtractSides(Eqn(x, y), z, evaluate=True)
    Eqn(x - z, y - z)
    >>> SubtractSides(z, Eqn(x, y), evaluate=True)
    Eqn(-x + z, -y + z)
    """
    eval_dispatcher = Dispatcher('SubtractSides_dispatcher')

@SubtractSides.register(Equation, Equation)
def _(eqn1, eqn2, assumptions=None):
    lhs = eqn1.lhs - eqn2.lhs
    rhs = eqn1.rhs - eqn2.rhs
    return Equation(lhs, rhs)


class MultiplySides(RelOp):
    """
    Multiply each side of two binary relations.

    Examples
    ========

    >>> from sympy import Eqn
    >>> from sympy.equation.relop import MultiplySides
    >>> from sympy.abc import x, y, z

    ``MultiplySides`` can multiply two relations.

    >>> MultiplySides(Eqn(x, y), Eqn(y, z), evaluate=True)
    Eqn(x*y, y*z)

    ``MultiplySides`` can multiply an expression to each side of the relation.

    >>> MultiplySides(Eqn(x, y), z, evaluate=True)
    Eqn(x*z, y*z)
    """
    eval_dispatcher = Dispatcher('MultiplySides_dispatcher')

@MultiplySides.register(Equation, Equation)
def _(eqn1, eqn2, assumptions=None):
    lhs = eqn1.lhs * eqn2.lhs
    rhs = eqn1.rhs * eqn2.rhs
    return Equation(lhs, rhs)


class DivideSides(RelOp):
    """
    Divide each side of two binary relations.

    Examples
    ========

    >>> from sympy import Eqn
    >>> from sympy.equation.relop import DivideSides
    >>> from sympy.abc import x, y, z

    ``DivideSides`` can divide two relations.

    >>> DivideSides(Eqn(x, y), Eqn(y, z), evaluate=True)
    Eqn(x/y, y/z)

    ``DivideSides`` can divide each side of the relation by an expression.

    >>> DivideSides(Eqn(x, y), z, evaluate=True)
    Eqn(x/z, y/z)
    >>> DivideSides(z, Eqn(x, y), evaluate=True)
    Eqn(z/x, z/y)
    """
    eval_dispatcher = Dispatcher('MultiplySides_dispatcher')

@DivideSides.register(Equation, Equation)
def _(eqn1, eqn2, assumptions=None):
    lhs = eqn1.lhs / eqn2.lhs
    rhs = eqn1.rhs / eqn2.rhs
    return Equation(lhs, rhs)
