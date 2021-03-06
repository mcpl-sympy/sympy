from collections import defaultdict
from collections.abc import MutableMapping

from sympy.assumptions.ask import Q
from sympy.assumptions.assume import Predicate, AppliedPredicate
from sympy.assumptions.cnf import AND, OR, to_NNF
from sympy.assumptions.facts import get_composite_predicates
from sympy.core import (Add, Mul, Pow, Integer, Number, NumberSymbol,)
from sympy.core.numbers import ImaginaryUnit
from sympy.core.rules import Transform
from sympy.core.sympify import _sympify
from sympy.functions.elementary.complexes import Abs
from sympy.logic.boolalg import (Equivalent, Implies, BooleanFunction)
from sympy.matrices.expressions import MatMul

# APIs here may be subject to change


def _find_freepredicate(expr):
    # Find unapplied predicate from expression tree.
    # Ignore the predicate in AppliedPredicate.
    if isinstance(expr, Predicate):
        return {expr}
    if not expr.args:
        return set()
    if isinstance(expr, AppliedPredicate):
        args = expr.arguments
    else:
        args = expr.args
    result = set()
    for arg in args:
        result.update(_find_freepredicate(arg))
    return result


class UnevaluatedOnFree(BooleanFunction):
    """
    Represents a Boolean function that remains unevaluated on free predicates.

    Explanation
    ===========

    This is intended to be a superclass of other classes, which define the
    behavior on singly applied predicates.

    A free predicate is a predicate that is not applied, or a combination
    thereof. For example, Q.zero or Or(Q.positive, Q.negative).

    A singly applied predicate is a free predicate applied everywhere to a
    single expression. For instance, Q.zero(x) and Or(Q.positive(x*y),
    Q.negative(x*y)) are singly applied, but Or(Q.positive(x), Q.negative(y))
    and Or(Q.positive, Q.negative(y)) are not.

    The boolean literals True and False are considered to be both free and
    singly applied.

    This class raises ValueError unless the input is a free predicate or a
    singly applied predicate.

    On a free predicate, this class remains unevaluated. On a singly applied
    predicate, the method apply() is called and returned, or the original
    expression returned if apply() returns None. When apply() is called,
    self.expr is set to the unique expression that the predicates are applied
    at. self.pred is set to the free form of the predicate.

    The typical usage is to create this class with free predicates and
    evaluate it using .rcall().

    """
    def __new__(cls, arg):
        # Mostly type checking here
        arg = _sympify(arg)
        predicates = _find_freepredicate(arg)
        applied_predicates = arg.atoms(AppliedPredicate)
        if predicates and applied_predicates:
            raise ValueError("arg must be either completely free or singly applied")
        if not applied_predicates:
            obj = BooleanFunction.__new__(cls, arg)
            obj.pred = arg
            obj.expr = None
            return obj
        predicate_args = {pred.arguments[0] for pred in applied_predicates}
        if len(predicate_args) > 1:
            raise ValueError("The AppliedPredicates in arg must be applied to a single expression.")
        obj = BooleanFunction.__new__(cls, arg)
        obj.expr = predicate_args.pop()
        obj.pred = arg.xreplace(Transform(lambda e: e.function, lambda e:
            isinstance(e, AppliedPredicate)))
        applied = obj.apply(obj.expr)
        if applied is None:
            return obj
        return applied

    def apply(self, expr=None):
        if expr is None:
            return
        pred = to_NNF(self.pred, get_composite_predicates())
        return self._eval_apply(expr, pred)

    def _eval_apply(self, expr, pred):
        return None


