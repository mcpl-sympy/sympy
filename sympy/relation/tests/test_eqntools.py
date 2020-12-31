from sympy import Q, refine, solveeqn, symbols

x, y = symbols('x y')
p = symbols('p', positive=True)
n = symbols('n', negative=True)
nz = symbols('nz', nonzero=True)
z = symbols('z', zero=True)

def test_refine_eq():
    assert refine(Q.eq(2*x, 2*y)) == Q.eq(x,y)
    assert refine(Q.eq(x+1, y+1)) == Q.eq(x,y)
    assert refine(Q.eq(2**x, 2**y)) == Q.eq(x,y)
    assert refine(Q.eq(3*2**x+3, 3*2**y+3)) == Q.eq(x,y)

    assert refine(Q.eq(p*x, p*y)) == Q.eq(x,y)
    assert refine(Q.eq(n*x, n*y)) == Q.eq(x,y)
    assert refine(Q.eq(nz*x, nz*y)) == Q.eq(x,y)
    assert refine(Q.eq(z*x, z*y)) == Q.eq(z*x,z*y)

def test_refine_ineq():
    assert refine(Q.gt(-2*x, -2*y)) == Q.lt(x,y)
    assert refine(Q.gt(2**(-x), 2**(-y))) == Q.lt(x,y)

    assert refine(Q.gt(p*x, p*y)) == Q.gt(x,y)
    assert refine(Q.gt(n*x, n*y)) == Q.lt(x,y)
    assert refine(Q.gt(nz*x, nz*y)) == Q.gt(nz*x,nz*y)
    assert refine(Q.gt(z*x, z*y)) == Q.gt(z*x,z*y)

def test_solveeqn_eq():
    assert solveeqn(Q.eq(z, x+y-3), x) == Q.eq(x, -y+z+3)
