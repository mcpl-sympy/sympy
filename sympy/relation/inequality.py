"""
Module for mathematical inequality.
"""
from sympy.assumptions import ask, Q
from sympy.core import Expr
from sympy.core.relational import (GreaterThan, StrictGreaterThan, LessThan,
    StrictLessThan)
from .binrel import BinaryRelation
from .equality import Equal
from .relop import relop_add, relop_mul


class InEqual(BinaryRelation):
    pass


class GreaterThan(InEqual):

    is_reflexive = False

    __name__ = "GreaterThan" # compatibility for count_ops
    name = 'gt'
    strname = latexname = ">"

    @property
    def reversed(self):
        return Q.lt

    @property
    def as_Relational(self):
        return StrictGreaterThan

    def _eval_relation(self, lhs, rhs):
        # logic for simple real numbers
        return lhs > rhs


class GreaterEq(GreaterThan):

    is_reflexive = True

    __name__ = "GreaterEq" # compatibility for count_ops
    name = 'ge'
    strname = ">="
    latexname = r"\geq"

    @property
    def reversed(self):
        return Q.le

    @property
    def as_Relational(self):
        return GreaterThan

    def _eval_relation(self, lhs, rhs):
        # logic for simple real numbers
        return lhs >= rhs


class LessThan(InEqual):

    is_reflexive = False

    __name__ = "LessThan" # compatibility for count_ops
    name = 'lt'
    strname = latexname = "<"

    @property
    def reversed(self):
        return Q.gt

    @property
    def as_Relational(self):
        return StrictLessThan

    def _eval_relation(self, lhs, rhs):
        # logic for simple real numbers
        return lhs < rhs


class LessEq(LessThan):

    is_reflexive = True

    __name__ = "LessEq" # compatibility for count_ops
    name = 'le'
    strname = "<="
    latexname = r"\leq"

    @property
    def reversed(self):
        return Q.ge

    @property
    def as_Relational(self):
        return LessThan

    def _eval_relation(self, lhs, rhs):
        # logic for simple real numbers
        return lhs <= rhs


@relop_add.register(GreaterThan, GreaterThan)
@relop_add.register(GreaterThan, Equal)
@relop_add.register(Equal, GreaterThan)
def gt_add(rel1, rel2):
    lhs = rel1.lhs + rel2.lhs
    rhs = rel1.rhs + rel2.rhs
    return Q.gt(lhs, rhs)

@relop_add.register(GreaterThan, Expr)
@relop_add.register(Expr, GreaterThan)
def gt_expr_add(arg1, arg2):
    if isinstance(arg1.func, GreaterThan):
        lhs = arg1.lhs + arg2
        rhs = arg1.rhs + arg2
    else:
        lhs = arg1 + arg2.lhs
        rhs = arg1 + arg2.rhs
    return Q.gt(lhs, rhs)

@relop_add.register(GreaterEq, GreaterEq)
@relop_add.register(GreaterEq, Equal)
@relop_add.register(Equal, GreaterEq)
def ge_add(rel1, rel2):
    lhs = rel1.lhs + rel2.lhs
    rhs = rel1.rhs + rel2.rhs
    return Q.ge(lhs, rhs)

@relop_add.register(GreaterEq, Expr)
@relop_add.register(Expr, GreaterEq)
def ge_expr_add(arg1, arg2):
    if isinstance(arg1.func, GreaterEq):
        lhs = arg1.lhs + arg2
        rhs = arg1.rhs + arg2
    else:
        lhs = arg1 + arg2.lhs
        rhs = arg1 + arg2.rhs
    return Q.ge(lhs, rhs)

@relop_add.register(LessThan, LessThan)
@relop_add.register(LessThan, Equal)
@relop_add.register(Equal, LessThan)
def lt_add(rel1, rel2):
    lhs = rel1.lhs + rel2.lhs
    rhs = rel1.rhs + rel2.rhs
    return Q.lt(lhs, rhs)

@relop_add.register(LessThan, Expr)
@relop_add.register(Expr, LessThan)
def lt_expr_add(arg1, arg2):
    if isinstance(arg1.func, LessThan):
        lhs = arg1.lhs + arg2
        rhs = arg1.rhs + arg2
    else:
        lhs = arg1 + arg2.lhs
        rhs = arg1 + arg2.rhs
    return Q.lt(lhs, rhs)

@relop_add.register(LessEq, LessEq)
@relop_add.register(LessEq, Equal)
@relop_add.register(Equal, LessEq)
def le_add(rel1, rel2):
    lhs = rel1.lhs + rel2.lhs
    rhs = rel1.rhs + rel2.rhs
    return Q.le(lhs, rhs)

@relop_add.register(LessEq, Expr)
@relop_add.register(Expr, LessEq)
def le_expr_add(arg1, arg2):
    if isinstance(arg1.func, LessEq):
        lhs = arg1.lhs + arg2
        rhs = arg1.rhs + arg2
    else:
        lhs = arg1 + arg2.lhs
        rhs = arg1 + arg2.rhs
    return Q.le(lhs, rhs)

@relop_add.register(GreaterThan, LessThan)
@relop_add.register(LessThan, GreaterThan)
def add_undetermined(rel1, rel2):
    raise TypeError("Result of (%s) + (%s) cannot be determined." % (rel1, rel2))

@relop_mul.register(InEqual, Expr)
@relop_mul.register(Expr, InEqual)
def ineq_expr_mul(arg1, arg2):
    if isinstance(arg1.func, InEqual):
        ineq, expr = arg1, arg2
    else:
        expr, ineq = arg1, arg2

    is_pos = ask(Q.positive(expr))
    is_neg = ask(Q.negative(expr))
    is_zero = ask(Q.zero(expr))

    if not any([is_neg, is_pos, is_zero]):
        # Maybe need conditional equation here
        raise ValueError("Cannot determine the sign of %s" % expr)

    lhs = ineq.lhs*expr
    rhs = ineq.rhs*expr
    if is_pos:
        return ineq.func(lhs, rhs)
    elif is_neg:
        return ineq.func.reversed(lhs, rhs)
    else:
        return Q.eq(lhs, rhs)
