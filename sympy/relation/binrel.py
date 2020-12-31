"""
Basic classes for relational predicates.
"""
from functools import partial

from sympy.assumptions import AppliedPredicate, Predicate, refine
from sympy.core import Expr, S
from sympy.core.compatibility import ordered
from sympy.core.sympify import _sympify
from sympy.logic.boolalg import BooleanAtom
from sympy.multipledispatch import MDNotImplementedError


class BinaryRelation(Predicate):
    """
    Base class for all binary relational predicates.
    """

    is_reflexive = None

    def __call__(self, *args):
        if not len(args) == 2:
            raise ValueError("Binary relation takes two arguments, but got %s." % len(args))
        return AppliedBinaryRelation(self, *args)

    def eval(self, args, assumptions=True):
        lhs, rhs = args

        # quick exit for structurally same arguments
        ret = self._compare_reflexive(lhs, rhs)
        if ret is not None:
            return ret

        lhs, rhs = lhs.simplify(), rhs.simplify()

        # attempt quick exit again with simplified arguments
        ret = self._compare_reflexive(lhs, rhs)
        if ret is not None:
            return ret

        # definitive comparison with 0
        try:
            dif = lhs - rhs
            v = None
            if dif.is_comparable:
                v = dif.n(2)
            elif dif.equals(0):  # XXX this is expensive
                v = S.Zero
            if v is not None:
                r = self._eval_relation(v, S.Zero)
                if r is not None:
                    return r
        except TypeError:
            pass

        # canonicallize the args and use dispatching
        r = self(lhs, rhs).simplify()
        lhs, rhs = r.lhs, r.rhs
        return super().eval((lhs, rhs), assumptions)

    def _compare_reflexive(self, lhs, rhs):
        # quick exit for structurally same arguments
        # do not check != here because it cannot catch the
        # same arguements with different structures.
        reflexive = self.is_reflexive
        if reflexive is None:
            pass
        elif reflexive and (lhs == rhs):
            return True
        elif not reflexive and (lhs == rhs):
            return False
        return None


