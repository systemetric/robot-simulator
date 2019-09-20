import unittest
import math
from vector3 import *

class Vector3Test(unittest.TestCase):
    #Note to self, flushed out three typing errors, learnt the need for providing an __rmul__, added a property decorator for magnitude, added unary negative, added check for non-equal types in equivilance, and 

    def testStringRepresentation(self):
        """Tests that a vector can be represented as a string, and that a vector is not equal to it's string representation."""
        a = Vector3(1, 2, 3)
        b = "Vector3(1, 2, 3)"
        self.assertEqual(str(a), b)
        self.assertNotEqual(a, b)
        self.assertNotEqual(b, a)
    
    def testNonIntegerStringRepresentation(self):
        """Tests that a vector with arbitrary non integer components can be represented as a string."""
        a = Vector3(1.0, -2.5, math.pi)
        b = "Vector3(1.0, -2.5, " + str(math.pi) + ")"
        self.assertEqual(str(a), b)
        self.assertNotEqual(a, b)

    def testEquivalent(self):
        """Tests that two Vector3s can compared."""
        a = Vector3(1, 2, 3)
        b = Vector3(1, 2, 3)
        c = Vector3(3, 2, 1)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def testAddition(self):
        """Tests that two Vector3s can be added."""
        a = Vector3(1, 2, 3)
        b = Vector3(4, 5, 6)
        c = Vector3(5, 7, 9)
        d = Vector3(0, 0, 0)
        self.assertEqual(a + b, c)
        self.assertNotEqual(a + b, d)
        
    def testNegativeAddition(self):
        """Tests that negative Vector3s can be added."""
        a = Vector3(-1, -2, -3)
        b = Vector3(1, 2, 3)
        c = Vector3(0, 0, 0)
        d = Vector3(2, 4, 6)
        self.assertEqual(a + b, c)
        self.assertNotEqual(a + b, d)

    def testUnaryNegative(self):
        """Tests that the unary negative function multiplies the vector by a scalar -1."""
        a = Vector3(-1, -2, -3)
        b = Vector3(1, 2, 3)
        self.assertEqual(a, -b)
        self.assertNotEqual(a, -a)

    def testSubtraction(self):
        """Tests that two Vector3s can be subtracted."""
        a = Vector3(5, 7, 9)
        b = Vector3(1, 2, 3)
        c = Vector3(4, 5, 6)
        d = Vector3(0, 0, 0)
        self.assertEqual(a - b, c)
        self.assertNotEqual(a - b, d)
    
    def testNegativeSubtraction(self):
        """Tests that negative Vector3s can be subtracted."""
        a = Vector3(1, 2, 3)
        b = Vector3(-1, -2, -3)
        c = Vector3(2, 4, 6)
        d = Vector3(0, 0, 0)
        self.assertEqual(a - b, c)
        self.assertNotEqual(a - b, d)

    def testScalarMultiply(self):
        """Tests that vectors can be multiplied by a scalar."""
        a = Vector3(1, 2, 3)
        b = Vector3(3, 6, 9)
        c = Vector3(1, 2, 3)
        self.assertEqual(3 * a, b)
        self.assertEqual(a * 3, b)
        self.assertNotEqual(3 * a, c)

    def testZeroScalarMultiply(self):
        """Tests that vectors can be multiplied by the scalar 0."""
        a = Vector3(1, 2, 3)
        b = Vector3(0, 0, 0)
        self.assertEqual(0 * a, b)
        self.assertNotEqual(0 * a, a)

    def testDecimalScalarMultiply(self):
        """Tests that vectors can be multiplied by a non integer scalar."""
        a = Vector3(1, 2, 3)
        b = Vector3(1.5, 3, 4.5)
        c = Vector3(2, 3, 5)
        self.assertEqual(1.5 * a, b)
        self.assertEqual(a * 1.5, b)
        self.assertNotEqual(1.5 * a, c)

    def testMagnitude(self):
        """Tests that the magnitude of a vector can be correctly calculated."""
        a = Vector3(1, 2, 3)
        b = Vector3(-1, -2, -3)
        c = Vector3(0, 0, 0)
        d = Vector3(3, 4, 12)
        self.assertAlmostEqual(a.magnitude, math.sqrt(14))
        self.assertEqual(a.magnitude, b.magnitude)
        self.assertEqual(c.magnitude, 0)
        self.assertEqual(d.magnitude, 13)

    def testUnitVector(self):
        """Tests that the unit vector corresponding to a vector can be correctly calculated."""
        a = Vector3(3, 4, 12)
        b = Vector3(3/13, 4/13, 12/13)
        c = Vector3(0, 0, 0)
        self.assertAlmostEqual(a.unit, b)
        self.assertEqual(a.unit.magnitude, 1)
        with self.assertRaises(ZeroDivisionError):
            c.unit

    def testDot(self):
        """Tests that the dot product of a vector can be correctly calculated."""
        a = Vector3(1, 2, 3)
        b = Vector3(2, 4, 6)
        c = Vector3(1, 2, 0)
        d = Vector3(2, -1, 0)
        e = Vector3(1, 0, 0)
        f = Vector3(1, 1, 0)
        #This test caught a typing error.
        self.assertAlmostEqual(a.dot(b), a.magnitude * b.magnitude) #For parallel vectors, a.b = |a|*|b|
        self.assertEqual(c.dot(d), 0) #For perpendicular vectors, c.d = 0
        self.assertAlmostEqual(e.dot(f), e.magnitude * f.magnitude * math.cos(0.25*math.pi) ) #e.f = |e|*|f|*cos(angle)

    def testCross(self):
        """Tests that the cross product of a vector can be correctly calculated."""
        x = Vector3(1, 0, 0)
        y = Vector3(0, 1, 0)
        z = Vector3(0, 0, 1)
        zero = Vector3(0, 0, 0)
        a = Vector3(1, 1, -2)
        b = Vector3(-5, 1, 3)
        c = Vector3(5, 7, 6)
        self.assertEqual(x.cross(y), z)
        #This test caught a typing error.
        self.assertEqual(y.cross(x), -z)
        self.assertEqual(x.cross(x), zero)
        self.assertEqual(x.cross(zero), zero)
        self.assertEqual(a.cross(b), c)

    def testAngleBetween(self):
        """Tests that the angle between two vectors can be correctly calculated."""
        #Vector facing up.
        VectorA = Vector3(0, 0, 1)
        #Vectors perpendicular:
        VectorB = Vector3(1, 0, 0)
        VectorC = Vector3(-1, 0, 0)
        VectorD = Vector3(0, 1, 0)
        VectorE = Vector3(0, -1, 0)
        self.assertAlmostEqual( VectorA.angleBetween(VectorB), math.pi / 2 )
        self.assertAlmostEqual( VectorA.angleBetween(VectorC), math.pi / 2 )
        self.assertAlmostEqual( VectorA.angleBetween(VectorD), math.pi / 2 )
        self.assertAlmostEqual( VectorA.angleBetween(VectorE), math.pi / 2 )
        #Vector facing down.
        VectorF = Vector3(0, 0, -1)
        self.assertAlmostEqual( VectorA.angleBetween(VectorF), math.pi )
        self.assertAlmostEqual( VectorF.angleBetween(VectorA), math.pi )
        #Longer vector at 45 degrees.
        VectorG = Vector3(0, 1, 1)
        #This test caught a typing error.
        self.assertAlmostEqual( VectorA.angleBetween(VectorG), math.pi / 4)
        self.assertAlmostEqual( VectorG.angleBetween(VectorA), math.pi / 4)

    def testRotateAroundZ(self):
        """Tests that a vector can be correctly rotated by an angle."""
        VectorA = Vector3(0.125, 0, 0)
        VectorB = Vector3(0, 0.125, 0)
        VectorC = Vector3(-0.125, 0, 0)
        VectorD = Vector3(0, -0.125, 0)
        #it is impossible to assert a vector is almost equal to a vector, so the vectors are subtracted from one another and the magnitude is taken
        self.assertEqual( (VectorA.rotateAroundZ(0) - VectorA).magnitude, 0 )
        self.assertAlmostEqual( (VectorA.rotateAroundZ(math.pi / 2) - VectorB).magnitude, 0 )
        self.assertAlmostEqual( (VectorA.rotateAroundZ(-math.pi) - VectorC).magnitude, 0 )
        self.assertAlmostEqual( (VectorA.rotateAroundZ(-math.pi / 2) - VectorD). magnitude, 0 )



