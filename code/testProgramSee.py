import RobotClient
import random

print("LazyRobot started!")
robot = RobotClient.Robot()

while True:
    seen = robot.see( (1920,1440) )
    for marker in seen:
        print("Marker " + str(marker.info.code) + ":")
        for i in range(0,4):
            print("  Vertex[{}]: image=({},{})".format(i, marker.vertices[i].image.x, marker.vertices[i].image.y))
            print("  Vertex[{}]: polar=({},{})".format(i, marker.vertices[i].polar.rot_x, marker.vertices[i].polar.rot_y))
            print("  Vertex[{}]: world=({},{},{})".format(i, marker.vertices[i].world.x, marker.vertices[i].world.y, marker.vertices[i].world.z))
        print("  dist={}".format(marker.dist))
        print("  rot_y={}".format(marker.rot_y))
        print("  Orientation=({},{},{})".format(marker.orientation.rot_x, marker.orientation.rot_y, marker.orientation.rot_z))
    robot.sleep(200)
