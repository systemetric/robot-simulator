import sys
import threading
import xmlrpc.server
import pymunk
import json
import math
import random

"""Global Variables"""
#The pymunk "world". This is initialised when the ArenaThread is created, but stored here for visibility.
space = None
#The current time of the simulation (in seconds).
theTime = 0
#The time at which the simulation ends (in seconds).
endTime = 180
#A threading event used to block the main (Simulator) thread.
mainGate = threading.Event()
#A list of all running rpcThreads.
rpcThreads = []
#A list of all the print statements for the controller to print in the next timestep.
pendingOutput = []
#Lists containing all the bodies of the respective type that are currently in the arena.
wallSegments = []
tokens = []
robots = []
zones = []

"""Global Helper Functions"""
def trace(text):
    """Print a message to Standard Error, to avoid polluting the Standard Output (which is read by some processes)."""
    id = threading.current_thread().getName()
    line = "In " + id + " at " + str(theTime) + ": " + str(text)
    print(line, file = sys.stderr)

def isSimulationRunning():
    """Returns if the simulation has finished running."""
    return theTime < endTime

def sanitiseInput(input, datatype, default, minimum = None, maximum = None):
    """Takes an input and ensures that it is the correct datatype, and that it is within the allowable range.
    If it is not, the value will be set to an allowable value, to allow the simulation to run."""
    assert( (minimum == None) or (maximum == None) or (minimum < maximum) )
    assert( (minimum == None) or (minimum <= default) )
    assert( (maximum == None) or (maximum >= default) )
    if isinstance(input, datatype):
        if minimum != None:
            if input < minimum:
                return minimum
        if maximum != None:
            if input > maximum:
                return maximum
        return input
    else:
        return default

"""Threading"""
class RpcThread(threading.Thread):
    """A base class for the ArenaThread and RobotThread classes - this contains all the common functions for blocking, unblocking and stopping a thread."""
    
    def __init__(self):
        """Initialises the thread, creating common attributes to all threads.
        The server is created differently depending on the type of thread, so is set to None for now."""
        super().__init__(daemon = True, \
                         name="[{}]-Thread".format(len(rpcThreads)))
        #daemon makes the program run more "in the background", and the thread is named based on when it was added (first thread is "[0] thread", etc)
        self.wakeUpTime = 0
        self.gate = threading.Event()
        self.server = None
        self.isReadyToStart = False

    def block(self):
        """Block the thread, and unblocks the main thread."""
        self.gate.clear()
        trace("Yielding control to MainThread")
        mainGate.set()
        self.gate.wait()
        trace("Receiving control from MainThread")
        

    def unblock(self):
        """Unblocks the thread, blocking the main thread (unless the simulation has ended)."""
        mainGate.clear()
        self.gate.set()
        mainGate.wait()

    def shutdownAndWaitToExit(self):
        """Exits the thread cleanly, yielding the program until the shutdown is complete."""
        trace("Releasing " + self.name + " to shut down.")
        self.gate.set()
        self.server.shutdown()
        self.join()
        trace(self.name + " has shut down.")
        #For some reason, the function for "cleanly terminate thread" is "join".

"""Pymunk Body Classes"""
#The rotation corresponding to each team.
#For example, relative to an object created for team 0, an object created for team 1 is rotated -90 degrees about the origin.
_teamAngles = {
    0 : 0,
    1 : math.pi / -2,
    2 : math.pi,
    3 : math.pi / 2
}

