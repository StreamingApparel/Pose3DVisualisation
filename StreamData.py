# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 22:27:30 2017

Classes for handling streaming data, including receiving data over UDP stream. 
Class are:
    Element  - basic element in a time series contains data at a particular time
    Track    - Contains time series, together with the player and other associated 
               information
    RecPlay  - Class to manage the record and playback of tracks
    PlotData - Class to generate and manage a list of items to be plotted
    DataView - Class to generate and manage a lost of items to show realtime data in a table

25/10/18 Change from TCP to UDP

@author: Paul Gough
"""

import socket
from enum import Enum
import datetime as dt
import time
import Player as pl
import numpy as np

class PlayState(Enum):
    PLAY         = 1
    PAUSE        = 2
    RECORD       = 3
    STOP         = 4
    LIVE         = 5

# Element is the basic element in our time series which consists of a list
# of Elements. The dictionary can hold different types of data
class Element ():
    def __init__ (self, name, time, data_dict):
        self.name      = name
        self.time      = time       # Time in seconds
        self.data_time = None       # Time in date_time form, not always filled in
        self.data      = data_dict
            
    def Print (self):
        print (self.name, self.time, self.data)
        
    def String (self):
        return  (self.name + "," + str(self.time) + "," + dict_string (self.data))
    
    def Read (self, str_items):
        """ Read and store element data using array of string items containing 
        information"""   
        length = len(str_items)
        self.name = str_items [0]
        self.time = float (str_items[1])
        self.data = {}
        for i in range (2, length, 2):
            if (self.IsFloat(str_items[i])):
                self.data[str_items[i]] = float (str_items[i+1])
            elif (self.IsInt(str_items[i])):
                self.data[str_items[i]] = int (str_items[i+1])
            else:
                print (str_items[i])
                self.data[str_items[i]] = str_items[i+1]                
        
    def IsFloat (self, name):
        fl_names = ["angle_X", "angle_Y", "angle_Z", "acc_X", "acc_Y", "acc_Z"]
        return (name in fl_names)
        
    def IsInt (self, name):
        int_names = ["sensor"]
        return (name in int_names)
        
class Track ():
    """ A track is simply a time ordered sequence of elements
    Read routine in RecPlay at the moment
    """
    def __init__ (self, name):
        self.name        = name
        self.t_len       = 0.0    # How long is the track in seconds
        self.start_time  = 0.0    # Date time at start of recording 
        self.sequence    = []     # Track data sotred here as list of dict at each time point
        self.calibrate   = None   # Used to capture calibration data relevant to sequence
        self.player      = None
        self.sensor_dict = {}
        self.annotate    = []     # Names for components of a track e.g. bowling not useed yet
        
    def SetTimeLen (self):
        """ Determine how long (in sceonds) is the track time and reset sequence time
        so it starts at 0.0s """
        start_time_s = self.sequence[0].time
        end_time_s   = self.sequence[-1].time
        
        self.t_len = end_time_s - start_time_s
        if self.t_len < 0.0 :
            print ("Error, negative time for track length" )
            
        # Reset sequence time so it starts at 0.0
        for item in self.sequence:
            item.time -= start_time_s
               
    def SetCalibrate (self, calibrate):
        self.calibrate = calibrate.copy()   # Calibrate dictionary
       
    def SetPlayer (self, player):
        self.player = player
        
    def SetSensorDict (self, sensor_dict):
        self.sensor_dict = sensor_dict.copy()
        
    def Write (self, fp):
        """ Write out track information to file pointer"""
        #Track name
        fp.write ("SA_Track," + self.name + '\n')
        # Plyaer data
        fp.write ( self.player.String() + '\n')
        # sensor dictionary
        fp.write ("SA_SensorDict," + dict_string(self.sensor_dict)  + '\n')
        # Calibration Data
        fp.write ("SA_Calibrate," + dict_string(self.calibrate)  + '\n')
        # Time
        fp.write ("SA_Time," + str(self.start_time)  + '\n')
        # Sequence
        for ele in self.sequence:
            s = ele.String()
            if "SA_BNO_QEU" not in s:
                fp.write ( s  + '\n' )
    def DataList (self, limb, qty):
        """ Generate a time series for the limb and quantity requested e.g.
        trk.DataList ("rightupperarm", "amgle_X" """
        time = []
        y    = []
        for ele in self.sequence:
            if self.sensor_dict[ele.data["sensor"]] == limb:
                if qty in ele.data:
                    time.append (float(ele.time))
                    y.append (float(ele.data[qty]))
        return np.asarray(time), np.asarray(y)
        
    def DeltaTimList (self, msg, sen_num):
        """ Route that generates two arrays of time(s) and delta time, that is 
        the time between message. The particular message and sensor for this list
        are inputs - NOT TESTED"""
        tim    = []
        delta  = []
        first = True
        for ele in self.sequence:
            if ele.name == msg and ele.data['sensor'] == sen_num:  

                if (first):
                    prev_time = ele.time
                    first  = False
                else:
                    tim.append (ele.time)
                    delta.append (1./(ele.time - prev_time))
                    prev_time = ele.time
                    
        return tim, delta
    
    def FindAnnotate (self, label):
        """ Under construction """
        for item in self.annotate:
            if self.label == label:
                return (self)

    def PosData (self, limb):
        self.player.body.UpdateCalibrate (self.calibrate)
        tim, x, y, z= [], [], [], [] 

        for ele in self.sequence:
            updates = {}
            updates = pl.UpdateLimbPos ( [ele], updates, self.sensor_dict)
            self.player.body.Update (updates)
            if limb in updates:  
                pos_dict = self.player.body.OutputPos()
                pos = pos_dict[limb]
                x.append (pos[0])
                y.append (pos[1])
                z.append (pos[2])
                tim.append (ele.time)
        #    print (ele.time)
        return (tim, x, y, z)
        
    def TrackDetails (self):
        """ return an array of data describing the track """
        begin = self.sequence[0].time
        end   = self.sequence[-1].time
        diff = end - begin
        return (np.array ([begin, end, diff]))
       
def ReadTrackList ( fp ):
    """ Function to read a list of tracks from a file. Why is this not a class?
    did not want to have a class simply being a list of Tracks """
    tracklist = [] 
    new_track = None
    for line in fp:
        # -1 used to eliminate the \n character
        # split string into elements, striping out \n and leading and trailing 
        # white spaces
        items =  [x.strip() for x in line[:-1].split(',')]
        
        if items[0] == "SA_Track":
            if new_track:               # Save previous track
                new_track.SetTimeLen()
                tracklist.append (new_track)
            new_track = Track (items[1])
        elif (items[0] == "SA_Player"):
            new_track.player = pl.Player (items[1], items[2], float(items[3]))
        elif (items[0] == "SA_Calibrate"):
            cal = {}
            for i in range (1, len(items), 2):
                xyz = items[i+1][1:-1].split()
                cal[items[i]] = np.array ([float(xyz[0]), float(xyz[1]), float(xyz[2])])
            new_track.calibrate = cal
        elif (items[0] == "SA_SensorDict"):
            for i in range (1,len(items), 2) :
                new_track.sensor_dict[int(items[i])] = items[i+1]
        elif (items[0] == "SA_Time"):         # Not sure this is used
            pass
        elif (items[0] == "SA_Annotate"):
            labels = Annotate()
            labels.ReadAnnotate ( items, 1)
            
        else:
            new_ele = Element (None, None, None)
            new_ele.Read (items)
            new_track.sequence.append (new_ele)
                    
    # Store away last track read
    if (new_track):
        new_track.SetTimeLen()
        tracklist.append (new_track)
        
    return (tracklist)

class Annotate():
    """ Simple class to give a name to an activity, for example bowling. An activity
    can contain other activities, for example 'Run up' is part of bowling
    Still UNDER CONSTRUCTION """
    def __init__ (self, name, start_time, end_time=None):
        self.label      = name
        self.start_time = start_time
        self.end_time   = end_time
        self.annotation = []
        
    def FindLabel (self, label):
        if len(self.label) == 0:
            return (None)
        
        for item in self.annoation:
            pass
        
    def ReadAnnotate (self, items, count):
        ln = len(items)
        if count >= ln :
            return
        
        while (count <= ln):
            if items[count] == "start":
                count += 1                 # Kludge to move along list
                self.start_time = float (items[count])
            elif items[count] == "end":
                count += 1                 # Kludge to move along list
                self.end_time = float (items[count])
            elif items[count] == "label":
                count += 1
                self.label = items[count]
            elif items[count] == "(":
                pass
         
class RecPlay ():
    """ Class to handle the recording and playback of tracks. A track is simply
    a atream of elements in sequence """
    def __init__ (self):
        self.track_list     = []
        self.track_name_num = 1 
        self.cur_track      = None
        self.cur_time       = 0.0   # How far into a track is the playback (in seconds)
        self.cur_pos        = 0     # How far in track_list is the playback (integer) 
        self.delta          = 0.0
        self.state          = PlayState.STOP
        self.state_change   = False # Set true when state changes - this is how we communicate to top level
        
    def SetState (self, state):
        """ If the new state is different than current state, update and set
        state_change as True. Going between play/pause not seen as a change of
        state """
        if self.state != state:
            self.state_change = True
            
            if state == PlayState.RECORD:
                self.InitialiseRecord ()
                
            elif state == PlayState.STOP:
                if self.state == PlayState.RECORD:
                    self.EndRecord()
                    self.Reset()
                
            elif state == PlayState.PAUSE:
                if self.state == PlayState.PLAY:
                    self.state = state
                    self.state_change = False

            elif state == PlayState.PLAY:
                if self.state == PlayState.PAUSE:
                    self.state = state
                    self.state_change = False

                elif self.state == PlayState.RECORD:
                    self.EndRecord()
                    self.Reset()
                else:
                    self.Reset()
                    
                
            self.state = state 
                    
            
    def Reset(self):
        """ Go back to the beginning"""
        self.cur_time   = 0.0   # How far into a track is the playback (in seconds)
        self.cur_pos    = 0     # How far in track_list is the playback (integer)
        self.start_play_time = time.time()
        self.start_track_time = self.cur_track.sequence[0].time  # Not needed now as track should start at zero
        

    def Record (self, elements):
        for item in elements:
            self.cur_track.sequence.append (item)
            
    def InitialiseRecord (self) :
        """ Give the track a name and start data time"""
        self.cur_track = Track( "Track_" + str(self.track_name_num))
        self.track_name_num += 1
        self.cur_track.start_time = dt.datetime.now()
        
    def EndRecord (self) :
        """ Work out length of track in seconds, and ensure that time is set 
        relative to first element on the list"""
        self.cur_track.SetTimeLen()
        self.track_list.append (self.cur_track)
        
    def Play (self):
        """ Returns data from the position it was last called up to the current
        elapsed time. Can handles pauses and the effect of a slider (which is just
        treated as a pause) 
        """
        ret_data = []
        if self.state == PlayState.PAUSE:
            self.start_play_time = time.time() - self.delta
            ret_data = self.GetLastElemData (10)
            return (ret_data)
       
        self.cur_time = time.time() - self.start_play_time
        start_pos = self.cur_pos
        
        #Check if already at end
        if self.cur_time > self.cur_track.t_len:
            self.cur_time = self.cur_track.t_len
            self.SetState (PlayState.PAUSE)
            
        # Not at end so handle play
        for i in range (start_pos, len(self.cur_track.sequence)):
            self.delta = self.cur_track.sequence[i].time - self.cur_track.sequence[0].time
            if self.delta < self.cur_time:
                ret_data.append (self.cur_track.sequence[i])
                self.cur_pos = i
            else:
                return (ret_data)
                
        return (ret_data)
            
    def GetLastElemData (self, depth):
        """ This is a bit of a kludge, delivers a set of elements before time point self.cur_time.
        does check if the depth is too long"""
        ret_data = []
        for i in range (0,len(self.cur_track.sequence)):
            self.delta = self.cur_track.sequence[i].time - self.cur_track.sequence[0].time
            if self.delta > self.cur_time:
                break                
        end = i
        if end < depth:
            start = 0
        else:
            start = end - depth
        for i in range (start, end):
            ret_data.append (self.cur_track.sequence[i])
        
        # Needed to work with slider
        self.cur_pos = end-1

        return (ret_data)
 
    def LoadTracklist (self, fp):
        """ Reads in track from file pointer fp. 
        Used to be a bigger method but replace with function  call"""
        self.track_list = ReadTrackList (fp)
# =============================================================================

#         new_track = None
#         for line in fp:
#             items = line[:-1].split(",")    # -1 used to eliminate the \n character
#             if items[0] == "SA_Track":
#                 if new_track:
#                     new_track.SetTimeLen()
#                     self.track_list.append (new_track)
#                 new_track = Track (items[1])
#             elif (items[0] == "SA_Player"):
#                 new_track.player = pl.Player (items[1], items[2], float(items[3]))
#             elif (items[0] == "SA_Calibrate"):
#                 cal = {}
#                 for i in range (1, len(items), 2):
#                     xyz = items[i+1][1:-1].split()
#                     cal[items[i]] = np.array ([float(xyz[0]), float(xyz[1]), float(xyz[2])])
#                 new_track.calibrate = cal
#             elif (items[0] == "SA_EUL_ANG"):
#                 if (len(items) < 10):
#                     print ("Error Insufficent data for SA_EUL_ANG", line)
#                 else:
#                     new_ele = Element (None, None, None)
#                     new_ele.Read (items)
#                     new_track.sequence.append (new_ele)
#                     
#         # Store away last track read
#         if (new_track):
#             new_track.SetTimeLen()
#             self.track_list.append (new_track)
# =============================================================================
                    
    def WriteTracklist (self, fp):
        """ fp is file pointer """
        for trk in self.track_list:
            trk.Write (fp)
    

            
 # High level class to handle sensor data for a player. At this point the extra level
# of abstraction is not needed as we only have data over WiFi, but in the future 
# the data source may include BT sensors from a bat for example                    
class Sensors ():
    def __init__ (self):
        self.sensoritems = {}   # List of items sending data
    
    def AddConTCP (self, label, tcp_ip, port, buffer_size ):
        newcon = ApparelConnection (label, tcp_ip, port, buffer_size )
        self.sensoritems[label] = newcon
 
    # At the moment this trys to connect everything
    # Probably need to add one that just connects a specific item       
    def Connect (self):
        for key, item in self.sensoritems.items():
            item.Connect()
            if item.status == ConStatus.ERROR_CONNECTING:
                print ("Failed to make connection")
                
    def ReadData (self):
        buff = []
        for key, item in self.sensoritems.items():   # Go through all the connected devices
            new_data = item.GetData ()
            if new_data:
                for elem in new_data:
                    buff.append(elem)
        return (buff)
    
    def CloseDataCon (self):
        for key, item in self.sensoritems.items():
            item.CloseConnect()
        

class ConStatus (Enum):
    DISCONNECTED     = 1
    CONNECTING       = 2
    CONNECTED        = 3
    ERROR_CONNECTING = 5
    STREAMING        = 6
#
#    
class ApparelConnection ():
    def __init__ (self, label, tcp_ip, port, buffer_size ):
        self.label  = label  # Name for connection e.g. jacket
        self.tcp_ip = tcp_ip
        self.port   = port
        self.buffer_size = buffer_size
        self.status      = ConStatus.DISCONNECTED
        self.socket      = None
  #      self.buf         = []

    def Connect (self):
        self.status = ConStatus.CONNECTING
        try :
#            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP 
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # UDP
            self.sock.connect((self.tcp_ip, self.port))
            self.sock.setblocking (0)                                    # Non blocking
            self.sock.sendto(bytes("Start", "utf-8"), (self.tcp_ip, self.port))
            self.status = ConStatus.CONNECTED
        except:
            self.status = ConStatus.ERROR_CONNECTING
            
    def SendMSG (self, msg):
        if self.status in  [ConStatus.CONNECTED, ConStatus.STREAMING]:
            self.sock.sendall (msg.encode('ascii'))
        
    def StreamData (self):
        string = 'SA_SND_DAT'
        self.SendMSG (string)
        self.status = ConStatus.STREAMING
        
    def GetData (self):
        try:
            data, addr = self.sock.recvfrom(self.buffer_size)
            buff = data.decode('utf-8')
#            print (buff)
        except:
 #           print ("Error reading socket data")
            return (None)
        return (translate_elem (buff))

    def StreamClose (self):
        string = 'SA_STP_DAT'       
        self.SendMSG (string)
        self.status = ConStatus.CONNECTED
        
    def CloseConnect (self):
        self.socket.close()
        self.status = ConStatus.DISCONNECTED

        
class PlotView ():
    """ Class to filter data from input and mantain a list of items
    that will be identified and returned. Used for plotting RT data.
    """
    def __init__ (self, index):
        self.optionslist  = []  # Items selected to be selected from
        self.plotlist     = []  # List of plot objects
        self.index = index      # Dict for converting sensor number to a name
        self.buffersize = 5.0   # Size in seconds of time 
        self.datanames = ["SA_EUL_ANG", "SA_ACC_LIN"]
        
    def ClearList (self):
        """ Empty optionlist and filterlist """
        self.optionslist = []  # List of items to select from
        self.plotlist    = []  # Items selected to be returned

    def RefreshList (self, item ):
        """ Element check to see if item is already on the list of options
        """
        #convert name
        if item.name == "SA_EUL_ANG":
            limb = self.index[item.data["sensor"]]
            limb_x = limb+"_angle_X"
            limb_y = limb+"_angle_Y"            
            limb_z = limb+"_angle_Z"
            # Check if in options list, if not add
            if limb_x not in self.optionslist:
                self.optionslist.append (limb_x)
                self.optionslist.append (limb_y)
                self.optionslist.append (limb_z)
                return (True)
        elif item.name == "SA_ACC_LIN":
            limb = self.index[item.data["sensor"]]
            limb_x = limb+"_acc_X"
            limb_y = limb+"_acc_Y"            
            limb_z = limb+"_acc_Z"
            # Check if in options list, if not add
            if limb_x not in self.optionslist:
                self.optionslist.append (limb_x)
                self.optionslist.append (limb_y)
                self.optionslist.append (limb_z)
                return (True)
        return(False)
            
    def UpdatePlotList (self, selecteditems):
        """ There has been a change to the list of plots selected, so update 
        the plotlist according"""
        
        plotnamelist =  [x.name for x in self.plotlist]
        # Do we need to add item
        for item in selecteditems:
            if item not in plotnamelist:
                self.plotlist.append ( PlotData (item, self.buffersize))
    
        for item in plotnamelist:
            if item not in selecteditems:
                self.plotlist = [x for x in self.plotlist if x.name != item]
        print ([x.name for x in self.plotlist])       
                
    def UpdatePlot (self, ele, selecteditems):
        """ update plot with data contained in ele if it is relevant 
        First check that the ele is piece of data we are interested in 
        plotting"""

        if ele.name not in self.datanames:
            return
        
        for item in selecteditems:     
            # Find if limbs match
            ind = item.find('_')
            if item[0:ind] ==  self.index[ele.data["sensor"]]:  # Check name like spine
                if (item[ind+1:-2] == 'angle' and ele.name == 'SA_EUL_ANG') or (item[ind+1:-2] == 'acc'and ele.name == 'SA_ACC_LIN'): # This is messy
                    for plot in self.plotlist:
                        if plot.name == item:
                            plot.x = np.append (plot.x, ele.time)
                            plot.y = np.append (plot.y, ele.data[item[ind+1:]])
                          
                            diff = plot.x[-1] - plot.x[0]
                            if (diff > self.buffersize):
                                for i in range (0, len(plot.x)):
                                    if (plot.x[-1] - plot.x[i]) < self.buffersize:
                                        break
                                plot.x = plot.x[i:]
                                plot.y = plot.y[i:]
                        

class PlotData ():
    """ Data to be plotted"""
    def __init__ (self, name, xwin):
        self.name = name
        self.x   = np.array ([])
        self.y   = np.array ([])
        self.timewin = xwin
        
    def GetPlotData (self):
        if len (self.x) > 0:
            x = self.x - self.x[-1]
            rx = x[(x > -5.0)]
            ry = self.y[(x > -5.0)]
        else:
            x = np.array([0.])
            rx = x
            ry = x

        return (rx, ry)

class DataView ():
    """ Class to fitler data from input and mantain a list of items
    that will be identified and returned. Used for dataview
    """
    def __init__ (self):
        self.optionslist = []  # List of items to select from
        self.filterlist  = []  # Items selected to be returned
        self.max_datapoints = 400 
        
    def ClearList (self):
        """ Empty optionlist and filterlist """
        self.optionslist = []  # List of items to select from
        self.filterlist  = []  # Items selected to be returned
        
    def RefreshList (self, item):
        if item.name not in self.optionslist:
            self.optionslist.append (item.name)
            return (True)
        if item.data["sensor"] :
            sen = "Sensor_" + str(item.data["sensor"])
            if sen not in self.optionslist:
                self.optionslist.append (sen)
                return (True)
        return (False)
                
    def SetFilter (self, item):
        if item not in self.filterlist:
            self.filterlist = [item]  # Currently only allow one item for filtering
        else:
            print ("Warning, item already in DataView list")
            
    def CheckDataView (self, elem):
        if elem:
            name = elem.name
            snum = "Sensor_" + str(elem.data["sensor"])
            if name in self.filterlist:
                return (elem)
            elif snum in self.filterlist:
                return (elem)
        
        return (None)
            
#
# Reads data string from sensor and returns a list of elements for processing
# NOT COMPLETE Still needs to be worked on
def translate_elem ( item ):
    lines = item.split (';')
    ele_list = []
    for line in lines[:-1]:   # Don't include blank item
        li = line.split (',')
        if li[0] == 'SQ':
            if len (li) == 7:
                name = "SA_BNO_QUA"
                sensor = int (li[1])
                time   = float(li[2])/1000.
                data   = {"sensor":sensor, "qw":float(li[3]), "qx":float(li[4]), "qy":float(li[5]), "qz":float(li[6])}
                new_elem = Element (name, time, data)
                ele_list.append (new_elem)
            else:
                print ("Wrong number of parameters for SQ, expecting 7 got ", len(li))
                print (li)
 
        elif li[0] == 'SE':
            if len (li) == 6:
                name = "SA_EUL_ANG"
                sensor = int (li[1])
                time   = float(li[2])/1000.
                data   = {"sensor":sensor, "angle_X":float(li[3]), "angle_Y":float(li[4]), "angle_Z":float(li[5])}
                new_elem = Element (name, time, data)
                ele_list.append (new_elem)
            else:
                print ("Wrong number of parameters for SE, expecting 6 got ", len(li))
                print (li)
                
        elif li[0] == 'SO':
            if len (li) == 6:
                name = "SA_BNO_EUL"
                sensor = int (li[1])
                time   = float(li[2])/1000.
                data   = {"sensor":sensor, "angle_x":float(li[3]), "angle_y":float(li[4]), "angle_z":float(li[5])}
                new_elem = Element (name, time, data)
                ele_list.append (new_elem)
            else:
                print ("Wrong number of parameters for SE, expecting 6 got ", len(li))
                print (li)
                
        elif li[0] == 'CL':
            if len(li) == 4:
                name = "SA_BNO_CAL"
                sensor = int (li[1])
                time   = float(li[2])/1000.
                data   = {"sensor":sensor, "cal":int(li[3])}
                new_elem = Element (name, time, data)
                ele_list.append (new_elem)
            else:
                print ("Wrong number of parameters for CL, expecting 2 got ", len(li))
                print (li)
                
        elif li[0] == 'AC':
            if len(li) == 6:
                name = "SA_ACC_LIN"
                sensor = int (li[1])
                time   = float(li[2])/1000.
                data   = {"sensor":sensor, "acc_X":float(li[3]), "acc_Y":float(li[4]), "acc_Z":float(li[5])}
                new_elem = Element (name, time, data)
                ele_list.append (new_elem)
            else:
                print ("Wrong number of parameters for CL, expecting 2 got ", len(li))
                print (li)
        else:
            print ("Unknown item: ", item )
        
    return (ele_list)

def TrackListDetails (tracklist):
    print ("Hello")
    """ Go through tracklist and extract basic information 
    return a dataframe with the information in """
    for trk in tracklist:
        info = trk.TrackDetails()
    return (info)

def ConvertToEarthCoord (sx, sy, sz, ang_x, ang_y, ang_z):
    """ Function that converts a vector quantity in the form of 3 arrays 
    (sx, sy, sz) in the sensor frame of reference into one in a earth frame 
    of reference using the provided angle arrays """
      
    new_sx = np.array([])
    new_sy = np.array([])
    new_sz = np.array([])
    if len(sx) != len (ang_x):
        print ("Warning dimensions of arrays different")
        return (new_sx, new_sy, new_sz)
    
    for i in range (0, len(sx)):
        vec = np.array([sx[i], sy[i], sz[i]]).reshape((3,1))
        ang = np.array ([ang_x[i], ang_y[i], ang_z[i]])
        rot = pl.RotationMat (ang)
        new_vec = rot.T * vec
        new_sx = np.append (new_sx, new_vec[0])
        new_sy = np.append (new_sy, new_vec[1])
        new_sz = np.append (new_sz, new_vec[2])
        
    return (new_sx, new_sy, new_sz)

def CumulativeIntegration (x, t):
    """ Cumulative Sum integrating the variable x in time, using central trapizodal integration """
    cs = np.array([])
    sz = len(x)
    if len(x) != len(t):
        print ("Error, array length error in cumulative integration function" )
    elif len (x) <= 1 :
        print ("Error, array length less than or equal to 1, so unable to integrate" )
    else:
        sm  = 0.0
        dt1 = (t[1] - t[0])/2
        xm1 = (x[1] + x[0])/2
        sm  += dt1*xm1             # Accumulate the area
        cs = np.append (cs, sm)
        for i in range (1,sz-1):
            dt2 = (t[i+1] - t[i])/2
            xm2 = (x[i] + x[i+1])/2
            sm += dt1*xm1 + dt2*xm2  # Accumulate the area
            cs = np.append (cs, sm)
            dt1 = dt2
            xm1 = xm2
        sm += dt2*xm2             # Accumulate the area
        cs = np.append (cs, sm )
        return ( cs )

def AngularVel (a, t):
    """ Anglular velocity """
    ang   = np.diff (a)
    delta = np.diff (t)
    return ( ang/delta)

def Velocity (x, y, z, t, conv):
    """ take the time series position vector and return component velocity 
    and speed """ 
    dx = np.diff (x)
    dy = np.diff (y)
    dz = np.diff (z)
    dt = np.diff (t)
    
    vx = conv*dx/dt 
    vy = conv*dy/dt 
    vz = conv*dz/dt
    
    sp = np.sqrt (vx*vx + vy*vy + vz*vz)
    
    return (vx, vy, vz, sp)
        
def dict_string ( dct ):
    """ Convert dictionary to string
    """
    line = ""
    for key, value in dct.items():
        line += str(key) + "," + str(value) + ","
        
    if len(line) > 0:
        return (line[0:-1])   # Don't include final commma
    else:
        return (line)
        
def TidyUpAngles ( angle_list ):
    """ Function that changing angles are continous without sudden changes of sign
    e.g. prevents 180 degree going to -180 degree """
    new_angle_list = np.array([])
    old_ang        = None
    
    for ang in angle_list:
        if old_ang:
            if (old_ang >=0) == (ang < 0):
                if abs(ang-old_ang) > 90:  # This is a bit of a kludge
                    if ang > 0 :
                        new_ang = -360 + ang
                    else:
                        new_ang = 360 + ang
                else:
                    new_ang = ang   
            else:
                new_ang = ang
        else:
            new_ang = ang
        new_angle_list = np.append (new_angle_list, [new_ang])
        old_ang = new_ang
    return (new_angle_list)  
    
if __name__ == '__main__':
    import sys
    import matplotlib.pyplot as plt
    sys.path.insert(0, '..\\..\\..\\Python_Code\\Version_04')
    import StreamData as sd
    import numpy as np
    
    try:
        fp = open ('181118SmallfiledBolng3.sat', 'r')
    except:
        print ("Error reading file")
        
    tracklist = sd.ReadTrackList (fp)
    print ("Numbers of tracks = ", len(tracklist))
    
    