class PlaneTest(unittest.TestCase):

    def testPlaneFacingCamera(self):
        """Tests that it can be calculated if a plane is facing the camera."""
        planeA = Plane( Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0) ) #facing upwards
        cameraPositionA = Vector3(0, 0, 1)
        cameraPositionB = Vector3(0, 0, 0) #inside the planes (does not face either)
        planeB = Plane( Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, -1, 0) ) #facing downwards
        self.assertTrue( planeA.isFacingCamera(cameraPositionA) )
        self.assertFalse( planeA.isFacingCamera(-cameraPositionA) )
        self.assertFalse( planeA.isFacingCamera(cameraPositionB) )
        self.assertFalse( planeB.isFacingCamera(cameraPositionB) )
    
    def testPlaneObstructingPoint(self):
        """Tests that it can be calculated if a bounded plane obstructs the line between two points."""
        #A square normal to the Z axis, centred on 0, 0, 0, with side length 2.
        plane = Plane( Vector3(-1, -1, 0), Vector3(1, -1, 0), Vector3(-1, 1, 0) )
        #A point above the plane.
        cameraPositionA = Vector3(0, 0, 1)
        #A point directly under the camera, below the plane.
        pointA = Vector3(0, 0, -1)
        #A point directly under the camera, above the plane.
        pointB = Vector3(0, 0, 0.5)
        #A point directly above the camera, above the plane.
        pointC = Vector3(0, 0, 2)
        #A point far beyond the bounds of the plane, below the plane.
        pointD = Vector3(0, 10, -1)
        self.assertTrue( plane.isObstructingPoint(pointA, cameraPositionA) )
        self.assertFalse( plane.isObstructingPoint(pointB, cameraPositionA) )
        self.assertFalse( plane.isObstructingPoint(pointC, cameraPositionA) )
        self.assertFalse( plane.isObstructingPoint(pointD, cameraPositionA) )
        
        #A point to the side of the plane.
        cameraPositionB = Vector3(0, 2, 0)
        #A point on the other side of the plane.
        pointE = Vector3(0, -2, 0)
        self.assertFalse( plane.isObstructingPoint(pointE, cameraPositionB) )
