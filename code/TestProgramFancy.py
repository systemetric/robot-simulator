import RobotClient

robot = RobotClient.Robot()
robot.print("hello cats are fluffy and cats like markers")

markers = robot.see()
for marker in markers:
    if marker.info.marker_type == RobotClient.MARKER_TOKEN:
        robot.print("angle " + str(marker.rot_y))
        robot.print("dist " + str(marker.dist))
        robot.print("x" + str(marker.centre.world.x))
        robot.print("y" + str(marker.centre.world.y))
        robot.print("z" + str(marker.centre.world.z))
        break

robot.sleep(300)

robot.motors[1] = 50
robot.motors[2] = 50
robot.sleep(3.5)

robot.motors[1] = 50
robot.motors[2] = 0
robot.sleep(0.6)

robot.motors[1] = 40
robot.motors[2] = 50
while robot.sleep(1):
    markers = robot.see()
    for marker in markers:
        if marker.info.marker_type == RobotClient.MARKER_TOKEN:
            robot.print(marker.rot_y)
            robot.print(marker.centre.world.x)
            robot.print(marker.centre.world.y)
            robot.print(marker.centre.world.z)
            break


print("FancyRobot has finished.")