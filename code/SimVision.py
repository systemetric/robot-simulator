import math
import random

from vector3 import *
import SimBase

def _getVisibleCuboidFaces(body, cameraPosition, height):
    """Takes a body, the position of the camera, and the height of the body, and returns a list of all faces of the cuboid that are visible to the camera.

    Faces that do not face the camera are not returned as they cannot be visible, as they are fully obstructed by the faces in that cuboid that face the camera.
    Additionally, the floor face is not checked, as it can never face the camera."""
    planes = []
    #body.shapes is actually a set, which means it cannot be indexed and I need to iterate through it with a for loop.
    #Since all my bodies only contain one shape, this for loop will always run exactly once.
    for shape in body.shapes:
        groundVertexes = []
        raisedVertexes = []
        for groundVertex in shape.get_vertices():
            x,y = groundVertex.rotated(body.angle) + body.position
            groundVertexes.append( Vector3(x, y, 0) )
            raisedVertexes.append( Vector3(x, y, height) )
        
        frontLeft = Plane(groundVertexes[0], raisedVertexes[0], groundVertexes[3])
        if frontLeft.isFacingCamera:
            planes.append(frontLeft)
        frontRight = Plane(groundVertexes[1], raisedVertexes[1], groundVertexes[0])
        if frontRight.isFacingCamera:
            planes.append(frontRight)
        backLeft = Plane(groundVertexes[2], groundVertexes[3], raisedVertexes[2])
        if backLeft.isFacingCamera:
            planes.append(backLeft)
        backRight = Plane(groundVertexes[1], groundVertexes[2], raisedVertexes[1])
        if backRight.isFacingCamera:
            planes.append(backRight)
        roof = Plane(raisedVertexes[0], raisedVertexes[1], raisedVertexes[3])
        if roof.isFacingCamera:
            planes.append(roof)

    return planes

def _getObstructingPlanesFromBody(obstructingBody, cameraPosition):
    """Takes a body that could potentially obstruct the camera (a robot or token), and the position of the camera.
    Returns the three planes that are visible to the camera (and could obstruct it's vision)."""
    obstructionHeight = None
    if isinstance(obstructingBody, SimBase.Robot):
        obstructionHeight = obstructingBody.height
    else:
        #Must be a token.
        obstructionHeight = 0.11
    
    planes = _getVisibleCuboidFaces(obstructingBody, cameraPosition, obstructionHeight)
    return planes

def _isMarkerResolvable(markerCornerSet, cameraPosition, FoV, resolution, pixelThreshold):
    """Takes a set of four corner positions, the position of the camera, the FoV of the camera, the resolution of the image,
    and the smallest number of pixels that the marker can encompass in the image while still being visible.
    
    A marker is resolvable if the angle subtended by the corners of the marker is greater than the minimum resolvable angle
    (determined by the resolution of the image, field of view of the camera, and the pixelThreshold).
    If either is too small, the marker would be either shorter or thinner than the pixelThreshold if a picture was taken."""
    #Avoid divide by 0 errors.
    if resolution[0] == 0 or FoV == 0:
        return False
    pixelsPerRadian = resolution[0] / FoV
    minimumResolvableAngle = pixelThreshold / pixelsPerRadian

    #Vectors between three corners and the position of the camera.
    vectorA = markerCornerSet[0] - cameraPosition
    vectorB = markerCornerSet[1] - cameraPosition
    vectorC = markerCornerSet[3] - cameraPosition

    return (vectorA.angleBetween(vectorB) > minimumResolvableAngle) and (vectorA.angleBetween(vectorC) > minimumResolvableAngle)

def _getMarkerCornersFromWallSegment(body):
    """Takes a wall segment, and calcuates a list of points in 3D space where the corners of the marker would lie.
    This is then returned inside another list, for compatibility with tokens (which have multiple markers)."""
    corners = []
    markerCentre = Vector3(body.position[0], body.position[1], 0.175)
    #Vector from the centre of the marker to the side.
    markerRadius = Vector3(0, 0.125, 0).rotateAroundZ(body.angle)
    corners.append( markerCentre - markerRadius - Vector3(0, 0, 0.125) )
    corners.append( markerCentre + markerRadius - Vector3(0, 0, 0.125) )
    corners.append( markerCentre + markerRadius + Vector3(0, 0, 0.125) )
    corners.append( markerCentre - markerRadius + Vector3(0, 0, 0.125) )
    #return a list of 1 markers
    return [corners]

