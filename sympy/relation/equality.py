"""
Module for mathematical equality.
"""
from sympy.assumptions import ask, Q
from sympy.core import Add, Equality, Expr, S
from sympy.core.logic import fuzzy_and, fuzzy_bool, fuzzy_xor, fuzzy_not
from sympy.core.relational import _n2
from sympy.functions import arg
from sympy.logic.boolalg import Boolean, BooleanAtom
from sympy.simplify.simplify import clear_coefficients
from sympy.utilities.iterables import sift
from .binrel import BinaryRelation, AppliedBinaryRelation
from .relop import relop_add, relop_mul, relop_pow


class Equal(BinaryRelation):
    """
    Binary equality.

    """

    is_reflexive = True

    __name__ = "Equal" # compatibility for count_ops
    name = 'eq'
    str_name = latex_name = "="

    @property
    def handler(self):
        from .handlers.equality import EqualHandler
        return EqualHandler

    @property
    def reversed(self):
        return Q.eq

    @property
    def as_Relational(self):
        return Equality

    def _eval_relation(self, lhs, rhs):
        # logic for simple real numbers
        return lhs == rhs

    def eval(self, args, assumptions=True):
        retval = super().eval(args, assumptions)
        if retval is not None:
            return retval

        # Go through the equality logic.
        # If expressions have the same structure, they must be equal.
        lhs, rhs = args
        if not (lhs.is_Symbol or rhs.is_Symbol) and (
            isinstance(lhs, Boolean) !=
            isinstance(rhs, Boolean)):
            return False  # only Booleans can equal Booleans

        if lhs.is_infinite or rhs.is_infinite:
            if fuzzy_xor([lhs.is_infinite, rhs.is_infinite]):
                return False
            if fuzzy_xor([lhs.is_extended_real, rhs.is_extended_real]):
                return False
            if fuzzy_and([lhs.is_extended_real, rhs.is_extended_real]):
                return fuzzy_xor([lhs.is_extended_positive, fuzzy_not(rhs.is_extended_positive)])

            # Try to split real/imaginary parts and equate them
            I = S.ImaginaryUnit

            def split_real_imag(expr):
                real_imag = lambda t: (
                    'real' if t.is_extended_real else
                    'imag' if (I * t).is_extended_real else None)
                return sift(Add.make_args(expr), real_imag)

            lhs_ri = split_real_imag(lhs)
            if not lhs_ri[None]:
                rhs_ri = split_real_imag(rhs)
                if not rhs_ri[None]:
                    eq_real = Q.eq(Add(*lhs_ri['real']), Add(*rhs_ri['real']))
                    eq_imag = Q.eq(I * Add(*lhs_ri['imag']), I * Add(*rhs_ri['imag']))
                    return fuzzy_and(map(fuzzy_bool, [ask(eq_real), ask(eq_imag)]))

            # Compare e.g. zoo with 1+I*oo by comparing args
            arglhs = arg(lhs)
            argrhs = arg(rhs)
            # Guard against Eq(nan, nan) -> Falsesymp
            if not (arglhs == S.NaN and argrhs == S.NaN):
                return fuzzy_bool(ask(Q.eq(arglhs, argrhs)))

        if all(isinstance(i, Expr) for i in (lhs, rhs)):
            # see if the difference evaluates
            dif = lhs - rhs
            z = dif.is_zero
            if z is not None:
                if z is False and dif.is_commutative:  # issue 10728
                    return False
                if z:
                    return True

            n2 = _n2(lhs, rhs)
            if n2 is not None:
                return n2 == 0

            # see if the ratio evaluates
            n, d = dif.as_numer_denom()
            rv = None
            if n.is_zero:
                rv = d.is_nonzero
            elif n.is_finite:
                if d.is_infinite:
                    rv = True
                elif n.is_zero is False:
                    rv = d.is_infinite
                    if rv is None:
                        # if the condition that makes the denominator
                        # infinite does not make the original expression
                        # True then False can be returned
                        l, r = clear_coefficients(d, S.Infinity)
                        args = [_.subs(l, r) for _ in (lhs, rhs)]
                        if args != [lhs, rhs]:
                            rv = fuzzy_bool(ask(Q.eq(*args)))
                            if rv is True:
                                rv = None
            elif any(a.is_infinite for a in Add.make_args(n)):
                # (inf or nan)/x != 0
                rv = False
            if rv is not None:
                return rv


@relop_add.register(Equal, Equal)
def eq_add(rel1, rel2):
    lhs = rel1.lhs + rel2.lhs
    rhs = rel1.rhs + rel2.rhs
    return Q.eq(lhs, rhs)

@relop_add.register(Equal, Expr)
@relop_add.register(Expr, Equal)
def eq_expr_add(arg1, arg2):
    if isinstance(arg1, AppliedBinaryRelation):
        lhs = arg1.lhs + arg2
        rhs = arg1.rhs + arg2
    else:
        lhs = arg1 + arg2.lhs
        rhs = arg1 + arg2.rhs
    return Q.eq(lhs, rhs)

@relop_mul.register(Equal, Equal)
def eq_mul(rel1, rel2):
    lhs = rel1.lhs*rel2.lhs
    rhs = rel1.rhs*rel2.rhs
    return Q.eq(lhs, rhs)

@relop_mul.register(Equal, Expr)
@relop_mul.register(Expr, Equal)
def eq_expr_mul(arg1, arg2):
    if isinstance(arg1, AppliedBinaryRelation):
        lhs = arg1.lhs*arg2
        rhs = arg1.rhs*arg2
    else:
        lhs = arg1*arg2.lhs
        rhs = arg1*arg2.rhs
    return Q.eq(lhs, rhs)

@relop_pow.register(Equal, Equal)
def eq_pow(rel1, rel2):
    lhs = rel1.lhs**rel2.lhs
    rhs = rel1.rhs**rel2.rhs
    return Q.eq(lhs, rhs)

@relop_pow.register(Equal, Expr)
@relop_pow.register(Expr, Equal)
def eq_expr_pow(arg1, arg2):
    if isinstance(arg1, AppliedBinaryRelation):
        lhs = arg1.lhs**arg2
        rhs = arg1.rhs**arg2
    else:
        lhs = arg1**arg2.lhs
        rhs = arg1**arg2.rhs
    return Q.eq(lhs, rhs)
