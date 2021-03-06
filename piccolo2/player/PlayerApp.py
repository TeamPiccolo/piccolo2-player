# Copyright 2014-2016 The Piccolo Team
#
# This file is part of piccolo2-player.
#
# piccolo2-player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# piccolo2-player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with piccolo2-player.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['main']

import piccolo2.client
from piccolo2 import PiccoloCompress

from PyQt4 import QtGui, QtCore
import player_ui
import connect_ui
from ScheduleList import *
from Schedule import ScheduleDialog
from SpectraList import SpectraListDialog
import datetime

TIMEFORMAT = "%Y-%m-%dT%H:%M:%S"

class IntegrationTimes(QtGui.QStandardItemModel):
    def __init__(self,*args,**keywords):

        QtGui.QStandardItemModel.__init__(self,*args,**keywords)

        self._shutters = None
        self._spectrometers = None
        self._piccolo = None
        self._listenerID = None
        self._updatePiccolo = True

        self.itemChanged.connect(self.updateIntegrationTime)


    def updateIntegrationTime(self,index):
        if index.column() >= len(self._shutters):
            #the last column is spectrometer enable/disable switches
            isChecked = index.checkState()
            if(index.checkState()):
                index.setText("true")
            else:
                index.setText("false")
            if self._updatePiccolo:
                self._piccolo.setSpectrometerEnabledStatus(enabled=isChecked,
                    spectrometer=self._spectrometers[index.row()])
            return

        try:
            data = float(index.text())
        except:
            index.setForeground(QtGui.QBrush(QtGui.QColor('red')))
            return
        index.setForeground(QtGui.QBrush(QtGui.QColor('black')))
        if self._updatePiccolo:
            self._piccolo.setIntegrationTime(shutter=self._shutters[index.column()],
                                             spectrometer=self._spectrometers[index.row()],
                                             milliseconds=data)


    def updateIntegrationTimeDisplay(self,spectrometer,shutter):
        j = self._spectrometers.index(spectrometer)
        i = self._shutters.index(shutter)
        data = self._piccolo.getIntegrationTime(shutter=shutter,
                                                spectrometer=spectrometer)
        self._updatePiccolo = False
        self.setItem(j,i,QtGui.QStandardItem(str(data)))
        self._updatePiccolo = True
            
    def piccoloConnect(self,piccolo):
        self._piccolo = piccolo
        self._shutters = self._piccolo.getShutterList()
        self._spectrometers = self._piccolo.getSpectrometerList()

        self.setRowCount(len(self._spectrometers))
        self.setColumnCount(len(self._shutters)+1)
        last_col = len(self._shutters)
        for i in range(len(self._shutters)):
            self.setHorizontalHeaderItem(i,QtGui.QStandardItem(self._shutters[i]))
        self.setHorizontalHeaderItem(last_col,QtGui.QStandardItem("enabled"))

        for j in range(len(self._spectrometers)):
            spec_item = QtGui.QStandardItem(self._spectrometers[j])
            self.setVerticalHeaderItem(j,spec_item)

            enable_item = QtGui.QStandardItem("true")
            enable_item.setCheckable(True)
            enable_item.setEditable(False)
            enable_item.setCheckState(2)
            self.setItem(j,last_col,enable_item)
            

        for spectrometer in self._spectrometers:
            for shutter in self._shutters:
                self.updateIntegrationTimeDisplay(spectrometer,shutter)
        
        

