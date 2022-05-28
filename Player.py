# -*- coding: utf-8 -*-
"""
Class and methods for describing a body as connection of rigid rods joined
together at joints


Originally Created on Fri Nov 17 08:21:01 2017

@author: Paul Gough
"""
import numpy as np
import math as m

class Player ():
    def __init__ (self, name, model, height ):
        self.name = name
        self.model = model
        self.height = height   # Height in metres
        self.config = {}

        self.model_list = {"standard", "extended"}
        if model in self.model_list:
            self.body = Body (model, self.height)
        else:
            ErrorMsg (0, "Unknown model type, using standard")
            self.body = Body ("standard", self.height)

    def ConnectDataStream ( self, datastream ):
        self.sensors = datastream

    def String (self):
        out = "SA_Player," + self.name + "," + self.model + "," + str(self.height)
        return out

# =============================================================================
# class Activity ():
#     def __init__ (self, label, start_time ):
#         self.label = label
#         self.start_time = start_time # in datetie format
#         self.duration = 0            # duration in seconds to 3 decimal places
#         self.stream = []
# =============================================================================

class Body ():
    def __init__ (self, model, height):
        self.root      = []
        self.root_name = "Root"
        self.tran      = np.array ([0.0, 57.0*height, 0.0]) # Transformed value after transalation
        self.origin    = np.array ([0.0, 57.0*height, 0.0]) # Store origin value
        self.rotate    = np.array ([0.0, 0.0, 0.0])  # Rotation angles - absolute not relative
        self.calibrate = np.array ([0.0, 0.0, 0.0])  # Calibaration angles - absolute not relative
        self.rotm      = np.identity (3)             # Rotation matrix intially set to id matrix

        # Standard body parts
        # A bit of a messy structure (should have been a dictionary)
        # The components are:
        # Label
        # Vector representing rod (offset)
        # Rotation from world to sensor in ideal position
        # Combined rotation matrix
        # Not used
        # Boolean of true use absolute update of rod orientation, if false use relative update
        #
        # Does the rod have a sensor
        #
    #    spine       = Rod ("Spine", np.array ([0.0, 24.8, 0.0])*height, np.array ([0.0, -90.0,  180.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), True )
        spine       = Rod ("Spine", np.array ([0.0, 24.8, 0.0])*height, np.array ([0.0, 0.0,  0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]),False )
        r_shoulder  = Rod ("RightShoulder",np.array ([-11.0, 0.0, 0.0])*height, np.array ([0.0, 90.0, 90.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False )
        r_upperarm  = Rod ("RightUpperarm",np.array ([-18.8, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False )
        r_lowerarm  = Rod ("RightLowerarm",np.array ([-14.5, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False)
        r_hand      = Rod ("RightHand",np.array ([-10.8, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False )
        l_shoulder  = Rod ("LeftShoulder",np.array ([11.0, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_upperarm  = Rod ("LeftUpperarm",np.array ([18.8, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_lowerarm  = Rod ("LeftLowerarm",np.array ([14.5, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_hand      = Rod ("LeftHand",np.array ([10.8, 0.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        r_hip       = Rod ("RightHip",np.array ([-5.2, -4.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        r_knee      = Rod ("RightKnee",np.array ([0.0, -24.5, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        r_ankle     = Rod ("RightAnkle",np.array ([0.0, -26.5, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        r_foot      = Rod ("RightFoot",np.array ([0.0, -2.0, 10.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_hip       = Rod ("LeftHip",np.array ([ 5.2, -4.0, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_knee      = Rod ("LeftKnee",np.array ([0.0, -24.5, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_ankle     = Rod ("LeftAnkle",np.array ([0.0, -26.5, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        l_foot      = Rod ("LeftFoot",np.array ([0.0, -2.0, 10.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )
        head        = Rod ("Head",np.array ([0.0, 18.2, 0.0])*height, np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), np.array ([0.0, 0.0, 0.0]), False  )

        # Contruct Standard body
        self.root.append ( spine )
        spine.AddNext (r_shoulder)
        r_shoulder.AddNext (r_upperarm)
        r_upperarm.AddNext (r_lowerarm)
        r_lowerarm.AddNext (r_hand)
        spine.AddNext (l_shoulder)
        l_shoulder.AddNext (l_upperarm)
        l_upperarm.AddNext (l_lowerarm)
        l_lowerarm.AddNext (l_hand)
        self.root.append (r_hip)
        r_hip.AddNext (r_knee)
        r_knee.AddNext (r_ankle)
        r_ankle.AddNext(r_foot)
        self.root.append (l_hip)
        l_hip.AddNext (l_knee)
        l_knee.AddNext (l_ankle)
        l_ankle.AddNext(l_foot)
        spine.AddNext (head)
    
    # Take a list of absolute updates and calibration parameters
    def Update (self, updates):
        
        if "Root" in updates:
            tran = np.array (updates["Root"][0:3])
            self.rotate = np.array (updates["Root"][3:6])
            self.tran   = self.origin + tran
        
        rot_abs = RotationMat ( self.rotate )
        rot_cal = RotationMat ( self.calibrate )
        rotm =   rot_cal.T * rot_abs  # Matrix multiply to get combined rotation
        for limb in self.root:
            limb.UpdateRod ( updates, rotm)
            
    # Function that updates body with new calibreation data contained in updates dict
    def UpdateCalibrate (self, updates):
        for limb in self.root:
            limb.UpdateRodCalibrate (updates)

    # function that returns the x,y,z coord of the end of each limb using a dict
    def OutputPos (self):
        pos_dict =dict()
        for item in self.root:
            for n, pos in item.OutputPos(self.tran):
                pos_dict[n] = pos
        return pos_dict
    
    def GetRod (self, name):
        """ Simple routine to return Rod that is called name"""
        for item in self.root:
            rod = item.GetRod (name)
            if rod:
                return rod
        return (None)       

    #
    # Method to outout a body in a BVH format
    # Probably does not work now as rotation order don't match
    def OutputBVH (self, fn):
        try:
            f = open ( fn, 'w' )
        except:
            ErrorMsg (3, "Unable to open file: " + fn)
            
        f.write ("HIERARCHY\n")
        f.write ("ROOT " + self.root_name +"\n{\n")
        f.write ("\tOFFSET {} {} {}\n".format(self.tran[0], self.tran[1], self.tran[2]) )
        f.write ("\tCHANNELS 6 Xposition Yposition Zposition Zrotation Yrotation Xrotation\n")
        
        for item in self.root:
            item.WriteBVH (f, 1)
        f.write ("}\n")
            
        # Dummay statements for Motion and Frame
        f.write ( "MOTION\nFrames: 1\nFrame Time: 0.01\n")
        f.write ( 45*"0.00 ")
        f.close()
        
        
            
class Rod ():
    def __init__ (self, name, offset, orient, rotate, s_orient, abs_update):
        self.name       = name
        self.offset     = offset  # Transformed value
        self.orig       = offset  # Original value
        self.orient     = orient  # Rotation to orient body to sensor
        self.rotate     = rotate  # Combined rotation matrix 
        self.s_orient   = s_orient  # Not used yet
        self.calibrate  = np.array ([0.0,0.0,0.0])  # Calibration rotation
        self.abs_update = abs_update # Set true if node is updated using absolute values and false if relative
        self.next   = []
        
    def AddNext (self, next):
        self.next.append ( next)
        
    def GetRod (self, name):
        """ Retreive a rod by name, not tested """
        if self.name == name:
            return (self)
        else:
            for item in self.next:
                if item.GetRod(name):
                    return (item.GetRod(name))
            return (None)
        
    def OutputPos (self, offset):
        """ Method to extract the position of a limb in world coordinates 
        Uses recursion to traverse the full list
        """
        pos = self.offset + offset
        yield self.name, pos
        if len(self.next) != 0:
            for item in self.next:
                yield from item.OutputPos(pos)
  
    def UpdateRod (self, updates, rot_prev):
        if self.name in updates:
            self.rotate = updates[self.name]
            rot_rel = RotationMat ( self.rotate )
            rotm = rot_rel * rot_prev
        else:
            rotm = rot_prev            
     
#         if (self.abs_update):
#             rot_abs = RotationMat ( self.rotate )
#             rot_cal = RotationMat ( self.calibrate )
#             rot_ori = RotationMat ( self.orient )
# #            rot_ori = RotationMat (np.array([0.,0.,90.]))
            
#             if self.name == 'Spine':
# #                cor = np.array([0., self.calibrate[1], self.calibrate[2]-90.])
#                 cor = np.array([0., self.calibrate[1], self.calibrate[2]-90.])                
# #                cor = np.array([0., 0., 0.])
#             else:
#                 cor     = np.array([0.,self.calibrate[1], self.calibrate[2]])
#             rot_cor = RotationMat ( cor )
            
#             # Compose the rotation
#             rot_net = rot_cal.T * rot_abs
#             rotm = rot_ori * rot_cor * rot_net  * rot_cor.T * rot_ori.T

#         else:
#             rotm = rot_prev
        
        t_orig = self.orig.reshape(3,1)
        new_pos = rotm * t_orig
        self.offset = np.squeeze (np.array(new_pos))

        if self.next != []:
            for item in self.next:
                item.UpdateRod (updates, rotm)
                
    # Update the calibration data, go through list recursively   
    def UpdateRodCalibrate (self, updates):

        if self.name in updates:
            self.calibrate = updates[self.name]
            
        if self.next != []:
            for item in self.next:
                item.UpdateRodCalibrate (updates)
        

#
#   Function to return a rotation matrix for the input angles
#
def RotationMat ( rotate_angles ):
    r_x = m.radians( rotate_angles[0] )
    r_y = m.radians( rotate_angles[1] )
    r_z = m.radians( rotate_angles[2] )

    # Rotations for Left Hand coordinates
   # rot_z = np.matrix ([[m.cos(r_z), m.sin(r_z), 0.], [-m.sin(r_z), m.cos(r_z), 0.], [0., 0., 1.]])
   # rot_y = np.matrix ([[m.cos(r_y), 0., -m.sin(r_y)], [0., 1., 0.], [m.sin(r_y), 0., m.cos(r_y)]])
   # rot_x = np.matrix ([[1., 0., 0.], [0., m.cos(r_x), m.sin(r_x)], [0, -m.sin(r_x), m.cos(r_x)]])
    
   # Right Hand Rule
    rot_z = np.matrix ([[m.cos(r_z), -m.sin(r_z), 0.], [m.sin(r_z), m.cos(r_z), 0.], [0., 0., 1.]])
    rot_y = np.matrix ([[m.cos(r_y), 0., m.sin(r_y)], [0., 1., 0.], [-m.sin(r_y), 0., m.cos(r_y)]])
    rot_x = np.matrix ([[1., 0., 0.], [0., m.cos(r_x), -m.sin(r_x)], [0, m.sin(r_x), m.cos(r_x)]])
        
    return (rot_x * rot_y * rot_z)

#
# Simple fnction to take latest data from sensors and update the angle list used
# to give the body position. Only uses SA_EUL_ANG, ignores other messages                              
def UpdateLimbPos ( angles, abs_updates, sensorlist ):
    for ang in angles:
        if ang.name == "SA_EUL_ANG":
            sensor = ang.data['sensor']
            new_ang = np.array([ang.data['angle_X'], ang.data['angle_Y'], ang.data['angle_Z']])
            limb = sensorlist[sensor]
            abs_updates[limb] = new_ang
    return ( abs_updates )


def isRotationMatrix(R) :
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype = R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6
 
 
# Calculates rotation matrix to euler angles
# The result is the same as MATLAB except the order
# of the euler angles ( x and z are swapped ).
def rotationMatrixToEulerAngles(R) :
 
    assert(isRotationMatrix(R))
     
    sy = m.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
     
    singular = sy < 1e-6
 
    if  not singular :
        x = m.atan2(R[2,1] , R[2,2])
        y = m.atan2(-R[2,0], sy)
        z = m.atan2(R[1,0], R[0,0])
    else :
        x = m.atan2(-R[1,2], R[1,1])
        y = m.atan2(-R[2,0], sy)
        z = 0
 
    return np.array([x, y, z])

def ErrorMsg ( level, msg):
    print ("Warning ", msg)
    
if __name__ == '__main__':
#    print ("Define Marvin")
#
    marvin = Player ( "Marvn", "standard", 1.68 )
    print ("Marvin created")
    print(marvin.body.OutputPos())
    sp = marvin.body.GetRod ("Spine")
    la = marvin.body.GetRod ("LeftAnkle")
    lk = marvin.body.GetRod ("LeftKnee")
    lh = marvin.body.GetRod ("LeftHip")
    he = marvin.body.GetRod ("Head")
    lf = marvin.body.GetRod ("LeftFoot")
    print (abs(sp.orig[1]) + abs(la.orig[1]) + abs(lk.orig[1]) + abs(lh.orig[1]) + abs(he.orig[1]) + abs(lf.orig[1]))
    
 

    