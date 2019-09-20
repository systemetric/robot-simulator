import threading
import time
import random

#my modules
import SimBase
import SimArena
import SimDisplay
    
if __name__ == "__main__":
    """Main program."""
    SimBase.trace("Simulator starting.")
    #Create threads for all participants.
    SimBase.mainGate.clear()
    SimBase.trace("Creating ArenaThread.")
    SimBase.rpcThreads.append( SimArena.ArenaThread() )
    SimBase.trace("Starting ArenaThread.")
    SimBase.rpcThreads[0].start()
    #The robot rpcThreads are created by the ArenaThread. When it finishes, it'll unblock the mainGate.
    SimBase.trace("Simulator is waiting for clients to be ready to begin.")
    SimBase.mainGate.wait()
    SimBase.trace("All clients are ready to begin, entering main loop.")

    #Create the display, and enter the main loop.
    display = SimDisplay.Display()
    while SimBase.isSimulationRunning():
        for thread in SimBase.rpcThreads:
            if SimBase.theTime >= thread.wakeUpTime:
                thread.unblock()

        for robot in SimBase.robots:
            #Apply the motor forces for this step and check if the robot has left its zone.
            robot.applyMotorForce()
            if not robot.hasLeftZone:
                robot.checkIfLeftZone()

        SimBase.theTime += 1/64
        SimBase.space.step(1/64)

        display.updateDisplay()
        display.processInputs()

    #Exit main loop.
    #Unblock the ArenaThread to allow it to run post-simulation functions (namely calculating the score).
    SimBase.trace("Yielding control to [0]-Thread")
    SimBase.rpcThreads[0].unblock()
    #Once the main thread is unblocked, the Simulator and all the robot threads can shutdown.
    for thread in SimBase.rpcThreads:
        thread.shutdownAndWaitToExit()
    SimBase.trace("Simulator process ends")