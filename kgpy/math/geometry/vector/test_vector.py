
import pytest
from typing import List, Union
from numbers import Real
import numpy as np
import astropy.units as u
import quaternion as q

from kgpy.math import Vector

__all__ = ['TestVector']

t = (0, 1, 0.0, 1.0)


@pytest.mark.parametrize('x', t)
@pytest.mark.parametrize('y', t)
@pytest.mark.parametrize('z', t)
@pytest.mark.parametrize('unit', [
    1,
    u.mm
])
class TestVector:

    def test__init__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Test the constructor by confirming that the Vector.X property is of the correct type, and that every component
        of the vector was set to the correct value.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        v = Vector([x, y, z] * unit)
        assert isinstance(v.X, u.Quantity)

        assert v.x == x * unit
        assert v.y == y * unit
        assert v.z == z * unit

    def test__eq__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Test the equality operator of the Vector object.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        # Create two vectors with identical components
        v0 = Vector([x, y, z] * unit)
        v1 = Vector([x, y, z] * unit)

        # Check that the two vectors are equal
        assert v0 == v1

        # Create another vector with different components than the first two
        v2 = Vector([x + 1, y - 1, z] * unit)

        # Check that this vector is not equal to the original vector
        assert v0 != v2

        # If all three components of the Vector is zero check scalar equality
        if x == y == z:
            assert v0 == x * unit

    def test__neg__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Check the negation operation of the Vector object
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        # Create test vector
        v0 = Vector([z, y, x] * unit)

        # Test negation operation
        v = -v0

        # Assert that every component was negated properly
        assert v.x == -v0.x
        assert v.y == -v0.y
        assert v.z == -v0.z

    def test__add__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Check the addition operator of the Vector object.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        # Declare two vectors to add together
        v0 = Vector([x, y, z] * unit)
        v1 = Vector([z, y, x] * unit)

        # Execute test addition operation
        v = v0 + v1

        # Check if the result of the addition operation is what we expected
        assert v.x == v0.x + v1.x
        assert v.y == v0.y + v1.y
        assert v.z == v0.z + v1.z

    def test__sub__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Check the subtraction operator of the Vector object.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        # Declare two vectors to add together
        v0 = Vector([x, y, z] * unit)
        v1 = Vector([z, y, x] * unit)

        # Execute test addition operation
        v = v0 + v1

        # Check if the result of the addition operation is what we expected
        assert v.x == v0.x + v1.x
        assert v.y == v0.y + v1.y
        assert v.z == v0.z + v1.z

    @pytest.mark.parametrize('a', [
        1,
        0,
    ])
    def test__mul__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity], a: Real):
        """
        Test the multiplication operator of the Vector object.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :param a: Factor to scale the Vector by.
        :return: None
        """

        # Append units onto the scalar factor.
        a = a * unit

        # Create vector
        v0 = Vector([x, y, z] * unit)

        # Execute test multiplication operation
        v = a * v0

        # Check that the scalar was multiplied by each component
        assert v.x == a * v0.x
        assert v.y == a * v0.y
        assert v.z == a * v0.z

        # Execute reverse multiplication test
        v = v0 * a

        # Check that the scalar was multiplied by each component
        assert v.x == a * v0.x
        assert v.y == a * v0.y
        assert v.z == a * v0.z

    def test_dot(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):

        # Create two test vectors
        a = Vector([x, y, z] * unit)
        b = Vector([x + z, y + x, z + y] * unit)

        # Test the dot product using the definition
        r = a.dot(b)
        assert r == a.x * b.x + a.y * b.y + a.z * b.z

    def test_cross(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):

        # Create two test vectors
        a = Vector([x, y, z] * unit)
        b = Vector([x + z, y + x, z + y] * unit)

        # Execute the test cross product
        v = a.cross(b)

        # Test the result using the definition of the cross product
        assert v.x == (a.y * b.z - a.z * b.y)
        assert v.y == -(a.x * b.z - a.z * b.x)
        assert v.z == (a.x * b.y - a.y * b.x)

    a_0 = (0, np.pi / 4)

    @pytest.mark.parametrize('a', a_0)
    @pytest.mark.parametrize('b', a_0)
    @pytest.mark.parametrize('c', a_0)
    def test_rotate(self, x: Real, y: Real, z: Real, a: Real, b: Real, c: Real, unit: Union[Real, u.Quantity]):

        # Create test vector
        X1 = Vector([x, y, z] * unit)

        # Create forward and inverse rotation quaternions
        Q1 = q.from_euler_angles(a, b, c)
        Q2 = q.from_euler_angles(-c, -b, -a)

        # Rotate and unrotate the vector
        X2 = X1.rotate(Q1).rotate(Q2)

        # Check that the result is very close to the original vector
        assert (X2 - X1).mag < 1e-15 * unit

    def test_mag(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):

        # Create test vector
        a = Vector([x, y, z] * unit)

        # Calculate the test magnitude
        m = a.mag

        # Compare to the definition of magnitude
        assert m == np.sqrt((x * x + y * y + z * z) * unit * unit)

    def test_isclose(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):

        # Create test vector
        a = Vector([x, y, z] * unit)

        # Create second vector with small changes
        err = 1e-17
        b = Vector([x + err, y - err, z] * unit)

        # Test if the two Vectors have close to the same value
        assert a.isclose(b)

        # Create a third Vector with large changes
        c = Vector([x + 1, y + 1, z + 1] * unit)

        # Test that the two vectors are not close
        assert not a.isclose(c)

    def test__array__(self, x: Real, y: Real, z: Real, unit: Union[Real, u.Quantity]):
        """
        Test the capability to cast a Vector to a numpy.ndarray. This operation is only allowed for dimensionless
        Vectors.
        :param x: x-component of the Vector
        :param y: y-component of the Vector
        :param z: z-component of the Vector
        :param unit: units associated with the Vector
        :return: None
        """

        # If the Vector is dimensionless, we expect to be able to cast it to an np.ndarray, otherwise we expect the
        # __array__ function to throw a type error.
        if isinstance(unit, Real):

            # Check that dimensionless vector casts to the same value as a numpy array
            v0 = Vector([x, y, z] * unit)
            a0 = v0.__array__()
            b0 = np.array([x, y, z])
            assert np.all(a0 == b0)

            # Check that we can make the above test fail by changing the value of the numpy array
            v0 = Vector([x, y, z] * unit)
            a0 = v0.__array__()
            b0 = np.array([x, y, z + 1])
            assert not np.all(a0 == b0)

        elif isinstance(unit, u.Quantity):

            # Check that converting a vector with dimensions throws a TypeError
            v0 = Vector([x, y, z] * u.m)
            with self.assertRaises(TypeError):
                v0.__array__()