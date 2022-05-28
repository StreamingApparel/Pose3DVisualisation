# -*- coding: utf-8 -*-
"""
Software that enables a user to load a time series pose data file (.sat) and
replay the data in the form of a 3D pose, data graphs and tables. This file 
containsclasses to create a user interface using pyQt5 and control the 
main event loop for the program.

Created on Fri Jan 19 13:42:49 2018

@author: Paul Gough
"""
import sys
import time
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QSlider, QFileDialog, \
        QAction, QMdiArea, QMdiSubWindow, QDialogButtonBox, QVBoxLayout, QGroupBox, QFormLayout, QGridLayout, QHBoxLayout, QListWidget, QDialog, QApplication, qApp
from PyQt5.QtCore import *
#from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtGui import  QColor, QPainter
from PyQt5 import QtWidgets

import pyqtgraph as pyg
from pyqtgraph.Qt import QtGui, QtCore

import Viewer as vw
import StreamData as sd 
import pygame as pg
#from pygame.locals import *
import Player as pl

#from enum import Enum
from OpenGL.GL import *
from OpenGL.GLU import *

#
# Main window - it all starts here
#
class MainWindow (QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle ("SA-Analyzer")
        self.resize (1350, 850)
        
        # Add bar menu and status bar
        self.create_bar_menu()
        self.statusBar().showMessage('Message in statusbar')
        
        # Some useful variables for connecting device
        self.state        = vw.ViewStates.PLAYER_IDLE
        self.conn_garment = None 
        self.ip_address   = '192.168.1.1'
        self.ip_port      = 8080
        self.conn_list    = []  # List of names of connected items
        
        # Set up player for test purposes
        self.curplayer = pl.Player( "Marvin", "standard", 1.6 )
        self.sensor_dict = {3:"RightLowerarm", 2:"RightUpperarm", 5:"Spine", 
                            4:"LeftLowerarm", 6:"LeftUpperarm", 7:"RightHip", 8:"RightKnee",
                            9:"RightAnkle", 10:"RightFoot", 11:"LeftHip", 12:"LeftKnee", 
                            13:"LeftAnkle", 14:"LeftFoot", 15:"RightHand", 16:"LeftHand"}
        self.calib =  {"RightLowerarm": np.array([0,0,0]), "RightUpperarm": np.array([0,0,0]),"Spine": np.array([0,0,0]), "LeftLowerarm": np.array([0,0,0]), "LeftUpperarm": np.array([0,0,0])}
        self.abs_updates = {"RightLowerarm": np.array([0, 0, 0]), "RightUpperarm": np.array([0, 0, 0]), "Spine": np.array([0, 0, 0]), "LeftLowerarm": np.array([0,0,0]), "LeftUpperarm": np.array([0,0,0]) }
        self.viewer3D  = vw.PlayerViewer ([self.curplayer], (800,800))
        
        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdiArea)

        # Data widget
        self.new_table = DataTable(None)
        self.sub1=QMdiSubWindow()
        self.sub1.setWidget(self.new_table.widget)
        self.mdiArea.addSubWindow(self.sub1)
        self.sub1.setWindowTitle ("Data Viewer")
        self.sub1.setGeometry (400,200,900,300)

#        self.sub1.show()
        
        # Real-time plots
        self.activeplots = []    # List of active plot windows
        self.new_plot = RTGraph (self, [0,500,1300,300])
        self.activeplots.append (self.new_plot)
 
        # Calibration 
        self.widget_garment = GarmentStatus(self)
        self.mdi_garment=QMdiSubWindow()
        self.mdi_garment.setWidget(self.widget_garment.widget)
        self.mdiArea.addSubWindow(self.mdi_garment)
        self.mdi_garment.setWindowTitle ("Garment Status")
        self.mdi_garment.setGeometry (0,0,400,200)
#        self.mdi_garment.show()
        
        # Play and record functions

        self.widget_recplay = RecordPlay(self)
        self.mdi_recplay=QMdiSubWindow()
        self.mdi_recplay.setWidget(self.widget_recplay.widget)
        self.mdiArea.addSubWindow(self.mdi_recplay)
        self.mdi_recplay.setWindowTitle ("Record Playback")
        self.mdi_recplay.setGeometry (0,200,400,300)
