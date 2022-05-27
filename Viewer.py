# -*- coding: utf-8 -*-
"""
Class and methods to enable the 3D viewing of players.
The software uses a combination of pyopengl and pygames


Created on Sun Nov 19 14:50:15 2017

@author: Paul Gough
"""
import sys
import math as m
import numpy as np
import pygame as pg
from pygame.locals import *
import time
from enum import Enum
from OpenGL.GL import *
from OpenGL.GLU import *
import StreamData as sd
#from OpenGL.GLUT import *

import Player as pl
from StreamData import Sensors, ConStatus

class ViewStates(Enum):
    IDLE             = 1
    PLAYER_IDLE      = 2
    STREAMING        = 3
    PLAYBACK         = 4
    RECORD           = 5
    CALIBRATE        = 6

# Global variables used to handle key presses
gl_logfile   = None
gl_vstate    = ViewStates.IDLE
gl_stime     = 0
gl_caldict   = {}
gl_calibrate = False


class PlayerViewer ():

    def __init__ (self, players, display ):
        pg.init()
        pg.display.set_caption('Player analyzer')
        self.players     = players
        self.display     = display
        self.solid_floor = True
        self.grid_floor  = True
        self.quadric     = gluNewQuadric()
        self.lbut        = False
        pg.display.set_mode (display, DOUBLEBUF | OPENGL )
        gluPerspective ( 70, (display[0]/display[1]), 0.1, 1000.0 )
        glTranslate(0.0, -120.0, -200.0)
        glRotatef ( 0, 0, 0, 0 )
        # TEst code
        glEnable(GL_DEPTH_TEST)


    #
    # Draws a player using lines and solid spheres at joints
    #
    def DrawPlayer(self, index):
        player = self.players[index].body
        self.DrawSphere (player.root[0].offset + player.tran)


        glBegin(GL_LINES)
        root = player.tran

        for item in player.root:
            glVertex3fv(root)
            next_point = item.offset + root
            glVertex3fv(next_point)
            self.DrawRod (item.next, next_point)
        glEnd()
     #
     # Draws a player using solid objects

    def DrawPlayerSolid (self, index):
        player = self.players[index].body

        self.DrawRodSolid (player.root, player.tran)

    def DrawRod (self, rod, prev_point):
        if rod == []:
            return

        for item in rod:
            glVertex3fv(prev_point)
            next_point = item.offset + prev_point
            glVertex3fv(next_point)
            self.DrawRod ( item.next, next_point)

    def DrawRodSolid (self, rod, prev_point):
        if rod == []:
            return

        # Test code
        #glEnable(GL_LIGHTING)
        #glShadeModel(GL_FLAT)
        #glEnable(GL_COLOR_MATERIAL)
        #glEnable(GL_BLEND)
        #glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        #glEnable(GL_LIGHT0)
        #glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.8, 0.8, 1])
        #glColor3fv ((1.,1.0,1.0))
        #glColor3fv ((0.5,0.5,0.5))
        for item in rod:
            self.DrawSphere ( prev_point)
            next_point = item.offset + prev_point

            glPushMatrix()
            glTranslatef(prev_point[0], prev_point[1], prev_point[2])
            gluQuadricNormals(self.quadric, GLU_FLAT)
            glColor3ub(200, 200, 200)
            mag = np.sqrt(item.offset.dot(item.offset))
            ivec = np.array([0,0,mag])
            rot_axis = (ivec + item.offset)/2
            glRotatef(180, rot_axis[0], rot_axis[1], rot_axis[2])

            gluQuadricDrawStyle(self.quadric, GLU_FILL)
            gluCylinder (self.quadric, 2, 2, mag, 6, 6)
            gluQuadricDrawStyle(self.quadric, GLU_LINE)
            glColor3ub(2, 2, 2)
            gluCylinder (self.quadric, 2, 2, mag, 6, 6)
            glDisable(GL_LIGHT0)
            glPopMatrix()
            self.DrawRodSolid ( item.next, next_point)
        glDisable(GL_LIGHT0)

    def DrawGround (self):
        max_g =  500
        min_g = -500
        diff   = 10
        del_g = max_g - min_g

        # Create filled floor if require
        if self.solid_floor:
            ground_vert = ((min_g,0,max_g),
                           (min_g,0,min_g),
                           (max_g,0,min_g),
                           (max_g,0,max_g))
            glBegin(GL_QUADS)
            for vertex in ground_vert:
                glColor3fv ((0.4,0.6,0.3))
                glVertex3fv (vertex)
            glEnd()

        if self.grid_floor:
            glBegin(GL_LINES)
            glColor3fv ((0.1,0.1,0.1))
            for i in range ( min_g, max_g, int(del_g/diff)):
                glVertex3fv ( (i, 0, max_g) )
                glVertex3fv ( (i, 0, min_g) )
                glVertex3fv ( (max_g, 0, i) )
                glVertex3fv ( (min_g, 0, i) )

            glEnd()

    def DrawSphere (self, pos):
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        glColor3ub(250, 48, 250)
        gluSphere (self.quadric, 3, 30, 30)
