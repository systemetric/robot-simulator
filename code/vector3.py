import math

class Vector3:
    """An object that represents a vector in 3D space."""

    def __init__(self, xComponent, yComponent, zComponent):
        self.x = xComponent
        self.y = yComponent
        self.z = zComponent

    """Defining these functions overloads their respective python operators, allowing me to use =, +, -, * and the str() function on Vector3 objects."""
    def __str__(self):
        """Returns a string representation of the vector, allowing it to be print()ed or similar."""
        return "Vector3(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

    def __eq__(self, other):
        """First, checks if the other object is a Vector3.
        If they are, it compares the components of the two vectors to see if the vectors are equivalent."""
        if isinstance(other, Vector3):
            return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)
        else:
            return False

    def __add__(self, otherVector3):
        """Adds the second vector to the first one."""
        return Vector3(self.x + otherVector3.x, self.y + otherVector3.y, self.z + otherVector3.z)
    
    def __sub__(self, otherVector3):
        """Subtracts the second vector from the first one."""
        return Vector3(self.x - otherVector3.x, self.y - otherVector3.y, self.z - otherVector3.z)

    def __neg__(self):
        """Creates a vector multiplied by the scalar constant -1."""
        return Vector3(self.x * -1, self.y * -1, self.z * -1)

    def __mul__(self, constant):
        """Multiply the vector by a scalar constant:
        Vector3 * Constant"""
        return Vector3(self.x * constant, self.y * constant, self.z * constant)
    
    def __rmul__(self, constant):
        """Multiply a scalar constant by the vector:
        Constant * Vector3"""
        return Vector3(self.x * constant, self.y * constant, self.z * constant)

    @property
    def magnitude(self):
        """Returns the magnitude of the vector."""
        return math.sqrt( (self.x ** 2) + (self.y ** 2) + (self.z ** 2) )

    @property
    def unit(self):
        """Returns the unit vector with the same direction as the vector."""
        vectorMagnitude = self.magnitude
        if vectorMagnitude == 0:
            raise ZeroDivisionError("Attempted to get the direction of a null vector.")
        else:
            return Vector3( self.x / vectorMagnitude, self.y / vectorMagnitude, self.z / vectorMagnitude )
    
    def dot(self, otherVector3):
        """Calculates the dot product of a vector with another vector."""
        return (self.x * otherVector3.x) + (self.y * otherVector3.y) + (self.z * otherVector3.z)
    
    def cross(self, otherVector3):
        """Calculates the cross product of a vector with another vector."""
        return Vector3(
            (self.y * otherVector3.z) - (self.z * otherVector3.y),
            (self.z * otherVector3.x) - (self.x * otherVector3.z),
            (self.x * otherVector3.y) - (self.y * otherVector3.x)
        )
    
    def angleBetween(self, vectorB):
        """Returns the angle in radians between two vectors."""
        return math.acos(self.dot(vectorB) / ( self.magnitude * vectorB.magnitude ) )
    
    def rotateAroundZ(self, angle):
        """Rotates the vector around the Z axis angle radians.
        The only rotations used by the function are around the Z axis, so a general function is not needed."""
        return Vector3(
            self.x * math.cos(angle) - self.y * math.sin(angle),
            self.x * math.sin(angle) + self.y * math.cos(angle),
            self.z
        )
    
    def convertToDictionary(self):
        """Converts the vector into a dictionary for the purposes of transferring it through XMLrpc."""
        return {
            "x" : self.x,
            "y" : self.y,
            "z" : self.z
        }

def constructFromDictionary(dictionary):
    """Constructs a vector3 from a dictionary containing values for "x", "y" and "z"."""
    return Vector3(dictionary["x"], dictionary["y"], dictionary["z"])

class Plane:
    """An object that represents a bounded plane in 3D space."""
    
    def __init__(self, bottomLeft, bottomRight, topLeft):
        """Takes three corners, and defines a plane in vector form (point J being the "bottom right" corner, vectors U and V
        being two vectors on the plane).
        This also finds the normal to the plane, and finds its cartesian form.
        """
        self._pointJ = bottomLeft
        self._vectorU = bottomRight - bottomLeft
        self._vectorV = topLeft - bottomLeft

    @property
    def pointJ(self):
        return  self._pointJ
    @property
    def vectorU(self):
        return  self._vectorU
    @property
    def vectorV(self):
        return  self._vectorV

    @property
    def normalToPlane(self):
        return self._vectorU.cross(self._vectorV)   

    @property
    def cartesianA(self):
        return self.normalToPlane.x
    @property
    def cartesianB(self):
        return self.normalToPlane.y
    @property
    def cartesianC(self):
        return self.normalToPlane.z
    @property
    def cartesianD(self):
        return self._pointJ.dot(self.normalToPlane)

    def isFacingCamera(self, cameraPosition):
        """The normal to the plane points OUT of the cuboid, due to the order of the corners in the plane.
        This means that if the vector from pointJ to the camera also points in that same direction, the plane is facing the camera.
        If the dot product of the two vectors is > 0, they are pointing in the same direction, so the plane is facing the camera.
        """
        return (cameraPosition - self._pointJ).dot(self.normalToPlane) > 0

    def isObstructingPoint(self, point, cameraPosition):
        """Takes a point, and the position of the camera.
        Returns True if the bounded plane obstructs the line between the point and the cameraPosition, False otherwise."""
        #First, give up if the line is parallel to the plane, to avoid dividing by 0 later.
        direction = point - cameraPosition
        if self.cartesianA * direction.x + self.cartesianB * direction.y + self.cartesianC * direction.z != 0:
            # direction * distance = cameraPosition - intersectionPoint
            lamda = (
                    ( self.cartesianD - self.cartesianA*cameraPosition.x - self.cartesianB*cameraPosition.y - self.cartesianC*cameraPosition.z )
                    / ( self.cartesianA * direction.x + self.cartesianB * direction.y + self.cartesianC * direction.z)
                    )
            #if plane of obstruction is between point and camera
            if lamda > 0 and lamda < 1:
                intersectionPoint = cameraPosition + (direction * lamda) - self._pointJ
                mu = intersectionPoint.dot(self._vectorU) / (self._vectorU.magnitude ** 2)
                if mu > 0 and mu < 1:
                    nu = intersectionPoint.dot(self._vectorV) / (self._vectorV.magnitude ** 2)
                    if nu > 0 and nu < 1:
                        return True
        return False
