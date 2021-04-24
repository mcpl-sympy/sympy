from sympy import Eqn, symbols

x, y, z = symbols('x y z')


def test_Equation_add():
    assert Eqn(x, y) + Eqn(y, z) == Eqn(x + y, y + z)
    assert Eqn(x, y) + z == Eqn(x + z, y + z)
    assert z + Eqn(x, y) == Eqn(x + z, y + z)
    assert Eqn(x, y) + 1 == Eqn(x + 1, y + 1)
    assert 1 + Eqn(x, y) == Eqn(x + 1, y + 1)


def test_Equation_subtract():
    assert Eqn(x, y) - Eqn(y, z) == Eqn(x - y, y - z)
    assert Eqn(x, y) - z == Eqn(x - z, y - z)
    assert z - Eqn(x, y) == Eqn(z - x, z - y)
    assert Eqn(x, y) - 1 == Eqn(x - 1, y - 1)
    assert 1 - Eqn(x, y) == Eqn(1 - x, 1 - y)


def test_Equation_multiply():
    assert Eqn(x, y) + Eqn(y, z) == Eqn(x + y, y + z)
    assert Eqn(x, y) + z == Eqn(x + z, y + z)
    assert z + Eqn(x, y) == Eqn(x + z, y + z)
    assert Eqn(x, y) + 1 == Eqn(x + 1, y + 1)
    assert 1 + Eqn(x, y) == Eqn(x + 1, y + 1)


def test_Equation_divide():
    assert Eqn(x, y) / Eqn(y, z) == Eqn(x / y, y / z)
    assert Eqn(x, y) / z == Eqn(x / z, y / z)
    assert z / Eqn(x, y) == Eqn(z / x, z / y)
    assert Eqn(x, y) / 1 == Eqn(x, y)
    assert 1 / Eqn(x, y) == Eqn(1 / x, 1 / y)