class AllArgs(UnevaluatedOnFree):
    """
    Class representing vectorizing a predicate over all the .args of an
    expression

    See the docstring of UnevaluatedOnFree for more information on this
    class.

    The typical usage is to evaluate predicates with expressions using .rcall().

    Example
    =======

    >>> from sympy.assumptions.sathandlers import AllArgs
    >>> from sympy import symbols, Q
    >>> x, y = symbols('x y')
    >>> a = AllArgs(Q.positive | Q.negative)
    >>> a
    AllArgs(Q.negative | Q.positive)
    >>> a.rcall(x*y)
    ((Literal(Q.negative(x), False) | Literal(Q.positive(x), False)) & (Literal(Q.negative(y), False) | \
    Literal(Q.positive(y), False)))

    See Also
    ========

    UnevaluatedOnFree

    """

    def _eval_apply(self, expr, pred):
        return AND(*[pred.rcall(arg) for arg in expr.args])


class AnyArgs(UnevaluatedOnFree):
    """
    Class representing vectorizing a predicate over any of the .args of an
    expression.

    See the docstring of UnevaluatedOnFree for more information on this
    class.

    The typical usage is to evaluate predicates with expressions using .rcall().

    Example
    =======
    >>> from sympy.assumptions.sathandlers import AnyArgs
    >>> from sympy import symbols, Q
    >>> x, y = symbols('x y')
    >>> a = AnyArgs(Q.positive & Q.negative)
    >>> a
    AnyArgs(Q.negative & Q.positive)
    >>> a.rcall(x*y)
    ((Literal(Q.negative(x), False) & Literal(Q.positive(x), False)) | (Literal(Q.negative(y), False) & \
    Literal(Q.positive(y), False)))

    """

    def _eval_apply(self, expr, pred):
        return OR(*[pred.rcall(arg) for arg in expr.args])


class ExactlyOneArg(UnevaluatedOnFree):
    """
    Class representing a predicate holding on exactly one of the .args of an
    expression.

    See the docstring of UnevaluatedOnFree for more information on this
    class.

    The typical usage is to evaluate predicate with expressions using
    .rcall().

    Example
    =======
    >>> from sympy.assumptions.sathandlers import ExactlyOneArg
    >>> from sympy import symbols, Q
    >>> x, y = symbols('x y')
    >>> a = ExactlyOneArg(Q.positive)
    >>> a
    ExactlyOneArg(Q.positive)
    >>> a.rcall(x*y)
    ((Literal(Q.positive(x), False) & Literal(Q.positive(y), True)) | (Literal(Q.positive(x), True) & \
    Literal(Q.positive(y), False)))

    """

    def _eval_apply(self, expr, pred):
        pred_args = [pred.rcall(arg) for arg in expr.args]
        # Technically this is xor, but if one term in the disjunction is true,
        # it is not possible for the remainder to be true, so regular or is
        # fine in this case.
        res = OR(*[AND(pred_args[i], *[~lit for lit in pred_args[:i] +
            pred_args[i+1:]]) for i in range(len(pred_args))])
        return res
        # Note: this is the equivalent cnf form. The above is more efficient
        # as the first argument of an implication, since p >> q is the same as
        # q | ~p, so the the ~ will convert the Or to and, and one just needs
        # to distribute the q across it to get to cnf.

        # return And(*[Or(*map(Not, c)) for c in combinations(pred_args, 2)]) & Or(*pred_args)


_old_assump_getters = {
    Q.positive: lambda o: o.is_positive,
    Q.zero: lambda o: o.is_zero,
    Q.negative: lambda o: o.is_negative,
    Q.nonpositive: lambda o: o.is_nonpositive,
    Q.nonzero: lambda o: o.is_nonzero,
    Q.nonnegative: lambda o: o.is_nonnegative,
    Q.rational: lambda o: o.is_rational,
    Q.irrational: lambda o: o.is_irrational,
    Q.even: lambda o: o.is_even,
    Q.odd: lambda o: o.is_odd,
    Q.integer: lambda o: o.is_integer,
    Q.composite: lambda o: o.is_composite,
    Q.imaginary: lambda o: o.is_imaginary,
    Q.commutative: lambda o: o.is_commutative,
}

def _old_assump_replacer(obj):
    # obj is AppliedPredicate

    getter = _old_assump_getters.get(obj.function, None)
    if getter is None:
        return obj

    ret = getter(*obj.arguments)
    if ret is None:
        return obj
    return ret


