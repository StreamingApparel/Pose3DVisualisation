# -*- coding: utf-8 -*-
"""
Simple routine to create motion data for testing visualisation
software

Created on Sun May 15 10:33:31 2022

@author: Paul Gough
"""
from datetime import datetime
from math import sin, pi
import os

class Motion ():
    def __init__ (self, folder, t_step=0.02, height=1.6):
        self.path   = folder
        self.t_step = t_step
        self.height = height
        self.limb_table = "SA_SensorDict,3,RightLowerarm,2,RightUpperarm,4,LeftLowerarm,"\
        "5,Spine,6,LeftUpperarm, 7,RightHip,8,RightKnee,9,RightAnkle,10,RightFoot,"\
        "11,LeftHip,12,LeftKnee,13,LeftAnkle,14,LeftFoot,15,RightHand,16,LeftHand\n"

    def Bow (self, file_name, period = 10.):
        # Open the file
        try:
            fp = open (self.path + file_name, 'a+')
        except:
            print ("Error opening the file ", self.path + file_name)
            return False

        self.Header(fp, lbl='Bow_2X')
        
        # Make sure arms are down
        fp.write ("SA_EUL_ANG,0.0,sensor,2,angle_Z,90.0 ,angle_X,0.0,angle_Y,0.0\n")       
        fp.write ("SA_EUL_ANG,0.0,sensor,6,angle_Z,-90.0 ,angle_X,0.0,angle_Y,0.0\n")

        steps = int(period/self.t_step)
        for _ in range (0, 2):
            for i in range (0, steps+1):
                frac = i/steps
                tim = frac * period
                spine     =  90 * sin (frac*pi)
                fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,5,angle_Z,0.0 ,angle_X,{spine:.2f},angle_Y,0.0\n")  
        fp.close()
        return True
    
    def BicepCurl (self, file_name, period = 10.):
        # Open the file
        try:
            fp = open (self.path + file_name, 'a+')
        except:
            print ("Error opening the file")
            return False

        self.Header(fp, lbl='Bicep_Curl')

        # Make sure arms are down
        fp.write ("SA_EUL_ANG,0.0,sensor,2,angle_Z,90.0 ,angle_X,0.0,angle_Y,0.0\n")       
        fp.write ("SA_EUL_ANG,0.0,sensor,6,angle_Z,-90.0 ,angle_X,0.0,angle_Y,0.0\n")

        steps = int(period/self.t_step)
        for _ in range (0, 2):
            for i in range (0, steps+1):
                frac = i/steps
                tim = frac * period
                r_elbow     =  -90 * sin (frac*pi)
                l_elbow     = r_elbow
                r_hand      = r_elbow
                l_hand      = l_elbow
                fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,3,angle_Z,0.0 ,angle_X,{r_elbow:.2f},angle_Y,0.0\n")       
                fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,4,angle_Z,0.0 ,angle_X,{l_elbow:.2f},angle_Y,0.0\n")
                fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,15,angle_Z,0.0 ,angle_X,{r_hand:.2f},angle_Y,0.0\n")       
                fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,16,angle_Z,0.0 ,angle_X,{l_hand:.2f},angle_Y,0.0\n")
        fp.close()
        return True

    def FoldArms (self, file_name, period = 10.):
        # Open the file
        try:
            fp = open (self.path + file_name, 'a+')
        except:
            print ("Error opening the file ", )
            return False

        self.Header(fp, lbl='Fold_Arms')

        steps = int(period/self.t_step)
        for i in range (0, steps+1):
            frac = i/steps
            tim = frac * period
            r_shoulder  = 90 * sin (frac*pi)
            l_shoulder  = -r_shoulder
            r_elbow     =  r_shoulder
            l_elbow     = -r_shoulder
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,2,angle_Z,0.0 ,angle_Y,{r_shoulder:.2f},angle_X,0.0\n")       
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,6,angle_Z,0.0 ,angle_Y,{l_shoulder:.2f},angle_X,0.0\n")
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,3,angle_Z,0.0 ,angle_Y,{r_elbow:.2f},angle_X,0.0\n")       
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,4,angle_Z,0.0 ,angle_Y,{l_elbow:.2f},angle_X,0.0\n")

        fp.close()
        return True
        
    def Squat (self, file_name, period = 10.):

        # Open the file
        try:
            fp = open (self.path + file_name, 'a+')
        except:
            print ("Error opening the file")
            return False

        self.Header(fp)
        
        steps = int(period/self.t_step)
        for i in range (0, steps+1):
            frac = i/steps
            tim = frac * period
            r_knee  = -90 * sin (frac*pi)
            l_knee  = r_knee
            r_ankle = -r_knee
            l_ankle = -l_knee
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,8,angle_Z,0.0 ,angle_X,{r_knee:.2f},angle_Y,0.0\n")       
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,12,angle_Z,0.0 ,angle_X,{l_knee:.2f},angle_Y,0.0\n")
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,9,angle_Z,0.0 ,angle_X,{r_ankle:.2f},angle_Y,0.0\n")       
            fp.write (f"SA_EUL_ANG,{tim:.3f},sensor,13,angle_Z,0.0 ,angle_X,{l_ankle:.2f},angle_Y,0.0\n")    
            
        fp.close()
        return True
        
        # Print Header
        
    def Header (self, fp, lbl='Squat', name='Marvin' ):
        now        = datetime.now()
        now_string = now.strftime("%d/%m/%Y %H:%M:%S")

        track_lbl   = f"SA_Track,{lbl}\n"
        player      = f"SA_Player,{name},standard,{self.height}\n"
        start_time  = f"SA_Time,{now_string}\n"
        
        fp.write (track_lbl)
        fp.write (player)   
        fp.write (self.limb_table)
        fp.write (start_time)

if __name__ == '__main__':
    print ("Start")
    
   # path = "X:\\Dropbox\\Projects\\FootfallAndHeartbeats\\"
    path = "C:\\Users\\pgou\\Dropbox\\Projects\\FootfallAndHeartbeats\\"
    fn   = "testset.sat"
    
    if os.path.exists(path+fn):
        os.remove (path + fn)
    move = Motion(path)
    move.Squat (fn)
    move.FoldArms (fn, period = 5.)
    move.BicepCurl (fn, period = 4.)
    move.Bow (fn, period = 5.)
    print ("Finish")
    