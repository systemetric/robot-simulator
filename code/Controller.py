import sys
import argparse
import subprocess
import time
import xmlrpc.client

def trace(text):
    """Prints a message to Standard Error for debugging - this avoids polluting the Standard Output (which is read by some processes)."""
    print("In Controller: " + text, file = sys.stderr)

if __name__ == "__main__":
    """Main program."""
    #Construct a list of all programs to test.
    parser = argparse.ArgumentParser("RobotClient")
    parser.add_argument("--test", action="append", help="The filename of the program to test.")
    arguments = parser.parse_args()
    programsToTest = []
    if arguments.test:
        for testProgram in arguments.test:
            programsToTest.append(testProgram)

    #Start the simulator as a subprocess, then wait for it to print the URL of the ArenaThread's xmlrpc server.
    #Once the controller recieves the URL, it connects to the server and stores the connection.
    trace("Starting simulator process.")
    simulator = subprocess.Popen( ["python3", "Simulator.py"], stdout=subprocess.PIPE)
    trace("Started simulator, waiting for URL.")
    arena = None
    for line in simulator.stdout:
        text = line.decode('UTF-8').rstrip()
        #Printed lines come in as a Bytes object, and must be converted to a string.
        if text[0:12] == "Arena URL = ":
            trace("URL recieved, connecting to the arena service.")
            arena = xmlrpc.client.ServerProxy(text[12:])
            trace("Connected to arena service.")
            break

    #Starts the robot programs as subprocesses.
    robots = []
    teamNumber = 0
    for testProgram in programsToTest:
        trace("Creating robot number " + str(teamNumber))
        serviceURL = arena.createRobot(teamNumber)
        trace("Robot created, starting test program subprocess.")
        robots.append( subprocess.Popen([ "python3", testProgram, "--url", serviceURL ]) )
        trace("Test program subprocess created.")
        teamNumber += 1
    trace("All robots created, waiting for start.")
    arena.waitForStart()
    trace("Receiving control from Simulator.")
    #Main loop.
    isSimulatorRunning = True
    while isSimulatorRunning:
        trace("Yielding control to Simulator.")    
        output = arena.waitForOutput(30)
        trace("Receiving control from Simulator.")
        isSimulatorRunning = output[0]
        messages = output[1]
        for message in messages:
            print(message)
    trace("Simulation no longer running. Calculating scores.")
    #At this stage, the simulation has finished, and the simulator is waiting for a "terminate" call once the arena thread has finished.
    scores = arena.getScores()
    teamNumber = 0
    for score in scores:
        print("Team " + str(teamNumber) + " scored " + str(score) + " point(s)!")
        teamNumber = teamNumber + 1
    time.sleep(10)
    #Allow 10 seconds for the user to view the final state of the simulation.
    trace("Scores calculated, yielding control to Simulator.")
    arena.terminate()
    trace("Receiving control from Simulator.")
    #Shutdown all subprocesses cleanly.
    arena = None
    trace("Waiting for Simulator finish.")
    simulator.wait()
    trace("Simulator has finished.")
    for robot in robots:
        trace("Waiting for robot test program to finish.")
        robot.wait()
        trace("Robot test program has finished.")
    trace("All subprocesses have finished. Simulation successful.")
