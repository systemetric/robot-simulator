import argparse
import sys
import xmlrpc.client

from vector3 import *

def _trace(text):
    """Prints a message to Standard Error for debugging - this avoids polluting the Standard Output (which is read by some processes)."""
    print("In RobotClient: " + text, file = sys.stderr)

MARKER_ARENA, MARKER_TOKEN = 'arena', 'token'
TOKEN_NONE, TOKEN_ORE, TOKEN_FOOLS_GOLD, TOKEN_GOLD = 'none', 'ore', 'fools-gold', 'gold'
marker_offsets = {
    MARKER_ARENA: 0,
    MARKER_TOKEN: 32
}

"""These classes are defined by the robocon documentation.
Their names and properties match those described there - they are initialised using a dictionary of information returned by SimVision's see() function."""
class Orientation:

    def __init__(self, corners, cameraNormal):
        cornerVectors = []
        for corner in corners:
            cornerVectors.append(constructFromDictionary(corner))
        markerPlane = Plane(cornerVectors[0], cornerVectors[1], cornerVectors[3])
        markerNormal = markerPlane.normalToPlane
        rot_yRadians = cameraNormal.angleBetween( -markerNormal )
        self.rot_x = 0
        self.rot_y = (rot_yRadians / math.pi) * 180
        self.rot_z = 0

class image:

    def __init__(self, resolution, fieldOfView, polarPoint):
        fovDegrees = fieldOfView * 180 / math.pi
        self.x = (resolution[0] / 2) + (resolution[0] * polarPoint.rot_y / fovDegrees)
        #As my image is approximated to a cirlce instead of a rectangle (for ease of calculations), the x resolution is used for both.
        self.y = (resolution[1] / 2) + (resolution[0] * polarPoint.rot_x / fovDegrees)

class world:
    """Their Z axis is our cameraNormal.
    Their Y axis is our Z axis inverted.
    Their X axis is perpendicular to both."""

    def __init__(self, cameraPosition, cameraNormal, point):
        cameraToPoint = point - cameraPosition
        #Converting from the simulation's coordinate system to the camera's coordinate system.
        cameraZAxis = cameraNormal
        cameraYAxis = Vector3(0, 0, -1)
        cameraXAxis = cameraYAxis.cross(cameraZAxis)

        self.x = cameraXAxis.dot(cameraToPoint)
        self.y = cameraYAxis.dot(cameraToPoint)
        self.z = cameraZAxis.dot(cameraToPoint)

class polar:

    def __init__(self, worldPoint):
        worldVector = Vector3(worldPoint.x, worldPoint.y, worldPoint.z)
        self.length = worldVector.magnitude
        self.rot_x = (math.atan2(worldPoint.y, worldPoint.z) / math.pi) * 180
        self.rot_y = (math.atan2(worldPoint.x, worldPoint.z) / math.pi) * 180

class Point:

    def __init__(self, resolution, fieldOfView, cameraPosition, cameraNormal, point):
        self.world = world(cameraPosition, cameraNormal, point)
        self.polar = polar(self.world)
        self.image = image(resolution, fieldOfView, self.polar)


class MarkerInfo:

    def __init__(self, id, size, teamNumber):
        self.code = id
        self.size = size
        if id <= 23:
            self.marker_type = MARKER_ARENA
            self.token_type = TOKEN_NONE
            self.offset = id
        elif id >= 32 and id <= 41:
            self.marker_type = MARKER_TOKEN
            self.token_type = TOKEN_ORE
            self.offset = id - 32
        else:
            goldOffset = id - 42
            self.marker_type = MARKER_TOKEN
            goldTeam = id // 4
            if goldTeam == teamNumber:
                self.token_type = TOKEN_GOLD
            else:
                self.token_type = TOKEN_FOOLS_GOLD
            self.offset = goldOffset % 4

class Marker:

    def __init__(self, resolution, fieldOfView, cameraPosition, cameraNormal, currentTimestamp, teamNumber, markerDictionary):
        self.info = MarkerInfo(markerDictionary["Id"], markerDictionary["Size"], teamNumber)
        markerCentrePoint = 0.5 * ( constructFromDictionary(markerDictionary["Corners"][0]) + constructFromDictionary(markerDictionary["Corners"][2]) )
        self.centre = Point(resolution, fieldOfView, cameraPosition, cameraNormal, markerCentrePoint)
        self.vertices = []
        for corner in markerDictionary["Corners"]:
            self.vertices.append(Point(resolution, fieldOfView, cameraPosition, cameraNormal, constructFromDictionary(corner)))
        self.orientation = Orientation(markerDictionary["Corners"], cameraNormal)
        self.res = resolution
        self.timestamp = currentTimestamp
    
    @property
    def dist(self):
        return self.centre.polar.length

    @property
    def rot_y(self):
        return self.centre.polar.rot_y

class Motors:
    """An interface for the motors in the RobotService."""

    def __init__(self, robotService):
        self._robotService = robotService

    def __getitem__(self, index):
        return self._robotService.getMotorPower(index)

    def __setitem__(self, index, value):
        return self._robotService.setMotorPower(index, value)

class Robot:
    """An interface for this robot's RobotService.
    Attempts to accurately replicate the API of a real robot's Robot class, to allow programs written for real robots to work with this class."""

    def __init__(self):
        """Identifies the url of the RobotService based on the arguments passed to it when the program was initialised.
        Then creates an interface with that service to match the robocon API, and yields the program until the RobotService returns."""
        parser = argparse.ArgumentParser("RobotClient")
        parser.add_argument("--url", action="store", help="The URL of of the RobotThread's xmlrpc server.")
        arguments = parser.parse_args()

        _trace("Connecting to RobotService:")
        self._robotService = xmlrpc.client.ServerProxy(arguments.url)
        self.motors = Motors(self._robotService)
        self.gpio = []
        self.servos = []
        self.zone = self._robotService.getTeamNumber()
        _trace("Connected, waiting for start.")
        self._robotService.waitForStart()
        _trace("Starting.")
    
    def print(self, message):
        """Sends a message to be printed to the Controller's Standard Output."""
        return self._robotService.print(str(message))
    
    def sleep(self, time):
        """Yields the program until the specified number of seconds have passed in the simulation."""
        _trace("Entering sleep.")
        self._robotService.sleep(time)
        _trace("Exiting sleep.")

    def see(self, res=(640, 480)):
        """Yields the program for a brief amount of simulated time depending on the resolution specified, and returns a list of visible marker objects.
        Raises an exception if an illegal resolution is specified."""
        legalResolutions = [
        (640, 480),
        (1296, 736),
        (1296, 976),
        (1920, 1088),
        (1920, 1440)
        ]
        if not ( res in legalResolutions ):
            raise RuntimeError("Invalid resolution. Resolution must be one of (640, 480), (1296, 736), (1296, 976), (1920, 1088), (1920, 1440)")

        visionDictionary = self._robotService.see(res)
        markerObjects = []
        for marker in visionDictionary["List of Markers"]:
            markerObjects.append(Marker(
                visionDictionary["Resolution"],
                visionDictionary["Field of View"],
                constructFromDictionary(visionDictionary["Camera Position"]),
                constructFromDictionary(visionDictionary["Camera Normal"]),
                visionDictionary["Timestamp"],
                self._robotService.getTeamNumber(),
                marker
            ))
        return markerObjects

    def waitForStart(self):
        """Yields the program until the simulation begins."""
        return self._robotService.waitForStart()