def evaluate_old_assump(pred):
    """
    Replace assumptions of expressions replaced with their values in the old
    assumptions (like Q.negative(-1) => True). Useful because some direct
    computations for numeric objects is defined most conveniently in the old
    assumptions.

    """
    return pred.xreplace(Transform(_old_assump_replacer))


class CheckOldAssump(UnevaluatedOnFree):
    def apply(self, expr=None, is_Not=False):
        arg = self.args[0](expr) if callable(self.args[0]) else self.args[0]
        res = Equivalent(arg, evaluate_old_assump(arg))
        return to_NNF(res, get_composite_predicates())


class CheckIsPrime(UnevaluatedOnFree):
    def apply(self, expr=None, is_Not=False):
        from sympy import isprime
        arg = self.args[0](expr) if callable(self.args[0]) else self.args[0]
        res = Equivalent(arg, isprime(expr))
        return to_NNF(res, get_composite_predicates())

class CustomLambda:
    """
    Interface to lambda with rcall

    Workaround until we get a better way to represent certain facts.
    """
    def __init__(self, lamda):
        self.lamda = lamda

    def apply(self, *args):
        return to_NNF(self.lamda(*args), get_composite_predicates())


class ClassFactRegistry(MutableMapping):
    """
    Register handlers against classes.

    Explanation
    ===========

    ``registry[C] = handler`` registers ``handler`` for class
    ``C``. ``registry[C]`` returns a set of handlers for class ``C``, or any
    of its superclasses.
    """
    def __init__(self, d=None):
        d = d or {}
        self.d = defaultdict(frozenset, d)
        super().__init__()

    def __setitem__(self, key, item):
        self.d[key] = frozenset(item)

    def __getitem__(self, key):
        ret = self.d[key]
        for k in self.d:
            if issubclass(key, k):
                ret |= self.d[k]
        return ret

    def __delitem__(self, key):
        del self.d[key]

    def __iter__(self):
        return self.d.__iter__()

    def __len__(self):
        return len(self.d)

    def __repr__(self):
        return repr(self.d)


fact_registry = ClassFactRegistry()


def register_fact(klass, fact, registry=fact_registry):
    registry[klass] |= {fact}