def _getMarkerCornersFromToken(body, cameraPosition):
    """Takes a token, and returns a list containing three lists of points in 3D space where the corners of the markers visible to the camera would lie."""
    faces = _getVisibleCuboidFaces(body, cameraPosition, 0.11)
    
    markersCorners = []
    for face in faces:
        corners = []
        #accounts for the 5mm border around the markers
        uOffset = face.vectorU*(5/110)
        vOffset = face.vectorV*(5/110)
        corners.append(face.pointJ + uOffset + vOffset)
        corners.append(face.pointJ + face.vectorV + uOffset - vOffset)
        corners.append(face.pointJ + face.vectorU + face.vectorV - uOffset - vOffset) 
        corners.append(face.pointJ + face.vectorU - uOffset + vOffset)
        markersCorners.append(corners)
    
    return markersCorners

def _constructMarkerInfoDictionary(markerCornerSet, body):
    """Takes a set of corners and the body that the marker is attached to.
    Returns a dictionary that contains all the information needed by the RobotClient module to construct a Marker object."""
    corners = []
    for corner in markerCornerSet:
        corners.append(corner.convertToDictionary())
    size = 0
    if isinstance(body, SimBase.Token):
        size = 0.1
    else:
        size = 0.25
    return {
        "Corners" : corners,
        "Id" : body.id,
        "Size" : size
    }

                    
def see(robot, resolution, isImageBlurred):
    """Takes the robot attempting to look for markers, the resolution at which the image was taken, and if the image is blurred (caused by the robot moving).
    Returns a dictionary containing all the information needed by the RobotClient to construct a list of all visible Marker objects.
    Constructing the Marker objects is done by the RobotClient because it is not possible to send arbitary object structures using xmlrpc."""
    MarkersList = []
    cameraNormal = Vector3( math.cos(robot.angle), math.sin(robot.angle), 0 )
    cameraPosition = Vector3( robot.position[0], robot.position[1], robot.cameraHeight ) + ( cameraNormal * ( robot.length / 2) )
    #Only return any markers if the image is not blurred (or the robot is ignoring blur).
    if robot.isIgnoringMotionBlur or (not isImageBlurred):
        random.seed()
        #potentialObstructioningPlanes is a list of planes that could potentially get in the way
        potentialObstructingPlanes = []
        #tokens is a list of tokens, walls is a list of walls
        markedBodies = []
        for body in SimBase.space.bodies:
            if isinstance(body, SimBase.Robot):
                if body != robot:
                    potentialObstructingPlanes.extend(_getObstructingPlanesFromBody(body, cameraPosition))
            elif isinstance(body, SimBase.Token):
                potentialObstructingPlanes.extend(_getObstructingPlanesFromBody(body, cameraPosition))
                if robot.isIgnoringMotionBlur or (not body.isMoving):
                    markedBodies.append(body)
            elif isinstance(body, SimBase.WallSegment):
                markedBodies.append(body)
        for body in markedBodies:
            if isinstance(body, SimBase.Token):
                markerCornerSets = _getMarkerCornersFromToken(body, cameraPosition)
            else:
                markerCornerSets = _getMarkerCornersFromWallSegment(body)
            for markerCornerSet in markerCornerSets:
                #If the marker is too slanted or too far away for there to be enough pixels to resolve it, skip this marker.
                markerPixelMinimumAdjusted = robot.markerPixelsMinimum + random.randint( -robot.markerPixelsNoise // 2, robot.markerPixelsNoise // 2 )
                if not _isMarkerResolvable(markerCornerSet, cameraPosition, robot.fieldOfView, resolution, markerPixelMinimumAdjusted):
                    continue
                isVisible = False
                for markerCorner in markerCornerSet:
                    if cameraNormal.angleBetween(markerCorner - cameraPosition) > robot.fieldOfView:
                        break
                    for potentialObstructingPlane in potentialObstructingPlanes:
                        if potentialObstructingPlane.isObstructingPoint(markerCorner, cameraPosition):
                            break
                    else:
                        isVisible = True
                if isVisible:
                    #Set the time the body was last seen by the looking robot's id, and constructs a dictionary of information about the vector.
                    body.lastSeenList[robot.teamNumber] = SimBase.theTime
                    MarkersList.append(_constructMarkerInfoDictionary(markerCornerSet, body))
            
    #Construct the dictionary needed to build the list of Marker objects on the RobotClient.
    returnDictionary = {
        "Resolution" : resolution,
        "Field of View" : robot.fieldOfView,
        "Camera Position" : cameraPosition.convertToDictionary(),
        "Camera Normal" : cameraNormal.convertToDictionary(),
        "Timestamp" : SimBase.theTime,
        "List of Markers" : MarkersList
    }

    return returnDictionary