class Robot(pymunk.Body):
    """This class is derived from the body class, and in addition to the base pymunk body attributes, it contains all
    the information regarding that robot's configuration options, and some flags on if the robot has left it's zone or is moving.
    It initialises itself using the config file accociated with it's team number."""

    def __init__(self, teamNumber):
        """Initialises the body using information from the config file accociated with that teamNumber."""
        super().__init__(body_type = pymunk.Body.DYNAMIC)
        self.teamNumber = teamNumber
        with open("Robot " + str(teamNumber) + " Config.json") as RobotConfig:
            InitialiseDictionary = json.loads(RobotConfig.read())[0]

            #Create the pymunk body and shape:
            #pymunk shapes cannot have a width or length of 0, so the minimum footprint is 1cm by 1cm.
            self.width = sanitiseInput(InitialiseDictionary["Width"], float, 0.3, 0.01, 0.4)
            self.length = sanitiseInput(InitialiseDictionary["Length"], float, 0.4, 0.01, 0.4)
            self.height = sanitiseInput(InitialiseDictionary["Height"], float, 0.4, 0)
            #These constants are useful when constructing the object:
            halfWidth = self.width / 2
            halfLength = self.length / 2
            startingOffset = pymunk.Vec2d(
                sanitiseInput(InitialiseDictionary["Starting Position"][0], float, 0, -0.25 + halfLength, 5.75 - halfLength),
                sanitiseInput(InitialiseDictionary["Starting Position"][1], float, 0, -3 + halfWidth, 3 - halfWidth)
            )
            self.position = (pymunk.Vec2d(-2.75, 0) + startingOffset).rotated(_teamAngles[teamNumber])
            self.angle = _teamAngles[teamNumber]
            points = [(-halfLength, -halfWidth), (halfLength, -halfWidth), (halfLength, halfWidth), (-halfLength, halfWidth)]
            box = pymunk.Poly(self, points)
            #The mass can't be set until the shape is constructed, so this is stored as a variable for later.
            #It also can't be 0, so the minimum weight is 1 gram.
            box.mass = sanitiseInput(InitialiseDictionary["Mass"], float, 1, 0.001)
            #For whatever reason, collision_types have to be integers. I've decided that collision_type 1 is for robots, and 2 is for tokens.
            box.collision_type = 1
            box.elasticity = 0
            box.friction = 0.5
            space.add(self, box)

            #Initialise robot specific values:
            self._axleLength = sanitiseInput(InitialiseDictionary["Distance Between Wheels"], float, 0, 0)
            baseMaxPower = sanitiseInput(InitialiseDictionary["Maximum Motor Power"], float, 1, 0)
            powerOffset = sanitiseInput(InitialiseDictionary["Motor Noise Range"], float, 0, 0)
            random.seed()
            self._leftMaxPower = baseMaxPower + random.uniform(0, powerOffset / 2)
            self._rightMaxPower = baseMaxPower + random.uniform(0, powerOffset / 2)
            #These will be set when the service recieves a call to update the motor power.
            self.leftPower = 0
            self.rightPower = 0

            #Initialise camera values:
            self.cameraHeight = sanitiseInput(InitialiseDictionary["Camera Height"], float, 0.3, 0)
            #The field of view is input as the full angle between opposite sides in degrees, but used as the half angle in radians.
            #To make this conversion, the input is multiplied by math.pi/360.
            self.fieldOfView = sanitiseInput(InitialiseDictionary["Camera Field of View"], float, 45, 0, 360)  * math.pi / 360
            self.markerPixelsMinimum = sanitiseInput(InitialiseDictionary["Marker Pixels Minimum"], int, 0, 0)
            self.markerPixelsNoise = sanitiseInput(InitialiseDictionary["Marker Pixels Noise Range"], int, 0, 0)
            self.isIgnoringMotionBlur = sanitiseInput(InitialiseDictionary["Ignore Motion Blur"], bool, False)
            self.hasLeftZone = False

            robots.append(self)

    @property
    def isMoving(self):
        """Returns if the object is moving.
        Small thresholds are acceptable, as objects in pymunk usually take a while to stop moving entirely."""
        return self.velocity.length > 0.02 or self.angular_velocity > 0.05

    def applyMotorForce(self):
        """Applies the motor forces to the robot body."""
        leftMotorPower = ( self.leftPower / 100 ) * self._leftMaxPower
        self.apply_force_at_local_point( (leftMotorPower, 0), (0, self._axleLength/2) )
        rightMotorPower = ( self.rightPower / 100 ) * self._rightMaxPower
        self.apply_force_at_local_point( (rightMotorPower, 0), (0, self._axleLength/-2) )

    def checkIfLeftZone(self):
        """Checks if the robot is outside its zone, and updates the flag if it is."""
        zone = zones[self.teamNumber]
        for shape in zone.shapes:
            zoneBB = shape.cache_bb()
            for shapeInfo in space.shape_query(shape):
                body = shapeInfo.shape.body
                if body == self:
                    #if the shape has entirely left the zone
                    for robotShape in body.shapes:
                        if not( zoneBB.contains(robotShape.cache_bb()) ):
                            self.hasLeftZone = True

class WallSegment(pymunk.Body):
    """This class is derived from the body class, and in addition to the base pymunk body attributes, it contains
    the id of the wall segment and a list of timestamps the four robots last saw it at."""
    def __init__(self, segmentId, offset, teamSide):
        super().__init__(body_type = pymunk.Body.STATIC)
        rotation = _teamAngles[teamSide]
        self.position = pymunk.Vec2d(-3, offset - 2.5 )
        self.position = self.position.rotated(rotation)
        self.angle = rotation

        #Centred on the middle of the side pointing towards the arena.
        halfLength = 0.5
        width = 0.1
        points = [(-width, -halfLength), (-width, halfLength), (0, halfLength), (0, -halfLength)]
        box = pymunk.Poly(self, points)
        space.add(self, box)
        wallSegments.append(self)
        self.id = segmentId
        self.lastSeenList = [-5, -5, -5, -5]