class AppliedBinaryRelation(AppliedPredicate):
    """
    The class of expressions resulting from applying ``BinaryRelation``
    to the arguments.

    Examples
    ========

    Binary relation is never evaluated to boolean unless applied
    to ``ask()`` function.

    >>> from sympy import ask, sin, cos, Q
    >>> from sympy.abc import x, y, z
    >>> eq1 = Q.eq(sin(x)**2 + cos(x)**2, 1)
    >>> eq1
    sin(x)**2 + cos(x)**2 = 1
    >>> eq1.simplify()
    0 = 0
    >>> _.doit()
    0 = 0
    >>> ask(eq1)
    True

    Binary relation can be operated with another equal or expression.

    >>> eq2 = Q.eq(x, 4)
    >>> eq2 + 3
    x + 3 = 7
    >>> eq1/eq2
    (sin(x)**2 + cos(x)**2)/x = 1/4

    SymPy functions can be applied to binary relations.

    >>> sin(eq2)
    sin(x) = sin(4)

    ``refine()`` method refines the binary relation with assumptions
    without necessarily solving it.

    >>> Q.eq(x*y, y*z).refine()
    x*y = y*z
    >>> Q.eq(x*y, y*z).refine(Q.nonzero(y))
    x = z

    ``simplify()`` method simplifies the binary relation into canonical
    form. You can skip the canonicalization by passing *equation=False*,
    and decide which term will be simplified with *termname* parameter.

    >>> from sympy import gamma
    >>> eq3 = Q.eq(sin(x)**2 + cos(x)**2, gamma(x)/gamma(x-2))
    >>> eq3.simplify()
    x**2 - 3*x = -1
    >>> eq3.simplify(equation=False)
    1 = (x - 2)*(x - 1)
    >>> eq3.simplify(equation=False, termname='lhs')
    1 = gamma(x)/gamma(x - 2)

    ``solve()`` method solves the equation with respect to certain symbol.

    >>> Q.eq(2*(x+y), 2*(z+3)).solve(x)
    x = -y + z + 3

    Other methods are automatically applied to terms. You can control
    it with *termname* parameter.

    >>> eq4 = Q.eq(x*(x+1), y*(y+2))
    >>> eq4.expand(termname='lhs')
    x**2 + x = y*(y + 2)
    >>> eq4.expand(termname='rhs')
    x*(x + 1) = y**2 + 2*y

    """

    # will be deleted after _op_priority is removed from SymPy
    _op_priority = 1000

    @property
    def lhs(self):
        """The left-hand side of the relation."""
        return self.args[0]

    @property
    def rhs(self):
        """The right-hand side of the relation."""
        return self.args[1]

    @property
    def reversed(self):
        """Return the relationship with sides reversed.

        Examples
        ========

        >>> from sympy import Q
        >>> from sympy.abc import x
        >>> Q.eq(x, 1)
        x = 1
        >>> _.reversed
        1 = x
        >>> Q.lt(x, 1)
        x < 1
        >>> _.reversed
        1 > x
        """
        return self.func.reversed(self.rhs, self.lhs)

    @property
    def reversedsign(self):
        """Return the relationship with signs reversed.

        Examples
        ========

        >>> from sympy import Q
        >>> from sympy.abc import x
        >>> Q.eq(x, 1)
        x = 1
        >>> _.reversedsign
        -x = -1
        >>> Q.lt(x, 1)
        x < 1
        >>> _.reversedsign
        -x > -1
        """
        a, b = self.args
        if not (isinstance(a, BooleanAtom) or isinstance(b, BooleanAtom)):
            return self.func.reversed(-self.lhs, -self.rhs)
        else:
            return self

    @property
    def canonical(self):
        """Return a canonical form of the relational by putting a
        number on the rhs, canonically removing a sign or else
        ordering the args canonically. No other simplification is
        attempted.

        Examples
        ========

        >>> from sympy import Q
        >>> from sympy.abc import x, y
        >>> Q.lt(x,2)
        x < 2
        >>> _.reversed.canonical
        x < 2
        >>> Q.lt(-y, x).canonical
        x > -y
        >>> Q.gt(-y, x).canonical
        x < -y
        >>> Q.lt(-y, -x).canonical
        x < y
        """
        args = self.args
        r = self
        if r.rhs.is_number:
            if r.rhs.is_Number and r.lhs.is_Number and r.lhs > r.rhs:
                r = r.reversed
        elif r.lhs.is_number:
            r = r.reversed
        elif tuple(ordered(args)) != args:
            r = r.reversed

        LHS_CEMS = getattr(r.lhs, 'could_extract_minus_sign', None)
        RHS_CEMS = getattr(r.rhs, 'could_extract_minus_sign', None)

        if isinstance(r.lhs, BooleanAtom) or isinstance(r.rhs, BooleanAtom):
            return r

        # Check if first value has negative sign
        if LHS_CEMS and LHS_CEMS():
            return r.reversedsign
        elif not r.rhs.is_number and RHS_CEMS and RHS_CEMS():
            # Right hand side has a minus, but not lhs.
            # How does the expression with reversed signs behave?
            # This is so that expressions of the type
            # Q.eq(x, -y) and Q.eq(-x, y)
            # have the same canonical representation
            expr1, _ = ordered([r.lhs, -r.rhs])
            if expr1 != r.lhs:
                return r.reversed.reversedsign

        return r

    @property
    def binary_symbols(self):
        return set()

    # methods

    def as_Relational(self):
        return self.func.as_Relational(*self.args)

    def _eval_ask(self, assumptions):
        rel = self.simplify()
        return rel.func.eval(rel.args, assumptions)

    def refine(self, assumptions=True):
        """
        Rearrange the equation by removing the common term on both sides.

        See ``refine_equation()`` in ``relation/refine_equation`` module.
        """
        return refine(self, assumptions)

    def _eval_refine(self, assumptions):
        from .eqntools import refine_equation
        return refine_equation(self, assumptions)

    def simplify(self, equation=True, termname="all", **kwargs):
        """
        Simplify *self*, without evaluating to boolean value.

        Parameters
        ==========

        equation : bool, optional
            If ``False``, terms are simplified separately. You can
            decide which term to be separated by *termname* argument.
            If ``True``, not only term are simplified but they are
            rearranged to give canonical form.

        termname : "all", "lhs" or "rhs", optional
            Specify which term the rewriting will be done. Default is
            "all".

        kwargs : keyword arguments passed to ``simplify`` method

        """
        # do not call simplify function since it does not allow
        # custom kwargs.
        from sympy.core.function import count_ops
        from .eqntools import eqnsimp

        # Default options. If aforementioned problem of simplify function
        # is fixed, this can be removed.
        options = dict(
            ratio=1.7,
            measure=count_ops,
            rational=False,
            inverse=False,
            doit=True
        )
        options.update(kwargs)

        lhs, rhs = self.args

        if equation:
            return eqnsimp(self.func, lhs, rhs, **options)

        if termname in ("all", "lhs"):
            lhs = self.lhs.simplify(**options)
        if termname in ("all", "rhs"):
            rhs = self.rhs.simplify(**options)
        return self.func(lhs, rhs)

    def solve(self, symbol=None, domain=S.Complexes):
        """
        Solve the equation with respect to given symbol and domain.

        Se ``solveeqn()`` in ``relation/eqntools`` module.
        """
        from .eqntools import solveeqn
        return solveeqn(self, symbol, domain)

    # override operations

    def __pos__(self):
        return self

    def __neg__(self):
        return -1*self

    def __add__(self, other):
        other = _sympify(other)
        return relop_add(self, other)

    def __radd__(self, other):
        other = _sympify(other)
        return relop_add(other, self)

    def __sub__(self, other):
        other = _sympify(other)
        return relop_add(self, -other)

    def __rsub__(self, other):
        other = _sympify(other)
        return relop_add(other, -self)

    def __mul__(self, other):
        other = _sympify(other)
        return relop_mul(self, other)

    def __rmul__(self, other):
        other = _sympify(other)
        return relop_mul(other, self)

    def __pow__(self, other):
        other = _sympify(other)
        return relop_pow(self, other)

    def __rpow__(self, other):
        other = _sympify(other)
        return relop_pow(other, self)

    def __truediv__(self, other):
        other = _sympify(other)
        return relop_mul(self, other**-1)

    def __rtruediv__(self, other):
        other = _sympify(other)
        return relop_mul(other, self**-1)

    def apply_func(self, func, *args, termname="all", **kwargs):
        """
        Apply the function on the arguments and build applied predicate
        with the result.

        Parameters
        ==========

        func : any function or class

        args : arguments passed to function

        termname : "all", "lhs" or "rhs", optional
            Specify which term the function will be applied. Default is
            "all".

        kwargs : keyword arguments passed to function

        """
        lhs, rhs = self.args
        if termname in ("all", "lhs"):
            lhs = func(self.lhs, *args, **kwargs)
        if termname in ("all", "rhs"):
            rhs = func(self.rhs, *args, **kwargs)
        return self.func(lhs, rhs)

    def apply_attr(self, name, termname="all"):
        """
        Get the attribute on the arguments and build applied predicate
        with the result.

        Parameters
        ==========

        name : str
            Name of the attribute

        termname : "all", "lhs" or "rhs", optional
            Specify which term the method will be applied. Default is
            "all".

        """
        lhs, rhs = self.args
        if termname in ("all", "lhs"):
            lhs = getattr(self.lhs, name)
        if termname in ("all", "rhs"):
            rhs = getattr(self.rhs, name)
        return self.func(lhs, rhs)

    def apply_method(self, name, *args, termname="all", **kwargs):
        """
        Apply the method on the arguments and build applied predicate
        with the result.

        Parameters
        ==========

        name : str
            Name of the method

        args : arguments passed to method

        termname : "all", "lhs" or "rhs", optional
            Specify which term the method will be applied. Default is
            "all".

        kwargs : keyword arguments passed to method

        """
        lhs, rhs = self.args
        if termname in ("all", "lhs"):
            lhs = getattr(self.lhs, name)(*args, **kwargs)
        if termname in ("all", "rhs"):
            rhs = getattr(self.rhs, name)(*args, **kwargs)
        return self.func(lhs, rhs)

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            lhs_attr = getattr(self.lhs, name)
            rhs_attr = getattr(self.rhs, name)
            if not (callable(lhs_attr) and callable(rhs_attr)):
                return partial(self.apply_attr, name)
            elif (callable(lhs_attr) and callable(rhs_attr)):
                return partial(self.apply_method, name)
            else:
                raise TypeError("Inconsistent methods are called on each side.")

    # override Basic methods

    def rewrite(self, *args, termname="all", **kwargs):
        """
        Apply ``rewrite`` method on the arguments and build applied
        predicate with the result.

        Parameters
        ==========

        args : arguments passed to ``rewrite`` method

        termname : "all", "lhs" or "rhs", optional
            Specify which term the rewriting will be done. Default is
            "all".

        kwargs : keyword arguments passed to ``rewrite`` method

        """
        lhs, rhs = self.args
        if termname in ("all", "lhs"):
            lhs = self.lhs.rewrite(*args, **kwargs)
        if termname in ("all", "rhs"):
            rhs = self.rhs.rewrite(*args, **kwargs)
        return self.func(lhs, rhs)


from .relop import relop_add, relop_mul, relop_pow
