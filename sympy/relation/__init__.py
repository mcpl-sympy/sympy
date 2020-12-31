"""
A module to implement mathematical binary relations [1] as predicate.

This module expands assumption module to provide predicates for
binary relations. Relation can be symbolically manipulated, evaluated
to boolean, and assumed. Also, boolean functions for advanced equation
structures such as simultaneous equations are implemented.

Previously, binary relation was dealt by ``core/relational`` module. It
was automatically evaluated to boolean when possible, which made it
impossible to symbolially manipulated. Plus, assumption module wrapped
every relation with ``Q.true`` which makes it hard to distinguish. This
module can avoid both problems since it is never evaluated to boolean
unless applied to ``ask()``.

References
==========

 .. [1] https://en.wikipedia.org/wiki/Binary_relation
"""

__all__ = ['Equal', 'GreaterThan', 'GreaterEq', 'LessThan', 'LessEq',
    'eqnsimp', 'solveeqn']

from .equality import Equal
from .inequality import GreaterThan, GreaterEq, LessThan, LessEq
from .eqntools import eqnsimp, solveeqn

from sympy.assumptions import Q
Q.eq = Equal()
Q.gt = GreaterThan()
Q.ge = GreaterEq()
Q.lt = LessThan()
Q.le = LessEq()