#            gluCylinder(cylinder, 1, 1, 50, 10, 10)
        glPopMatrix()

    # Function to process viewer events including key presses
    def ProcessEvent (self, event, sensors):
        global gl_logfile
        global gl_vstate
        global gl_stime

        if event.type == pg.QUIT:
            pg.quit()
            exit()

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                glTranslate(-1,0,0)
            elif event.key == pg.K_RIGHT:
                glTranslate(1,0,0)
            elif event.key == pg.K_UP:
                glTranslate(0,1,0)
            elif event.key == pg.K_DOWN:
                glTranslate(0,-1,0)
            elif event.key == pg.K_l:    # Log data
                if gl_logfile:
                    gl_logfile.close()
                    gl_logfile = None
                else:
                    gl_logfile = open('log.txt', 'w')
            elif event.key == pg.K_c:   # Calibrate
                gl_vstate = ViewStates.CALIBRATE
                gl_stime = time.time()

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.lbut = True
                self.m_pos = pg.mouse.get_pos()
            if event.button== 4:
                glTranslate(0,0,4)
            if event.button== 5:
                glTranslate(0,0,-4)

        if event.type == pg.MOUSEMOTION:
            if self.lbut == True:
                new_pos = pg.mouse.get_pos()
                dx = new_pos[0] - self.m_pos[0]
                dy = new_pos[1] - self.m_pos[1]
                glRotatef(dx*0.2, 0, 1, 0)
                glRotatef(dy*0.2, 1, 0, 0)
                self.m_pos = new_pos

        if event.type == pg.MOUSEBUTTONUP:
            self.lbut = False

def GenerateEulerAngles (input_data):
    rtn_list = []
    for ele in input_data:
        if ele.name == 'SA_BNO_QEU':
            name = 'SA_EUL_ANG'
            time = ele.time
            data = {'sensor':ele.data['sensor'], "angle_X":ele.data["angle_x"],
                    "angle_Y":ele.data["angle_y"], "angle_Z":ele.data["angle_z"]}
            new_ele = sd.Element (name, time, data)
            rtn_list.append (new_ele)
    return rtn_list

#
# Does as suggest, output in degrees
                #
def quaternion_to_euler_angle(w, x, y, z):
    ysqr = y * y

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = m.degrees(m.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = m.degrees(m.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = m.degrees(m.atan2(t3, t4))

    return X, Y, Z
#
# Second function added to check original
#
def quaternion_to_euler_angle_2(qw, qx, qy, qz):
    qnorm = 1 / m.sqrt(qw*qw + qx*qx + qy*qy + qz*qz)  # normalize the quaternion
    qw *= qnorm
    qx *= qnorm
    qy *= qnorm
    qz *= qnorm
    roll = m.degrees(m.atan2(qw*qx + qy*qz, 0.5 - qx*qx - qy*qy))
    pitch = m.degrees (m.asin(2 * (qw*qy - qx*qz)))
    heading = m.degrees ( m.atan2(qw*qz + qx*qy, 0.5 - qy*qy - qz*qz))
    return (roll, pitch, heading)

            
if __name__ == '__main__':
    TCP_IP = '192.168.1.94'
    TCP_PORT = 80
    BUFFER_SIZE = 1024

    # Create player
    marvin = pl.Player ( "Marvn", "standard", 1.6 )
    # Set up connection to jacket
 #   jacket = Sensors()
 #   marvin.calib = {2:["RightLowerarm", np.array([0,0,0])], 3:["RightUpperarm", np.array([90,0,0])],5:["Spine", np.array([0,0,0])]}
    
 #   jacket.AddConTCP ("Jacket_BNO", TCP_IP, TCP_PORT, BUFFER_SIZE )
 #   while (jacket.sensoritems["Jacket_BNO"].status != ConStatus.CONNECTED):
 #       jacket.Connect()
 #       print ("Connecting")
 #       time.sleep(0.5)
 #   marvin.sensors = jacket
    gl_vstate = ViewStates.STREAMING
  #  print ("Connected")

    viewer  = PlayerViewer ([marvin], (1000,800))
    abs_updates = {"RightLowerarm": np.array([0, 0, 0]), "LeftLowerarm": np.array([0, 0, 0]), "RightUpperarm": np.array([0, 0, 0]), "LeftUpperarm": np.array([0, 0, 0]) }
    rel_updates = {"RightLowerarm": np.array([0, 0, 0]), "LeftLowerarm": np.array([0, 0, 0]), "RightUpperarm": np.array([0, 0, 0]), "LeftUpperarm": np.array([0, 0, 0]) }
    #----- main loop  ---------
 #   while True:
 #       new_data = jacket.ReadData()
 #       angles = GenerateEulerAngles (new_data)
 #       print (angles)
        
 #       if gl_logfile:
 #          gl_logfile.write (new_data)
 #          gl_logfile.write (angles)        
           
 #       for event in pg.event.get():
 #           viewer.ProcessEvent (event, None)
 #           
 #       if gl_vstate == ViewStates.CALIBRATE:
 #           marvin.calib = CalibateJacket (angles, marvin.calib)
 #           print (marvin.calib)

  #      if gl_calibrate & (gl_vstate == ViewStates.STREAMING) :
  #          if angles:
  #              rel_updates, abs_updates =  CalcLimbPos(angles, marvin.calib, rel_updates, abs_updates)
  #          print (rel_updates)
            
 #       glRotatef(0.1, 0, 1, 0)
    glClearColor( 0.1,0.8,1.0 ,0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    viewer.DrawGround()
        
    viewer.DrawPlayer (0)
    viewer.DrawPlayerSolid (0)

   #     marvin.body.Update (rel_updates)   
    pg.display.flip()
      #  pg.time.wait(1)
    