class ConnectDialog(QtGui.QDialog,connect_ui.Ui_ConnectDialog):
    def __init__(self,parent=None):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

    def setConnection(self,connection,data):
        if connection == 'http':
            self.connectHTTP.setChecked(True)
            self.serverURL.setText(data)
        elif connection == 'xbee':
            self.connectXBee.setChecked(True)
            self.xbeeSerial.setText(data)
        elif connection == 'xbee auto':
            self.connectXBeeAuto.setChecked(True)
            self.xbeeBaud.setText(data)
        else:
            raise RuntimeError, 'unkown connection type',connection

    @property
    def getConnectionMethod(self):
        if self.connectHTTP.isChecked():
            return 'http'
        elif self.connectXBee.isChecked():
            return 'xbee'
        elif self.connectXBeeAuto.isChecked():
            return 'xbee auto'
        else:
            raise RuntimeError, 'Unkown connection method'

    def getData(self,parent=None):
        dialog = ConnectDialog(parent=parent)
        result = self.exec_()

        if result != QtGui.QDialog.Accepted:
            return

        method = self.getConnectionMethod
        data = None
        if method == 'http':
            data = self.serverURL.text()
        elif method == 'xbee':
            data = self.xbeeSerial.text()
        elif method == 'xbee auto':
            data = self.xbeeBaud.text()
        return method,str(data)

