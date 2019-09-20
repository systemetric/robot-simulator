import sys
import threading
import xmlrpc.server

import SimBase
import SimVision

class RobotService:
    """Handles the creation of a robot and provides an interface to the simulated robot for the RobotClient.
    Also provides a helper function for the main simulator thread to check if the robot has left its zone, and apply its motor forces."""

    def __init__(self, teamNumber):
        """Initialises the service, with its own pymunk robot body. This contains all the information regarding the robot."""
        self.robotBody = SimBase.Robot(teamNumber)

    def getTeamNumber(self):
        """Returns the team number of the robot."""
        return self.robotBody.teamNumber

    def getMotorPower(self, motorNumber):
        """Returns the power of the motor specified, or 0 if asked for a motor outside the accepted range."""
        if not SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to call a robot function when simulation had already ended.")

        if motorNumber == 1:
            return self.robotBody.leftPower
        elif motorNumber == 2:
            return self.robotBody.rightPower
        else:
            raise RuntimeError("Invalid motor number given.")

    def setMotorPower(self, motorNumber, newPower):
        """Sets the power of the robot motor specified (capping values at +-100), and returns the power it was set to."""
        if not SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to call a robot function when simulation had already ended.")

        if not ( isinstance(newPower, int) or isinstance(newPower, float) ):
            raise RuntimeError("Attempted to set motor power to non-numeric value.")

        if newPower < -100:
            newPower = -100
        elif newPower > 100:
            newPower = 100
        
        if motorNumber == 1:
            self.robotBody.leftPower = newPower
        elif motorNumber == 2:
            self.robotBody.rightPower = newPower
        else:
            raise RuntimeError("Attempted to set power of an invalid motor.")
        return newPower

    def print(self, message):
        """Adds a message to the pending output, to be printed by the Controller program when it next recieves them.
        Returns True if successful, False if the simulation has ended."""
        if not SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to call a robot function when simulation had already ended.")
        
        SimBase.pendingOutput.append("Robot " + str(self.robotBody.teamNumber) + " at " + str(SimBase.theTime) + " printed: " + message)

        return True
    
    def sleep(self, time):
        """Waits until the simulated time has increased by the specified delay, unless the simulation has already ended.
        Returns False if the simulation is no longer running, True otherwise."""
        SimBase.trace("Entering RobotService.sleep()")
        if not SimBase.isSimulationRunning():
            SimBase.trace("Exiting RobotService.sleep()")
            raise RuntimeError("Attempted to call a robot function when simulation had already ended.")

        robotThread = threading.current_thread()
        robotThread.wakeUpTime += time
        robotThread.block()

        SimBase.trace("Exiting RobotService.sleep()")
        return SimBase.isSimulationRunning()

    def see(self, res):
        """Calls the see function (providing the robot, resolution and if the image is blurred).
        Returns a dictionary that is used by the RobotClient package to create a list of Marker Objects, or False if the simulation is no longer running.
        Additionally, yields the robot program briefly depending on the resolution given."""
        if not SimBase.isSimulationRunning():
            raise RuntimeError("Attempted to call a robot function when simulation had already ended.")

        ids = SimVision.see(self.robotBody, res, self.robotBody.isMoving)

        robotThread = threading.current_thread()
        robotThread.wakeUpTime += res[0]*0.001
        robotThread.block()

        return ids

    def waitForStart(self):
        """Sets a flag to indicate the robot is ready to start, and blocks itself until the competition begins."""
        robotThread = threading.current_thread()
        robotThread.isReadyToStart = True
        robotThread.gate.clear()
        SimBase.trace("Robot waiting for start.")
        robotThread.gate.wait()
        SimBase.trace("Robot now starting.")
        return True

class RobotThread(SimBase.RpcThread):
    """A thread that handles the xmlrpc server to communicate with the robot program under test."""
    
    def __init__(self, teamNumber):
        """Creates the xmlrpc server and connects it to the RobotService.
        Unlike ArenaThread, the server is created during __init__ instead of run(). This allows getURL to be called before the server is started."""
        super().__init__()
        self.server = xmlrpc.server.SimpleXMLRPCServer( ('localhost', 0), logRequests=False )
        self.server.register_instance( RobotService(teamNumber) )

    def getUrl(self):
        """Returns the URL of the server."""
        address = self.server.server_address
        url = "http://{}:{}".format(address[0], address[1])
        return url
    
    def run(self):
        """Executed when the thread is started. Runs the xmlrpc server until it is stopped when the simulation ends."""
        self.server.serve_forever()
        self.server.server_close()