class Zone(pymunk.Body):
    """This class is derived from the body class, and in addition to the base pymunk body attributes, it contains
    the team accociated with it, and a function to return a list of all the tokens fully within it's bounds."""
    def __init__(self, teamNumber):
        super().__init__(body_type = pymunk.Body.STATIC)
        rotation = _teamAngles[teamNumber]
        self.teamNumber = teamNumber

        #Half of the sensor zone exists inside the wall - this is to ensure tokens stay in the sensor even when pushed up against the wall.
        self.position = pymunk.Vec2d(-3, 0)
        self.position = self.position.rotated(rotation)
        self.angle = rotation

        halfWidth = 1
        halfLength = 0.5
        points = [(-halfLength, -halfWidth), (halfLength, -halfWidth), (halfLength, halfWidth), (-halfLength, halfWidth)]
        box = pymunk.Poly(self, points)
        box.sensor = True
        space.add(self, box)
        zones.append(self)

    def getTokensInZone(self):
        """Returns a list of all tokens fully contained within the zone (as opposed to just touching)."""
        validTokens = []
        for shape in self.shapes:
            zoneBB = shape.cache_bb()
            for shapeInfo in space.shape_query(shape):
                body = shapeInfo.shape.body
                if isinstance(body, Token):
                    #must be entirely contained within zone
                    for tokenShape in body.shapes:
                        if zoneBB.contains(tokenShape.cache_bb()):
                            validTokens.append(body)
        return validTokens

class Token(pymunk.Body):
    """This class is derived from the body class, and in addition to the base pymunk body attributes, it contains
    the id of the token, corresponding type, and a list of timestamps the four robots last saw it at. It also contains
    a function which returns who and what the token is currently scoring for.
    """    
    def __init__(self, TokenId, TokenType, XPosition, YPosition):
        super().__init__(body_type = pymunk.Body.DYNAMIC)
        #radius is a useful constant for construction purposes - it represents the distance from the centre of the box to an edge
        radius = 0.055
        self.position = (XPosition, YPosition)
        points = [(-radius, -radius), (radius, -radius), (radius, radius), (-radius, radius)]
        box = pymunk.Poly(self, points)
        box.collision_type = 2
        #For whatever reason, collision_types have to be integers. I've decided that collision_type 1 is for robots, and 2 is for tokens.
        box.mass = 0.02
        box.elasticity = 0
        box.friction = 0.5
        space.add(self, box)
        tokens.append(self)
        self.id = TokenId
        self.type = TokenType
        self.lastSeenList = [-5, -5, -5, -5]

    def getScore(self, robotCollisions):
        """Takes a list of all current collisions between robots and tokens, and returns a tuple containing the number of
        points the token is worth, and the team that those points are being scored for. If the token is not scoring for anyone, it scores
        0 points for team 0.
        
        As per the rules, tokens score for one team only, and for the highest (absolute) score they are valid for. If two robots are
        touching a token, neither team can score points for "controlling" it."""
        #List of tuples of the score value, and the team that it would be awarded to.
        potentialScores = []

        for listOfCollisionsForARobot in robotCollisions:
            robotNumber = robotCollisions.index(listOfCollisionsForARobot)
            if self.id in listOfCollisionsForARobot:
                if self.type == "Ore":
                    potentialScores.append( (1, robotNumber) )
                elif self.type == "Team " + str(robotCollisions.index(listOfCollisionsForARobot)) + " Gold":
                    potentialScores.append( (3, robotNumber) )
                else:
                    #Must be a different team's gold.
                    potentialScores.append( (-1, robotNumber) )
        
        if len(potentialScores) > 1:
            #Multiple robots touching token, all "controlling" scores invalid.
            potentialScores = []

        for zone in zones:
            if self in zone.getTokensInZone():
                if self.type == "Ore":
                    potentialScores.append( (5, zone.teamNumber) )
                elif self.type == "Team " + str(zone.teamNumber) + " Gold":
                    potentialScores.append( (7, zone.teamNumber) )
                else:
                    #Must be a different team's gold.
                    potentialScores.append( (-2, zone.teamNumber) )

        highestScore = (0, 0)
        for potentialScore in potentialScores:
            if abs(potentialScore[0]) > abs(highestScore[0]):
                highestScore = potentialScore

        return highestScore

    @property
    def isMoving(self):
        """Returns if the object is moving.
        Small thresholds are acceptable, as objects in pymunk usually take a while to stop moving entirely."""
        return self.velocity.length > 0.02 or self.angular_velocity > 0.05