class PlayerApp(QtGui.QMainWindow, player_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PlayerApp, self).__init__(parent)
        self.setupUi(self)

        # the piccolo connection
        self._piccolo = None
        self._connectionType = 'http'
        self._connectionData = 'http://localhost:8080'

        # status buttons
        self.syncTimeButton.clicked.connect(self.syncTime)

        # the integration times
        self._times = IntegrationTimes()
        self.integrationTimeView.setModel(self._times)

        # connect recording buttons
        self.startRecordingButton.clicked.connect(self.startRecording)
        self.stopRecordingButton.clicked.connect(self.stopRecording)
        self.autoButton.clicked.connect(self.autoIntegrate)
        self.darkButton.clicked.connect(self.recordDark)
        self.pauseRecordingButton.clicked.connect(self.pauseRecording)

        # connect spectra load boxes
        self._spectraList = {}
        self._updateSpectraFile = True
        self._currentFileName = None
        self._spectra = None
        self._selectedDirection = None
        self._selectedSpectrum = None
        self.selectSpectrumButton.clicked.connect(self.downloadSpectra)
        self.selectShutter.currentIndexChanged.connect(self.setSpectrumAndDirection)
        self.selectSpectrometer.currentIndexChanged.connect(self.setSpectrumAndDirection)
        self.selectSpectrum.currentIndexChanged.connect(self.setSpectrumAndDirection)
        self.displayUnits.currentIndexChanged.connect(lambda: self.spectraPlot
                .setUnits(self.displayUnits.currentText()))
        self.showLatest.clicked.connect(self.updateRealTime)


        # toggle spectra plotting (prevents multiple rapid calls)
        self._ableToPlot = True
        # hook up scheduler
        self._scheduledJobs = PiccoloSchedule()
        self._scheduledJobsDialog = ScheduleListDialog(scheduledJobs = self._scheduledJobs)

        # hook up menu
        self.action_Connect.triggered.connect(self.connectDialog)
        self.actionSave_Plot.triggered.connect(self.savePlot)
        self.action_Quit.triggered.connect(QtGui.qApp.quit)
        self.action_Add_Schedule.triggered.connect(self.addSchedule)
        self.actionList_Schedules.triggered.connect(self.scheduledJobsDialog)

        # periodically check status
        self.statusLabel = QtGui.QLabel()
        self.statusbar.addWidget(self.statusLabel)
        self.statusTimer = QtCore.QTimer()
        self.statusTimer.timeout.connect(self.status)
        # check every 5 seconds
        self.statusTimer.start(5000)        
        #check telemetry more regularly
        self.telemTimer = QtCore.QTimer()
        self.telemTimer.timeout.connect(self.telemetryStatus)
        # check every second
        self.telemTimer.start(1000)        

        self.spectrumTimer = QtCore.QTimer()
        self.spectrumInterval = 5000
        self.spectrumTimer.timeout.connect(self.updateRealTime)
        self.spectrumTimer.start(self.spectrumInterval)
        


    def syncTime(self):
        now = datetime.datetime.now()
        self._piccolo.piccolo.setClock(clock=now.strftime("%Y-%m-%dT%H:%M:%S"))

    def floatToDDMMSS(self,coord):
        "helper method to pretty-fy gps locations" 
        if isinstance(coord,float):
            formatstr = "{:d}\xB0 {:02d}' {:08.5f}\""
            if coord < 0:
                coord *= -1 
                formatstr = "-" + formatstr
            deg,minute = divmod(coord*60,60)
            minute,sec = divmod(minute*60,60)
            return formatstr.format(int(deg),int(minute),sec)
        else:
            return str(coord)

    def floatToUnits(self,val,units):
        "helper method to pretty-fy gps metadata" 
        if isinstance(val,float):
            return '{:.2f} {:s}'.format(val,units)
        else:
            return str(val)



    def updateSpectrumTimer(self):
        integrationTime = self._piccolo.piccolo.getTotalIntegrationTime()
        interval = max(2000, int(float(integrationTime)))
        print(interval)
        if interval != self.spectrumInterval:
            self.spectrumInterval = int(float(interval))
            self.spectrumTimer.setInterval(int(self.spectrumInterval))
            
    def telemetryStatus(self):
        # check if we need to update times
        now = datetime.datetime.now()
        self.localTime.setText(now.strftime("%Y-%m-%dT%H:%M:%S"))
        if self.tabWidget.currentIndex()==0 and self._piccolo!=None:
            try:
                ptime = self._piccolo.piccolo.getClock()
            except:
                ptime = None
            if ptime is not None:
                self.piccoloTime.setText(ptime.split('.')[0])

            #update location labels
            if "GPS" in self._peripherals:
                self.gpsContainerWidget.setHidden(False)
                plocation = self._piccolo.piccolo.getAuxRecord(aux_inst="GPS")
                self.gpsTime.setText(plocation['time'])
                self.longitudeLabel.setText(self.floatToDDMMSS(plocation['lon']))
                self.latitudeLabel.setText(self.floatToDDMMSS(plocation['lat']))
                self.altitudeLabel.setText(self.floatToUnits(plocation['alt'],'m'))
                self.speedLabel.setText(self.floatToUnits(plocation['speed'],'m/s'))
            else:
                self.gpsContainerWidget.setHidden(True)

            #update altimeter label
            if "Altimeter" in self._peripherals:
                self.altitudeContainerWidget.setHidden(False)
                pAltitude = self._piccolo.piccolo.getAuxRecord(aux_inst="Altimeter")
                self.altimeterLabel.setText(pAltitude+" m")
            else:
                self.altitudeContainerWidget.setHidden(True)



    def status(self):
        # handle status
        state = 'red'
        status = 'disconnected'
        if self._piccolo != None:
            try:
                pstatus = self._piccolo.piccolo.status(listener=self._piccolo.listenerID)
            except:
                pstatus = piccolo2.PiccoloStatus.PiccoloStatus()
                pstatus.connected = False
            if pstatus.connected:
                status = 'connected'
                state = 'green'
            else:
                status = 'disconnected'
                state = 'red'
            if pstatus.busy:
                status = 'busy'
                state = 'orange'
            if pstatus.paused:
                status += ', paused'
                self.pauseRecordingButton.setText("Unpause")
            else:
                self.pauseRecordingButton.setText("Pause")
            if pstatus.file_incremented:
                state = 'yellow'
                status += ', file_incr'

            if pstatus.new_message:
                msg = self._piccolo.piccolo.getMessage(listener=self._piccolo.listenerID)
                msg =msg.split('|')
                if msg[0] == 'IT':
                    spectrometer,shutter = msg[1:]
                    self._times.updateIntegrationTimeDisplay(spectrometer,shutter)
                elif msg[0] == 'warning':
                    QtGui.QMessageBox.warning(self,'Warning',msg[1],QtGui.QMessageBox.Ok)
            
            self.updateSpectrumTimer()

        self.statusLabel.setText(status)
        self.statusLabel.setStyleSheet(' QLabel {color: %s}'%state)
        self.repaint()

    def startRecording(self,start=None,end=None,interval=None):
        n = self.repeatMeasurements.value()
        if n==0 or self.infRepeat.isChecked():
            n='Inf'
        kwds ={}
        kwds['delay'] = self.delayMeasurements.value()
        kwds['nCycles'] = n
        kwds['outDir'] = str(self.outputDir.text())
        kwds['auto'] = self.checkAutoIntegrate.checkState()==2
        kwds['timeout'] = self.autoIntegrateTimeout.value()
        if start not in [None, False]:
            kwds['at_time'] = start
        if interval!=None:
            kwds['interval'] = interval
        if end!=None:
            kwds['end_time'] = end
        self._piccolo.piccolo.record(**kwds)

    def recordDark(self):
        self._piccolo.piccolo.dark()

    def autoIntegrate(self):
        self._piccolo.piccolo.setIntegrationTimeAuto()

    def pauseRecording(self):
        self._piccolo.piccolo.pause()

    def stopRecording(self):
        self._piccolo.piccolo.abort()

    def downloadLatestSpectrum(self):
        odir = str(self.outputDir.text())
        
        #TODO: can't get chunking to work with no filename
        simplify = (self.downloadSimple.isChecked() 
                or isinstance(self._piccolo,piccolo2.client.PiccoloXbeeClient))
        self._spectra = self._piccolo.piccolo.getSpectra(outDir=odir,
                fname='', simplify = simplify)

        #unlike downloadSpectra, we need to find out what file we just got
        #self._currentFileName = self._spectra[0]['FileName']
        self._plotDownloadedSpectrum()

    def updateRealTime(self):
        if self.showLatest.isChecked() and self.tabWidget.currentIndex()==2:
            self.downloadLatestSpectrum()

    def downloadSpectra(self,spectraName=None):
        odir = str(self.outputDir.text())
        if self._piccolo!=None and not spectraName:
            if odir not in self._spectraList:
                self._spectraList[odir] = []
            need_compressed = isinstance(self._piccolo, piccolo2.client.PiccoloXbeeClient)
            new_spectra = self._piccolo.piccolo.getSpectraList(outDir=odir,
                    compressed=need_compressed,haveNFiles=len( self._spectraList[odir]))
            if need_compressed:
                new_spectra = PiccoloCompress.decompressFileList(new_spectra)
            self._spectraList[odir] += new_spectra
            spectraName = SpectraListDialog.getSpectrum(fileList=self._spectraList[odir])

        elif self._piccolo is None:
            return

        if spectraName is None or spectraName == self._currentFileName:
            #trying to download the same spectrum multiple times in a row
            #messes with the chunking system
            return

        self._currentFileName = spectraName
        

        self._spectra = self._piccolo.piccolo.getSpectra(fname=spectraName, simplify = self.downloadSimple.isChecked())
        print(self._spectra)
        self._plotDownloadedSpectrum()

    def _plotDownloadedSpectrum(self,spectra = None):
        if spectra is None:
            spectra = self._spectra

        self._ableToPlot = False
        self._selectedDirection = self._spectra.directions[0]
        spectra = []
        for s in ['Light','Dark']:
            if self._spectra.haveSpectrum(s):
                spectra.append(s)
        self._selectedSpectrum = spectra[0]

        self.selectShutter.clear()
        if len(self._spectra.directions) == 2:
            self.selectShutter.addItems(["Bidirectional"])
        self.selectShutter.addItems(self._spectra.directions)

        self.selectSpectrometer.clear()
        self._spectrometers = list(set([s['SerialNumber'] for s in self._spectra]))
        if len(self._spectrometers) > 1:
            self.selectSpectrometer.addItems(["All Spectrometers"])
        self.selectSpectrometer.addItems(self._spectrometers)


        self.selectSpectrum.clear()
        self.selectSpectrum.addItems(spectra)

        self._ableToPlot = True
        self.setSpectrumAndDirection()

    def setSpectrumAndDirection(self):
        if not self._ableToPlot:
            return

        self._selectedSpectrum = self.selectSpectrum.currentText()
        self._selectedDirection = self.selectShutter.currentText()
        self._selectedSpectrometer = self.selectSpectrometer.currentText()
        if self._selectedSpectrum in ['Dark','Light'] and self._selectedDirection is not None:
            self.showSpectra()

    def showSpectra(self):
        self.spectraPlot.setTitle("{dir} {spec}".format(dir=self._selectedDirection,spec=self._selectedSpectrum))
        if self._selectedDirection == "Bidirectional":
            spectra = []
            directions = []
            for d in self._spectra.directions:
                new_spectra=self._spectra.getSpectra(d, self._selectedSpectrum)
                directions+=[d]*len(new_spectra)
                spectra+=new_spectra
        else:
            spectra = self._spectra.getSpectra(self._selectedDirection, self._selectedSpectrum)
            directions = [str(self._selectedDirection)]*len(spectra)
        
        if(self._selectedSpectrometer == "All Spectrometers"):
            spectrometers = self._spectrometers
        else:
            spectrometers = self._selectedSpectrometer

        self.spectraPlot.plotSpectra(spectra,directions,spectrometers)

    def connect(self,connection,data):
        ok = True
        if connection == 'http':
            self._connectionType = 'http'
            self._connectionData = data
            try:
                self._piccolo = piccolo2.client.PiccoloJSONRPCClient(data)
            except:
                ok = False
                errorTitle = 'failed to connect'
                errorMsg = 'failed to connect to {}'.format(data)

        elif connection == 'xbee':
            self._connectionType = 'xbee'
            self._connectionData = data
            try:
                self._piccolo = piccolo2.client.PiccoloXbeeClient(address=data)
            except:
                ok = False
                errorTitle = 'failed to connect'
                errorMsg = 'failed to connect to {}'.format(data)  

        elif connection == 'xbee auto':
            self._connectionType = 'xbee auto'
            self._connectionData = data
            try:
                self._piccolo = piccolo2.client.PiccoloXbeeClient(baudrate=data)
            except:
                ok = False
                errorTitle = 'failed to connect'
                errorMsg = 'failed to connect to {}'.format(data)  
        else:
            ok = False
            errorTitle ='not implemented'
            errorMsg = 'connection type {} is not implemented yet'.format(connection)
        if not ok:
            error=QtGui.QMessageBox.critical(self,errorTitle,errorMsg,QtGui.QMessageBox.Ok)
            return

        # get the current piccolo time
        ptime = self._piccolo.piccolo.getClock()
        self.piccoloTime.setText(ptime.split('.')[0])


        #get the piccolo's attached peripherals
        self._peripherals = self._piccolo.piccolo.getAttachedAuxInstruments()

        # get the data dir
        self.updateMounted()

        # hook up integration times
        self._times.piccoloConnect(self._piccolo.piccolo)

        # hook up scheduler
        self._scheduledJobs.piccoloConnect(self._piccolo)

    def updateMounted(self):
        info = self._piccolo.piccolo.info()
        self.dataDir.setText(info['datadir'])
        if info['datadir'] == 'not mounted':
            self.mountDataButton.setText("mount data")
        else:
            self.mountDataButton.setText("unmount data")
        
    def connectDialog(self):
        dialog = ConnectDialog()
        dialog.setConnection(self._connectionType,self._connectionData)
        data = dialog.getData()
        if data !=None:
            self.connect(data[0],data[1])

    def scheduledJobsDialog(self):
        self._scheduledJobsDialog.show()

    def addSchedule(self):
        start,interval,end = ScheduleDialog.getSchedule()
        print start,interval,end
        if start!=None:
            self.startRecording(start=start,end=end,interval=interval)

    def savePlot(self):
        fname = QtGui.QFileDialog.getSaveFileName(self,'Save Spectra Plot',
                                                  "spectra.png",
                                                  "Images (*.png *.jpg *.pdf)")
        self.spectraPlot.save(str(fname))

def main(connection):
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    if connection:
        form.connect(connection[0],connection[1])
    app.exec_()