for klass, fact in [
    (Mul, Equivalent(Q.zero, AnyArgs(Q.zero))),
    (MatMul, Implies(AllArgs(Q.square), Equivalent(Q.invertible, AllArgs(Q.invertible)))),
    (Add, Implies(AllArgs(Q.positive), Q.positive)),
    (Add, Implies(AllArgs(Q.negative), Q.negative)),
    (Mul, Implies(AllArgs(Q.positive), Q.positive)),
    (Mul, Implies(AllArgs(Q.commutative), Q.commutative)),
    (Mul, Implies(AllArgs(Q.real), Q.commutative)),

    (Pow, CustomLambda(lambda power: Implies(Q.real(power.base) &
    Q.even(power.exp) & Q.nonnegative(power.exp), Q.nonnegative(power)))),
    (Pow, CustomLambda(lambda power: Implies(Q.nonnegative(power.base) & Q.odd(power.exp) & Q.nonnegative(power.exp), Q.nonnegative(power)))),
    (Pow, CustomLambda(lambda power: Implies(Q.nonpositive(power.base) & Q.odd(power.exp) & Q.nonnegative(power.exp), Q.nonpositive(power)))),

    # This one can still be made easier to read. I think we need basic pattern
    # matching, so that we can just write Equivalent(Q.zero(x**y), Q.zero(x) & Q.positive(y))
    (Pow, CustomLambda(lambda power: Equivalent(Q.zero(power), Q.zero(power.base) & Q.positive(power.exp)))),
    (Integer, CheckIsPrime(Q.prime)),
    (Integer, CheckOldAssump(Q.composite)),
    # Implicitly assumes Mul has more than one arg
    # Would be AllArgs(Q.prime | Q.composite) except 1 is composite
    (Mul, Implies(AllArgs(Q.prime), ~Q.prime)),
    # More advanced prime assumptions will require inequalities, as 1 provides
    # a corner case.
    (Mul, Implies(AllArgs(Q.imaginary | Q.real), Implies(ExactlyOneArg(Q.imaginary), Q.imaginary))),
    (Mul, Implies(AllArgs(Q.real), Q.real)),
    (Add, Implies(AllArgs(Q.real), Q.real)),
    # General Case: Odd number of imaginary args implies mul is imaginary(To be implemented)
    (Mul, Implies(AllArgs(Q.real), Implies(ExactlyOneArg(Q.irrational),
        Q.irrational))),
    (Add, Implies(AllArgs(Q.real), Implies(ExactlyOneArg(Q.irrational),
        Q.irrational))),
    (Mul, Implies(AllArgs(Q.rational), Q.rational)),
    (Add, Implies(AllArgs(Q.rational), Q.rational)),

    (Abs, Q.nonnegative),
    (Abs, Equivalent(AllArgs(~Q.zero), ~Q.zero)),

    # Including the integer qualification means we don't need to add any facts
    # for odd, since the assumptions already know that every integer is
    # exactly one of even or odd.
    (Mul, Implies(AllArgs(Q.integer), Equivalent(AnyArgs(Q.even), Q.even))),

    (Abs, Implies(AllArgs(Q.even), Q.even)),
    (Abs, Implies(AllArgs(Q.odd), Q.odd)),

    (Add, Implies(AllArgs(Q.integer), Q.integer)),
    (Add, Implies(ExactlyOneArg(~Q.integer), ~Q.integer)),
    (Mul, Implies(AllArgs(Q.integer), Q.integer)),
    (Mul, Implies(ExactlyOneArg(~Q.rational), ~Q.integer)),
    (Abs, Implies(AllArgs(Q.integer), Q.integer)),

    (Number, CheckOldAssump(Q.negative)),
    (Number, CheckOldAssump(Q.zero)),
    (Number, CheckOldAssump(Q.positive)),
    (Number, CheckOldAssump(Q.nonnegative)),
    (Number, CheckOldAssump(Q.nonzero)),
    (Number, CheckOldAssump(Q.nonpositive)),
    (Number, CheckOldAssump(Q.rational)),
    (Number, CheckOldAssump(Q.irrational)),
    (Number, CheckOldAssump(Q.even)),
    (Number, CheckOldAssump(Q.odd)),
    (Number, CheckOldAssump(Q.integer)),
    (Number, CheckOldAssump(Q.imaginary)),
    # For some reason NumberSymbol does not subclass Number
    (NumberSymbol, CheckOldAssump(Q.negative)),
    (NumberSymbol, CheckOldAssump(Q.zero)),
    (NumberSymbol, CheckOldAssump(Q.positive)),
    (NumberSymbol, CheckOldAssump(Q.nonnegative)),
    (NumberSymbol, CheckOldAssump(Q.nonzero)),
    (NumberSymbol, CheckOldAssump(Q.nonpositive)),
    (NumberSymbol, CheckOldAssump(Q.rational)),
    (NumberSymbol, CheckOldAssump(Q.irrational)),
    (NumberSymbol, CheckOldAssump(Q.imaginary)),
    (ImaginaryUnit, CheckOldAssump(Q.negative)),
    (ImaginaryUnit, CheckOldAssump(Q.zero)),
    (ImaginaryUnit, CheckOldAssump(Q.positive)),
    (ImaginaryUnit, CheckOldAssump(Q.nonnegative)),
    (ImaginaryUnit, CheckOldAssump(Q.nonzero)),
    (ImaginaryUnit, CheckOldAssump(Q.nonpositive)),
    (ImaginaryUnit, CheckOldAssump(Q.rational)),
    (ImaginaryUnit, CheckOldAssump(Q.irrational)),
    (ImaginaryUnit, CheckOldAssump(Q.imaginary))
    ]:

    register_fact(klass, fact)
