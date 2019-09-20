import RobotClient
import random

print("LazyRobot started!")
robot = RobotClient.Robot()

while True:
   robot.sleep( random.randint(1, 20) )
