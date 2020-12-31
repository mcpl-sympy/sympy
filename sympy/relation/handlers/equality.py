from sympy.assumptions import ask, Q
from sympy.core import Basic, Expr, Symbol, Tuple
from sympy.core.function import AppliedUndef
from sympy.core.logic import fuzzy_bool, fuzzy_and
from sympy.logic.boolalg import BooleanAtom
from sympy.multipledispatch import Dispatcher

EqualHandler = Dispatcher(
    "EqualHandler",
    doc="""
    Handler for Q.eq.
    Test that two expressions are equal.
    """
)

@EqualHandler.register(Basic, Basic)
def _(lhs, rhs, assumptions):
    return None

@EqualHandler.register(Tuple, Expr)
def _(lhs, rhs, assumptions):
    return False

@EqualHandler.register(Tuple, AppliedUndef)
def _(lhs, rhs, assumptions):
    return None

@EqualHandler.register(Tuple, Symbol)
def _(lhs, rhs, assumptions):
    return None

@EqualHandler.register(Tuple, Tuple)
def _(lhs, rhs, assumptions):
    if len(lhs) != len(rhs):
        return False
    return fuzzy_and(fuzzy_bool(ask(Q.eq(s, o), assumptions)) for s, o in zip(lhs, rhs))

@EqualHandler.register(BooleanAtom, BooleanAtom)
def _(lhs, rhs, assumptions):
    return lhs is rhs
