import sys
import threading
import xmlrpc.server
import time
import pymunk
import json

#my modules
import SimBase
import SimRobot

def _tokenTypeToInteger(tokenType):
    """A helper function to convert from the type of the token to the first token with that id."""
    typeToInt = {
        "Ore" : 32,
        "Team 0 Gold" : 42,
        "Team 1 Gold" : 45,
        "Team 2 Gold" : 48,
        "Team 3 Gold" : 51
    }
    return typeToInt[tokenType]

class ArenaService:
    """Handles the creation of the arena and provides services to the Controller."""

    def __init__(self):
        """Initialises the arena, creating and configuring the space, creating a collision handler to track all active token and robot collisions,
        and populates the arena with walls, zones and tokens (but not robots)."""
        SimBase.space = pymunk.Space()
        SimBase.space.damping = 0.01

        #Set up collision handler for when a robot touches a token.
        self._scoringCollisions = []
        #This is a list, indexed by the id of the robot, and the value is a list of token ids that are colliding with that robot.
        #Since the arena doesn't know how many robots are going to be in the simulation yet, the list is populated with empty lists as robots are added.
        collisionHandler = SimBase.space.add_collision_handler(1, 2)
        collisionHandler.begin = self._robotTokenCollisionBegin
        collisionHandler.separate = self._robotTokenCollisionEnd

        #Create the walls:
        id = 0
        for teamSide in range(4):
            for offset in range(6):
                SimBase.WallSegment(id, offset, teamSide)
                id += 1
        
        #Create the zones:
        for team in range(4):
            SimBase.Zone(team)
        
        #Create the tokens:
        with open('Token Position Config.json') as TokenConfig:
            TokenList = json.loads(TokenConfig.read())
            for tokenType, tokenPositions in TokenList.items():
                currentId = _tokenTypeToInteger(tokenType)
                for tokenPosition in tokenPositions:
                    #Sanitise the two coordinates, returning False if it is not the correct datatype, and restricting the values to within the arena.
                    xPosition = SimBase.sanitiseInput(tokenPosition[0], float, False, -2.945, 2.945)
                    yPosition = SimBase.sanitiseInput(tokenPosition[1], float, False, -2.945, 2.945)
                    if isinstance(xPosition, float) and isinstance(yPosition, float):
                        SimBase.Token(currentId, tokenType, xPosition, yPosition)
                        currentId += 1

    def _robotTokenCollisionBegin(self, arbiter, space, data):
        """A function that gets bound to the CollisionHandler, which adds the token/robot pair to the list of active collisions."""
        #First, work out which of the shapes is the robot, and which is the token.
        token = None
        robot = None
        if isinstance(arbiter.shapes[0].body, SimBase.Token):
            token = arbiter.shapes[0].body
            robot = arbiter.shapes[1].body
        else:
            robot = arbiter.shapes[0].body
            token = arbiter.shapes[1].body
        self._scoringCollisions[robot.teamNumber].append(token.id)
        return True
        #This tells the collision handler to handle the physics of the collision normally.

    def _robotTokenCollisionEnd(self, arbiter, space, data):
        """A function that gets bound to the CollisionHandler, which removes the token/robot pair from the list of active collisions."""
        #First, work out which of the shapes is the robot, and which is the token.
        token = None
        robot = None
        if isinstance(arbiter.shapes[0].body, SimBase.Token):
            token = arbiter.shapes[0].body
            robot = arbiter.shapes[1].body
        else:
            robot = arbiter.shapes[0].body
            token = arbiter.shapes[1].body
        self._scoringCollisions[robot.teamNumber].remove(token.id)

    def createRobot(self, teamNumber):
        """Creates a new robot thread (which then creates a robot service and robot body), and returns the connection URL to it's xmlrpc server."""
        if not SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to create a robot when the simulation had already ended.")
        
        newThread = SimRobot.RobotThread(teamNumber)
        SimBase.rpcThreads.append(newThread)
        newThread.start()
        url = newThread.getUrl()
        self._scoringCollisions.append([])

        return url

    def getScores(self):
        """Calculates the scores of each team.
        This is done by first summing the scores of each token, and then awarding an additional point to the team of each robot that left it's zone."""
        scores = [0, 0, 0, 0]
        for token in SimBase.tokens:
            score, team = token.getScore(self._scoringCollisions)
            scores[team] += score
        
        for robot in SimBase.robots:
            if robot.hasLeftZone:
                scores[robot.teamNumber] += 1
            
        return scores

    def waitForOutput(self, time):
        """Clears the list of pending messages to send to the Controller, then waits for the simulated time to have elapsed, and then returns a tuple of
        if the simulation has finished yet, and a list of messages to print to the Standard Output."""
        SimBase.trace("Entering ArenaService.waitForOutput()")
        messagesToSend = SimBase.pendingOutput
        SimBase.pendingOutput = []

        if not SimBase.isSimulationRunning():
            SimBase.trace("Exiting ArenaService.waitForOutput()")
            return (False, messagesToSend)

        arenaThread = threading.current_thread()
        arenaThread.wakeUpTime += time
        arenaThread.block()

        SimBase.trace("Exiting ArenaService.waitForOutput()")
        return (True, messagesToSend)

    def waitForStart(self):
        """Marks the arena as ready, then waits until all other threads (the robots) are ready, then blocks itself,
        unblocking the main thread and allowing it to enter the main simulator loop."""
        SimBase.trace("Entering ArenaService.waitForStart()")
        arenaThread = threading.current_thread()
        arenaThread.isReadyToStart = True
        for thread in SimBase.rpcThreads:
            SimBase.trace("Arena is waiting for " + str(thread.name))
            while thread.isReadyToStart == False:
               time.sleep(1)
        
        SimBase.trace("All robots ready, leaving ArenaService.waitForStart()")
        arenaThread.block()
        return True

    def terminate(self):
        """If called before the simulation has ended, raises an error.
        Otherwise, blocks the thread and allows the simulator to end the simulation (and terminate this thread)."""
        if SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to terminate the ArenaThread before the simulation had ended.")
        arenaThread = threading.current_thread()
        arenaThread.block()
        return True


class ArenaThread(SimBase.RpcThread):
    """A thread that handles the xmlrpc server to communicate with the Controller."""
    
    def run(self):
        """Initialises the xmlrpc server, then prints connection details to the standard output, where they are caught by the Controller.
        Then connects the xmlrpc server to the ArenaService, and serves until stopped."""
        self.server = xmlrpc.server.SimpleXMLRPCServer( ('localhost', 0), logRequests=False )
        address = self.server.server_address
        print("Arena URL = http://{}:{}".format(address[0], address[1]))
        sys.stdout.flush() #flushing the stdout is required to allow the controller to see the message
        self.server.register_instance(ArenaService())
        self.server.serve_forever()
        self.server.server_close()
