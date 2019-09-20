import RobotClient as robot
 
MULTIPLIER_LEFT = 2
MULTIPLIER_RIGHT = 2
STARTUP_TIME = 0
SPEED_50 = 0.4
SPEED_ANGULAR_30 = 120
 
R = robot.Robot()
 
def move(distance):
    R.motors[1] = MULTIPLIER_LEFT * 50
    R.motors[2] = MULTIPLIER_RIGHT * 50
 
    R.sleep(STARTUP_TIME)
    R.sleep(distance / SPEED_50)
 
    R.motors[1] = 0
    R.motors[2] = 0
 
def turn(degrees):
    multiplier = 1
    if degrees < 0:
        multiplier = -1
    R.motors[1] = MULTIPLIER_LEFT * 30 * multiplier
    R.motors[2] = MULTIPLIER_RIGHT * -30 * multiplier
 
    R.sleep(abs(degrees) / SPEED_ANGULAR_30)
 
    R.motors[1] = 0
    R.motors[2] = 0

    R.sleep(1)
 
while True:
    R.print("Looking!")
    markers = R.see()
    if len(markers) == 0:
        turn(45)
    else:
        for marker in markers:
            if marker.info.marker_type == robot.MARKER_TOKEN:
                R.print(marker.info.code)
                turn(marker.rot_y)
                R.print(marker.rot_y)
                move(marker.dist-0.1)
                break
        else:
            turn(45)
