import pygame
from pygame.locals import *

import SimBase

class Display:
    """A class that provides a display of the simulation and encapsulates the dependancies on the pygame module."""

    _teamColourDictionary = {
        0 : Color("Gold"),
        1 : Color("Lime Green"),
        2 : Color("Red"),
        3 : Color("Blue")
    }
    _darkTeamColourDictionary = {
        0 : Color(100, 80, 0),
        1 : Color(0, 100, 0),
        2 : Color(100, 0, 0),
        3 : Color(0, 0, 100)
    }
    _tokenTypeColourDictionary = {
        "Ore" : Color("Grey"),
        "Team 0 Gold" : Color("Gold"),
        "Team 1 Gold" : Color("Lime Green"),
        "Team 2 Gold" : Color("Red"),
        "Team 3 Gold" : Color("Blue")
    }

    def __init__(self):
        """Creates the window for the display, and populates it with the objects currently in the arena."""
        pygame.init()
        pygame.display.set_caption("Test program.")
        self.screen = pygame.display.set_mode( (620, 620), pygame.RESIZABLE )
        #The screen is set to slightly larger than 6m by 6m, to allow the arena walls to be displayed.
        self.clock = pygame.time.Clock()
        self.updateDisplay()
    
    def _pymunkToPygame(self, point):
        """Converts pymunk coordinates to pygame coordinates."""
        width, height = self.screen.get_size()
        return int((point.x + 3.1) * width / 6.2), int((3.1 - point.y) * height / 6.2)

    def _drawPoly(self, shape, colour, borderColour = None):
        """Takes a pymunk Poly shape and draws the polygon in the specified colour, with a border if the borderColour argument is set."""
        vertexes = shape.get_vertices()
        pygameVertexes = []
        for vertex in vertexes:
            worldVertex = shape.body.local_to_world(vertex)
            pygameVertexes.append(self._pymunkToPygame(worldVertex))

        pygame.draw.polygon(self.screen, colour , pygameVertexes)
        if borderColour != None:
            pygame.draw.polygon(self.screen, borderColour , pygameVertexes, 3)

    def processInputs(self):
        """Checks to see if the window has been closed or the Escape key has been pressed,
        and if it has, ends the simulation by setting the duration to the current time.
        Also rescales the display if the window size is changed."""
        for event in pygame.event.get():
            if event.type == QUIT:
                SimBase.endTime = SimBase.theTime
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                SimBase.endTime = SimBase.theTime
            elif event.type == VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    def updateDisplay(self):
        """Updates the display to the current state of SimBase.space, and then waits
        a variable amount of time to keep the framerate consistent at 64 fps"""
        self.screen.lock()
        self.screen.fill((255,255,255))
        #Drawing is done in two passes to ensure the zones are drawn underneath the tokens or walls.
        for shape in SimBase.space.shapes:
            if isinstance(shape.body, SimBase.Zone):
                colour = Display._darkTeamColourDictionary[shape.body.teamNumber]
                self._drawPoly(shape, colour)
        
        for shape in SimBase.space.shapes:
            if isinstance(shape.body, SimBase.Token):
                mostRecentSeen = -5
                bestBorderColor = None
                for team in range(4):
                    if (SimBase.theTime - shape.body.lastSeenList[team] < 1) and (shape.body.lastSeenList[team] > mostRecentSeen):
                        bestBorderColor = Display._darkTeamColourDictionary[team]
                        mostRecentSeen = shape.body.lastSeenList[team]

                self._drawPoly(shape, self._tokenTypeColourDictionary[shape.body.type], bestBorderColor)
            elif isinstance(shape.body, SimBase.WallSegment):
                bestColour = Color("Black")
                mostRecentSeen = -5
                for team in range(4):
                    if (SimBase.theTime - shape.body.lastSeenList[team] < 1) and (shape.body.lastSeenList[team] > mostRecentSeen):
                        bestColour = Display._teamColourDictionary[team]
                        mostRecentSeen = shape.body.lastSeenList[team]

                self._drawPoly(shape, bestColour)
            
            elif isinstance(shape.body, SimBase.Robot):
                self._drawPoly(shape, Display._teamColourDictionary[shape.body.teamNumber])
                
        self.screen.unlock()
        pygame.display.flip()
        self.clock.tick(64)