#        self.mdi_recplay.show()

        # Set up timer 
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.mainUpdate) 
        self.timer.start(20)
        
        self.show ()
        
    def quit_trigger(self):
        qApp.quit()
        sys.exit()
        
    def create_bar_menu (self):
        
        # Create Root Menu Bar --------
        mbar = self.menuBar()
        file = mbar.addMenu ('File')
        view = mbar.addMenu ('View')
        conn = mbar.addMenu ('Connect')
        
        # Create action - file
        new_act =  QAction('New player...', self)
        new_act.setShortcut ('Ctrl+N')
        load_act =  QAction('Load tracks...', self)
        load_act.setShortcut ('Ctrl+L')
        save_act =  QAction('Save tracks...', self)
        save_act.setShortcut ('Ctrl+S')
        raw_act =  QAction('Log raw data...', self)
        raw_act.setShortcut ('Ctrl+R')
        quit_act = QAction('Exit', self)
        quit_act.setShortcut ('Ctrl+X')
        data_act = QAction('Data stream', self)
        plot_act = QAction('Data plots', self)
        conn_act = QAction('Connect garment...', self)
        disc_act = QAction('Disconnect garment...', self)
        
        #Create action - view
        
        # Add actions to Menu
        file.addAction(new_act)
        file.addAction(load_act)
        file.addAction (save_act)
        file.addAction (raw_act) 
        file.addSeparator ()
        file.addAction (quit_act)
        view.addAction (data_act)
        view.addAction (plot_act)
        conn.addAction (conn_act)
        conn.addAction (disc_act)
        
        # Events
        quit_act.triggered.connect(self.quit_trigger)
        new_act.triggered.connect(self.new_player_trigger)
        load_act.triggered.connect(self.load_tracks_trigger)
        save_act.triggered.connect(self.save_tracks_trigger)
        raw_act.triggered.connect(self.log_raw_trigger)
        file.triggered.connect(self.selected)
        conn_act.triggered.connect (self.conn_trigger)
        disc_act.triggered.connect (self.disc_trigger)
                               
    def new_player_trigger (self):
        print ("New Player...")
        
    def load_tracks_trigger (self):
        filename, _ = QFileDialog.getOpenFileName(self,"Load tracks", "../..","Track Files (*.sat)")
        
        if not filename:
            return
        
        try:
            self.save_fp = open (filename, "r")
        except:
            print ("Error opening track file")
            
        self.widget_recplay.recplay.LoadTracklist(self.save_fp)
        self.widget_recplay.UpdateTrackList ()
          
    def save_tracks_trigger (self):
        filename, _ = QFileDialog.getSaveFileName(self,"Save tracks","../..","Track Files (*.sat)")
        try:
            self.save_fp = open (filename, "w")
        except:
            return
        if len(self.widget_recplay.recplay.track_list) > 0:
           self.widget_recplay.recplay.WriteTracklist(self.save_fp)
        else:
            print ("No tracks to save")
        self.save_fp.close()
            
    def log_raw_trigger (self):
        pass
    
    def conn_trigger (self):
        self.sensor_name = "Jacket_BNO"
        if not self.conn_garment:
            self.conn_garment = ConnDialog(self.ip_address, self.ip_port, self.sensor_name)
        self.conn_garment.show()
        if self.sensor_name not in self.conn_list:
            self.conn_list.append (self.sensor_name)
           
    def disc_trigger (self):
        pass
        
    def selected(self,q):
        print(q.text() + ' selected')
        
    def update_plots (self, pdata):
        for plot in self.activeplots:
            plot.UpdatePlot(pdata)
            
    def clear_plots (self):
        for plot in self.activeplots:
            plot.ClearPlot() 
        
    #==========================================================================
    # Main event loop
    #==========================================================================
    def mainUpdate (self):
        
        """ Main loop that handles 3D viewer and realtime graphs"""
        
        # React to key press on 3D viewer
        for event in pg.event.get():
            self.viewer3D.ProcessEvent (event, None)
            
        # Check if rec/play back button pressed
        if (self.widget_recplay.recplay.state_change == True):
            self.clear_plots()
            if self.widget_recplay.recplay.state == sd.PlayState.RECORD:
                self.state = vw.ViewStates.RECORD
                self.widget_recplay.recplay.cur_track.SetCalibrate (self.calib)
                self.widget_recplay.recplay.cur_track.SetPlayer (self.curplayer)  # Should make a copy
                self.widget_recplay.recplay.cur_track.SetSensorDict (self.sensor_dict)
            elif self.widget_recplay.recplay.state == sd.PlayState.PLAY:
                self.state = vw.ViewStates.PLAYBACK
            elif self.widget_recplay.recplay.state == sd.PlayState.PAUSE:
                self.state = vw.ViewStates.PLAYBACK
            elif self.widget_recplay.recplay.state == sd.PlayState.STOP:
                self.state = vw.ViewStates.PLAYER_IDLE  # If this not true, will be correct with next code
            self.widget_recplay.recplay.state_change = False
                
        # Examine state and react accordingly
        if self.state == vw.ViewStates.PLAYER_IDLE:
            self.abs_updates = {"RightLowerarm": np.array([0, 0, 0]), "RightUpperarm": np.array([0, 0, 0]), "Spine": np.array([0, 0, 0]), "LeftLowerarm": np.array([0,0,0]), "LeftUpperarm": np.array([0,0,0]) }
            if self.conn_garment:
                if self.conn_garment.garment_sensors:
                    for item in self.conn_list:
                        if self.conn_garment.garment_sensors.sensoritems[item].status == sd.ConStatus.CONNECTED:
                            self.state = vw.ViewStates.STREAMING
                            
        elif self.state == vw.ViewStates.STREAMING:
            new_data = self.conn_garment.garment_sensors.ReadData()
#            angles = vw.GenerateEulerAngles (new_data)
            self.new_table.UpdateTable (new_data)
#            self.new_table.UpdateTable (angles)           
            if new_data:
                self.abs_updates = pl.UpdateLimbPos ( new_data, self.abs_updates, self.sensor_dict)
            self.update_plots(new_data)

        elif self.state == vw.ViewStates.CALIBRATE:
            new_data = self.conn_garment.garment_sensors.ReadData()
#            angles = vw.GenerateEulerAngles (new_data)
            for item in new_data:
                self.calib = self.widget_garment.Calibrate(item, self.calib, self.sensor_dict)
                
        elif self.state == vw.ViewStates.RECORD:
            new_data = self.conn_garment.garment_sensors.ReadData()
#            angles = vw.GenerateEulerAngles (new_data)
            self.widget_recplay.recplay.Record (new_data)
#            self.widget_recplay.recplay.Record (angles)
            self.new_table.UpdateTable (new_data)
#            self.new_table.UpdateTable (angles)
            self.abs_updates = pl.UpdateLimbPos ( new_data, self.abs_updates, self.sensor_dict)
            self.update_plots(new_data)
                
        elif self.state == vw.ViewStates.PLAYBACK:
           # self.curplayer = self.widget_recplay.recplay.cur_track.player
            if self.conn_garment:
                bitbucket = self.conn_garment.garment_sensors.ReadData()  # Read but ignore any new RT data during playback
            self.calib     = self.widget_recplay.recplay.cur_track.calibrate
            new_data = self.widget_recplay.recplay.Play()
            self.new_table.UpdateTable (new_data)
            self.abs_updates = pl.UpdateLimbPos ( new_data, self.abs_updates, self.sensor_dict)
            self.widget_recplay.UpdateSlider ()
            self.update_plots(new_data)
            
        # Should only need to update this when a change occuts
        # Should really put a quick check here to see if things have changed
        # For FFHB don't need this calibration step
        #self.curplayer.body.UpdateCalibrate (self.calib)
        self.curplayer.body.Update (self.abs_updates)
  
        # Draw the 3D image
        glClearColor( 0.2,0.2,0.2 ,0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLineWidth(1)    
        self.viewer3D.DrawGround()
        glLineWidth(3)    
        self.viewer3D.DrawPlayer (0)
        self.viewer3D.DrawPlayerSolid (0)
        
        pg.display.flip()
        self.timer.start(10)
#-----------------------------------------------------------------------------
# Connections popup dialog
#-----------------------------------------------------------------------------
class ConnDialog(QDialog):
    def __init__(self, ip_address, ip_port, sensor_name):
        super(ConnDialog, self).__init__()
        self.ip_address = ip_address
        self.ip_port = ip_port
        self.sensor_name = sensor_name
        self.garment_sensors = None
        self.createFormGroupBox()
 
        self.buttonBox   = QDialogButtonBox()
        self.but_connect = QPushButton("Connect", default=True)
        self.but_connect.clicked.connect (self.connectClicked)
        self.but_cancel  = QPushButton("Cancel", default=True)
        self.but_cancel.clicked.connect (self.cancelClicked)
        self.buttonBox.addButton (self.but_connect, QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton (self.but_cancel,  QDialogButtonBox.RejectRole)
         
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
 
        self.setWindowTitle("TCP Connection")
 
    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox("")
        layout = QFormLayout()
        self.get_ip_address  = QLineEdit(self.ip_address)
        self.get_ip_port     = QLineEdit(str(self.ip_port))
        self.get_buffer_size = QLineEdit('1024')
        layout.addRow(QLabel("IP Address:"), self.get_ip_address)
        layout.addRow(QLabel("Port:"), self.get_ip_port)
        layout.addRow(QLabel("Buffer Size:"), self.get_buffer_size)
        self.connect_status = QLabel("Waiting to connect")
        layout.addRow (self.connect_status)
        self.formGroupBox.setLayout(layout)
        
    def cancelClicked (self):
        self.connect_status.setText("Waiting to connect")
        self.connect_status.repaint()
        self.hide()
        
    def connectClicked (self):
        count = 0 
        self.connect_status.setText("Connecting")
        self.connect_status.repaint()
        new_ip   = self.get_ip_address.text()
        new_port = int (self.get_ip_port.text())
        new_buffer = int (self.get_buffer_size.text())
        self.ip_address = new_ip
        self.ip_port    = new_port
        self.buffer_size = new_buffer
        
        # Add to connected sensors list
        if not self.garment_sensors:        
            self.garment_sensors = sd.Sensors()
        self.garment_sensors.AddConTCP (self.sensor_name, self.ip_address, self.ip_port, self.buffer_size )
        while self.garment_sensors.sensoritems[self.sensor_name].status != sd.ConStatus.CONNECTED:
            count += 1
            self.connect_status.setText(dynamic_string ('Connecting', '.', count))
            self.connect_status.repaint()
            self.garment_sensors.Connect()
            if count > 4:
                self.connect_status.setText('Connection failed')
                self.connect_status.repaint()
                return

        print ("Made connection, assigning garment_sensor")
        self.hide()
#-----------------------------------------------------------------------------
# Window that shows the status of the garment and sensors
#-----------------------------------------------------------------------------
class GarmentStatus(QWidget):
    def __init__(self, parent):

        super(GarmentStatus, self).__init__()
        self.parent = parent 
        self.widget = QWidget()
        self.but_calibrate = QPushButton("Calibrate", default=True)
        self.but_calibrate.clicked.connect(self.Trigger_Calibrate)
        self.label_status  = QLabel('Status: Active')
        self.label_freq    = QLabel('')
        self.label_freq.setStyleSheet("font: 12pt Arial MS")
        self.label_status.setStyleSheet("font: 12pt Arial MS")
        self.but_calibrate.setStyleSheet("font: 12pt Arial MS")
        self.garment_view  = DrawJacket(self)
        self.garment_view.setGeometry (0,0,100,150)
        
        self.grid = QGridLayout(self.widget)

        self.grid.setSpacing(10)
        self.grid.addWidget (self.label_status, 1,0, 2,0)
        self.grid.addWidget (self.label_freq, 3,0)
        self.grid.addWidget (self.but_calibrate, 4, 0)
        self.grid.addWidget (self.garment_view, 1,1, 4,1)
    
    def Trigger_Calibrate (self):
        self.parent.state = vw.ViewStates.CALIBRATE
        self.calibrate_start =  time.time()
        self.waittime = 5 
        self.caltime  = 5  # Calibrate for 5 s
        self.caldict  = {}
        
    def Calibrate (self, new_data, cal_data, sensorlist):
        """ Function that initially waits, then starts to capture angle data, finally 
        it averages the angle data and returns the new data in the cal_dat dict"""
        if new_data == None:
            return (cal_data)
        
        if new_data.name != 'SA_EUL_ANG':
            return (cal_data)
        
        delta = time.time() - self.calibrate_start
    
        if delta > self.waittime:
            if delta < (self.waittime + self.caltime):
            # accumulate data
                sensor = new_data.data['sensor']
                angles = np.array([new_data.data['angle_X'], new_data.data['angle_Y'], new_data.data['angle_Z']])
                limb = sensorlist[sensor]
                if limb in self.caldict:
                    self.caldict[limb][0] += 1
                    self.caldict[limb][1] += angles
                else:
                    # Add a sensor if not on list
                    self.caldict[limb] = [1, angles]
                self.label_status.setText ("Calibrating")
                self.label_status.repaint()
            
            else:
                self.state = vw.ViewStates.STREAMING
                for key, val in self.caldict.items():
                    average_angle = val[1]/val[0]
                    cal_data[key] = average_angle
                print ("Calibration complete")
                print (cal_data)
                self.parent.state = vw.ViewStates.STREAMING
                return (cal_data)
                  
        self.label_status.setText ("Calibrating in 5 s")
        self.label_status.repaint()
        return (cal_data)
        
#-----------------------------------------------------------------------------
# Window that contains record and playback functions
#-----------------------------------------------------------------------------
class RecordPlay(QWidget):
    def __init__(self, parent):

        super(RecordPlay, self).__init__()
        self.parent    = parent 
        self.widget    = QWidget()
        self.but_rec   = QPushButton("Record", default=True)
        self.but_play  = QPushButton("Play/Pause", default=True)
        self.but_stop  = QPushButton("Stop", default=True)
        self.but_begin = QPushButton("Begin", default=True)

        self.but_rec.clicked.connect (self.recClicked)
        self.but_play.clicked.connect (self.playClicked)
        self.but_stop.clicked.connect (self.stopClicked)
        self.but_begin.clicked.connect (self.beginClicked)

        self.time  = QLabel('0.00')
        
        self.but_layout = QHBoxLayout()
        self.but_layout.addWidget(self.but_rec)
        self.but_layout.addWidget(self.but_play)
        self.but_layout.addWidget(self.but_stop)
        self.but_layout.addWidget(self.but_begin)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)
        self.slider.setMaximum(1000)
        self.slider.sliderMoved.connect (self.SliderChanged)

        self.slide_layout = QHBoxLayout()
        self.slide_layout.addWidget(self.time)
        self.slide_layout.addWidget(self.slider)
        self.list = QListWidget()
        self.list.itemClicked.connect(self.ListClicked)
        
        self.full_layout = QVBoxLayout(self.widget)
        self.full_layout.addWidget (self.list)
        self.full_layout.addLayout (self.slide_layout)
        self.full_layout.addLayout (self.but_layout)
                
        self.recplay = sd.RecPlay()   # Create object for 
        
    def recClicked (self):
        print ("Record clicked") 
        self.recplay.SetState (sd.PlayState.RECORD)
        self.but_rec.setStyleSheet("background-color:rgb(250,90,90)")
        
    def playClicked (self):
        print ("Play clicked")
        if self.recplay.state == sd.PlayState.PLAY:   
            self.recplay.SetState (sd.PlayState.PAUSE)
        else: 
            self.recplay.SetState (sd.PlayState.PLAY)
            
    def stopClicked (self):
        print ("Stop clicked")
        if self.recplay.state == sd.PlayState.RECORD:
            self.but_rec.setStyleSheet("")   # Set the record button back to default background
        self.recplay.SetState (sd.PlayState.STOP)
        self.UpdateTrackList ()
        
    def beginClicked (self):
        self.recplay.Reset()
    
    def UpdateTrackList (self):
        self.list.clear()
        for track in self.recplay.track_list:
            self.list.addItem(track.name)
            
    def ListClicked (self):
        row = self.list.currentRow()
        print ("List clicked ", row)
        self.recplay.cur_track = self.recplay.track_list[row]
        self.recplay.SetState (sd.PlayState.PAUSE)
        self.recplay.Reset()
        self.ResetSlider ()
        
    def SliderChanged (self):
        print ("Slider Value =", self.slider.value())
        self.recplay.cur_time = self.recplay.cur_track.t_len * (self.slider.value()/1000.)
        
    def ResetSlider (self):
        self.slider.setValue(0)
        
    def UpdateSlider (self):
        self.time.setText('{:.2f}'.format(self.recplay.cur_time))
        self.slider.setValue (int(1000*self.recplay.cur_time/self.recplay.cur_track.t_len))
        
        
        
class DrawJacket (QWidget):
    def __init__(self, parent):
        super(DrawJacket, self).__init__(parent)
        self.paint = QPainter()
        self.paint.begin (self)
#        self.setGeometry(0,0,200,200)
        radx = 30 
        rady = 30
        self.paint.setPen (Qt.red)
        center = QPoint (0,0)
        self.paint.drawEllipse(center,radx,rady)
        self.paint.setBrush(QColor(200, 200, 200))
        self.paint.drawRect(0, 0, 90, 60)
        self.paint.end()
        print ("DrawJack", self.size())
        
    def paintEvent(self, event):
        self.paint.begin (self)
#        self.setGeometry(0,0,200,200)
        radx = 30 
        rady = 30
        self.paint.setPen (Qt.red)
        center = QPoint (0,0)
        self.paint.drawEllipse(center,radx,rady)
        self.paint.setBrush(QColor(255, 255, 255))
        self.paint.drawRect(0, 0, self.size().width()-1, self.size().height()-1)
        self.paint.end()
#        print ("paintEvent", self.size().height())        
        
    def sizeHint(self):
        return QSize(150, 150)
    
    def jacketPolyline (self, height, width):
        pass

#-----------------------------------------------------------------------------
# Real-time plot graphs
#-----------------------------------------------------------------------------     
class RTGraph (QWidget):
    def __init__(self, parent, pos):
        super(RTGraph, self).__init__()
        
        self.plots = []  # List of data to plot
        
        self.plotWidget = pyg.PlotWidget()
        self.widget = QWidget()
        self.layout = QHBoxLayout(self.widget)
        self.ylist = QListWidget()
        self.ylist.setSelectionMode (QListWidget.MultiSelection)
        self.layout.addWidget(self.ylist, 1)
        self.ylist.itemClicked.connect(self.ItemClicked)
        self.layout.addWidget (self.plotWidget, 4)
        
        self.mdi_rt_graph = QMdiSubWindow()
        self.mdi_rt_graph.setWidget(self.widget)
#        for i in range (3):
#            self.plotWidget.plot(x, y[i], pen=(i,3)) 
        parent.mdiArea.addSubWindow(self.mdi_rt_graph)
        self.mdi_rt_graph.setWindowTitle ("Real-time graphs")
        self.mdi_rt_graph.setGeometry (pos[0],pos[1],pos[2],pos[3])
        
        self.plotview = sd.PlotView(parent.sensor_dict)
        self.timelapse = 5.0 # default is last 5 seconds
        
        self.max_plot = 4
        self.graph = []
        self.plt = self.plotWidget
        self.plt.addLegend()
        self.plt.showGrid(x=True, y=True)
        self.plt.setLabel('bottom','time','s')
        self.plt.setRange (xRange=[-5.0,0.], yRange=[-180.,180.])
        for i in range (0,self.max_plot):
            self.graph.append (self.plt.plot())
            
    def ItemClicked(self, item):
        # Update list of selected items, when user makes a selection or deselection
        self.plots = [item.text() for item in self.ylist.selectedItems()]
        self.plotview.UpdatePlotList (self.plots)
        
    def ClearPlot (self):
        """ Clear any running plots """
        # Empty buffers
        for plot in self.plotview.plotlist:
            plot.x = []
            plot.y = []
        # Clear plot
        for i in range (0,self.max_plot):
          x = []
          y = []
          name = ''
          self.graph[i].setData(x, y, pen = i, name = name)
          self.graph[i].clear()
            
    def UpdatePlot (self, ele_list ):
        """ Take in new data and update plot """
        if len(ele_list) == 0:
            return
        
        # Check to ensure plot list is upto date
        for ele in ele_list:
            update = self.plotview.RefreshList(ele)
            
            if (update):
                self.ylist.clear()
                for item in self.plotview.optionslist:
                    self.ylist.addItem(item)
                    
            if self.plots:
                self.plotview.UpdatePlot (ele, self.plots)

        i = 0
        for i in range (0,self.max_plot):
            if i < len(self.plotview.plotlist):
                x, y = self.plotview.plotlist[i].GetPlotData()
                name = self.plotview.plotlist[i].name
            else:
                x = y = []
                name = ''

            self.graph[i].setData(x, y, pen = i, name = name)

        
#-----------------------------------------------------------------------------
# Data tables
#-----------------------------------------------------------------------------
class DataTable (QWidget):
    def __init__(self, parent):
        super(DataTable, self).__init__(parent)

        self.widget = QWidget()
        self.layout = QHBoxLayout(self.widget)
        self.list = QListWidget()
        self.layout.addWidget(self.list, 1)
        self.list.itemClicked.connect(self.ItemClicked)
#        self.list.addItem("Item 1")
        self.tableWidget = QTableWidget()
        self.layout.addWidget (self.tableWidget, 4)
        self.tableWidget.setRowCount(5)
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setHorizontalHeaderLabels (['Msg', 'Time(s)'])
#         Adding this dynamic column resizing used to much computing power!
#        header4 = self.tableWidget.horizontalHeader()
#        header4.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidget.setItem(1, 0, QtGui.QTableWidgetItem())

        self.tablelist = []     # Used to store elements that appear in table
        
        # Set up DataView object to handle list 
        self.dataview = sd.DataView()
        
    def UpdateTable (self, ele_list):
        if len(ele_list) == 0:
            return
        
        # Check if item in option list - if not add it and update list
        for ele in ele_list:
            update = self.dataview.RefreshList(ele)  # Update true if a new option added to optionlist
            if update:
                self.list.clear()
                for item in self.dataview.optionslist:
                    self.list.addItem(item)
            
            # Is the element a selected item, if so update table entry
            for item in self.dataview.filterlist:
                update_ele = False
                if "Sensor" in item:
                    str_items = item.split ('_')
                    sen_num = int (str_items[1])
                    ele_sen_num = int(ele.data["sensor"])
                    if sen_num == ele_sen_num:
                        update_ele = True
                else :
                    if item == ele.name:
                        update_ele = True
                    
                if (update_ele):
                    indx = 0
                    found = False
                    for item in self.tablelist:
                        if item.name == ele.name and item.data['sensor'] == ele.data['sensor']:
                            found = True
                            break
                        indx += 1
                        
                    if not found :
                        self.tablelist.append (ele)

                    self.tableWidget.setItem (indx, 0, QTableWidgetItem (ele.name))
                    # Kludge to handle rare case when different tracks have different sensors
                    try:
                        self.tableWidget.item(indx,0).setBackground(QtGui.QColor(200,240,200))
                    except:
                        self.dataview.ClearList()
                    
                    
                    self.tableWidget.setItem (indx, 1, QTableWidgetItem ("{0:.2f}".format(ele.time)))
                    i = 1
                    for key, val in ele.data.items():
                        i += 1
                        if isinstance(key, str): 
                            self.tableWidget.setItem (indx, i, QTableWidgetItem(key))
                        else:
                            self.tableWidget.setItem (indx, i, QTableWidgetItem(str(key)))
                        i += 1
                        if isinstance(val, str): 
                            self.tableWidget.setItem (indx, i, QTableWidgetItem(val))
                        else:
                            self.tableWidget.setItem (indx, i, QTableWidgetItem(str(val)))
                
    def ItemClicked (self, item):
        self.tablelist = []
        self.tableWidget.clearContents()
        self.dataview.SetFilter (item.text())
                         
                
#    def SetSensorNum (self, n):
#        self.sensor_num = n
        

def dynamic_string (string, ch, i):
    return (string + (i%10)*ch )
        
if __name__ == '__main__':
    print ("Starting App")
    app = QApplication(sys.argv)
    menus = MainWindow()
    sys.exit(app.exec_())