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

from PyQt4 import QtGui, QtCore
import player_ui
import connect_ui
from ScheduleList import *
from Schedule import ScheduleDialog
from QuietTime import QuietTimeDialog
from RunList import RunListDialog
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
        try:
            data = float(index.text())
        except:
            index.setForeground(QtGui.QBrush(QtGui.QColor('red')))
            return
        index.setForeground(QtGui.QBrush(QtGui.QColor('black')))
        if self._updatePiccolo:
            shutter = self._shutters[index.column()]
            spectrometer = self._spectrometers[index.row()]
            if shutter == 'min':
                self._piccolo.setMinIntegrationTime(spectrometer=spectrometer,milliseconds=data)
            elif shutter == 'max':
                self._piccolo.setMaxIntegrationTime(spectrometer=spectrometer,milliseconds=data)
            else:
                self._piccolo.setIntegrationTime(shutter=shutter,
                                                 spectrometer=spectrometer,
                                                 milliseconds=data)


    def updateIntegrationTimeDisplay(self,spectrometer,shutter):
        j = self._spectrometers.index(spectrometer)
        i = self._shutters.index(shutter)
        if shutter == 'min':
            data = self._piccolo.getMinIntegrationTime(spectrometer=spectrometer)
        elif shutter == 'max':
            data = self._piccolo.getMaxIntegrationTime(spectrometer=spectrometer)
        else:
            data = self._piccolo.getIntegrationTime(shutter=shutter,
                                                    spectrometer=spectrometer)
        self._updatePiccolo = False
        self.setItem(j,i,QtGui.QStandardItem(str(data)))
        self._updatePiccolo = True
            
    def piccoloConnect(self,piccolo):
        self._piccolo = piccolo
        self._shutters = ['min']+self._piccolo.getShutterList()+['max']
        self._spectrometers = self._piccolo.getSpectrometerList()

        self.setRowCount(len(self._spectrometers))
        self.setColumnCount(len(self._shutters))

        for i in range(len(self._shutters)):
            self.setHorizontalHeaderItem(i,QtGui.QStandardItem(self._shutters[i]))
        for j in range(len(self._spectrometers)):
            self.setVerticalHeaderItem(j,QtGui.QStandardItem(self._spectrometers[j]))

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
        else:
            raise RuntimeError, 'unkown connection type',connection

    @property
    def getConnectionMethod(self):
        if self.connectHTTP.isChecked():
            return 'http'
        elif self.connectXBee.isChecked():
            return 'xbee'
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

        self.selectRunButton.clicked.connect(self.setRun)
        
        # connect spectra load boxes
        self._spectraList = {}
        self._updateSpectraFile = True
        self._spectra = None
        self._selectedDirection = None
        self._selectedSpectrum = None
        self.selectSpectrumButton.clicked.connect(self.downloadSpectra)
        self.selectShutter.currentIndexChanged.connect(self.setSpectrumAndDirection)
        self.selectSpectrum.currentIndexChanged.connect(self.setSpectrumAndDirection)

        # hook up scheduler
        self._scheduledJobs = PiccoloSchedule()
        self._scheduledJobsDialog = ScheduleListDialog(scheduledJobs = self._scheduledJobs)

        # hook up menu
        self.action_Connect.triggered.connect(self.connectDialog)
        self.actionSave_Plot.triggered.connect(self.savePlot)
        self.action_Quit.triggered.connect(QtGui.qApp.quit)
        self.action_Add_Schedule.triggered.connect(self.addSchedule)
        self.actionList_Schedules.triggered.connect(self.scheduledJobsDialog)
        self.actionQuietTime.triggered.connect(self.quietTimeDialog)

        # hook up autointegration checkbox
        self.checkAutoIntegrate.stateChanged.connect(self.handleAutointegrate)
        self.autoIntegrateRepeat.setEnabled(False)
        
        # periodically check status
        self.statusLabel = QtGui.QLabel()
        self.statusbar.addWidget(self.statusLabel)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.status)
        # check every second
        self.timer.start(1000)

    def syncTime(self):
        now = datetime.datetime.now()
        self._piccolo.piccolo.setClock(clock=now.strftime("%Y-%m-%dT%H:%M:%S"))

    def status(self):
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
                elif msg[0] == 'ITmin':
                    spectrometer = msg[1]
                    self._times.updateIntegrationTimeDisplay(spectrometer,'min')
                elif msg[0] == 'ITmax':
                    spectrometer = msg[1]
                    self._times.updateIntegrationTimeDisplay(spectrometer,'max')
                elif msg[0] == 'warning':
                    QtGui.QMessageBox.warning(self,'Warning',msg[1],QtGui.QMessageBox.Ok)
                
        self.statusLabel.setText(status)
        self.statusLabel.setStyleSheet(' QLabel {color: %s}'%state)
        self.repaint()

    def startRecording(self,start=None,end=None,interval=None):
        n = self.repeatMeasurements.value()
        if n==0:
            n='Inf'
        kwds ={}
        kwds['delay'] = self.delayMeasurements.value()
        kwds['nCycles'] = n
        kwds['outDir'] = str(self.outputDir.text())
        if self.checkAutoIntegrate.checkState()==2:
            kwds['auto'] = self.autoIntegrateRepeat.value()
        else:
            kwds['auto'] = -1
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

    def handleAutointegrate(self):
        if self.checkAutoIntegrate.checkState() == 2:
            self.autoIntegrateRepeat.setEnabled(True)
        else:
            self.autoIntegrateRepeat.setEnabled(False)
        
    def pauseRecording(self):
        self._piccolo.piccolo.pause()

    def setRun(self):
        runList = self._piccolo.piccolo.getRunList()
        r = RunListDialog.getRun(runList=runList)
        if r is not None:
            self.outputDir.setText(r)
        
    def stopRecording(self):
        self._piccolo.piccolo.abort()

    def downloadSpectra(self):
        odir = str(self.outputDir.text())
        if self._piccolo!=None:
            if odir not in self._spectraList:
                self._spectraList[odir] = []
            self._spectraList[odir] += self._piccolo.piccolo.getSpectraList(outDir=odir,haveNFiles=len( self._spectraList[odir]))
        else:
            return
        spectraName = SpectraListDialog.getSpectrum(fileList=self._spectraList[odir])
        self._spectra = self._piccolo.piccolo.getSpectra(fname=spectraName)
        self._selectedDirection = self._spectra.directions[0]
        spectra = []
        for s in ['Light','Dark']:
            if self._spectra.haveSpectrum(s):
                spectra.append(s)
        self._selectedSpectrum = spectra[0]

        self.selectShutter.clear()
        self.selectShutter.addItems(self._spectra.directions)
        self.selectSpectrum.clear()
        self.selectSpectrum.addItems(spectra)

    def setSpectrumAndDirection(self):
        self._selectedSpectrum = self.selectSpectrum.currentText()
        self._selectedDirection = self.selectShutter.currentText()
        if self._selectedSpectrum in ['Dark','Light'] and self._selectedDirection is not None:
            self.showSpectra()

    def showSpectra(self):
        self.spectraPlot.setTitle("{dir} {spec}".format(dir=self._selectedDirection,spec=self._selectedSpectrum))
        spectra = self._spectra.getSpectra(self._selectedDirection, self._selectedSpectrum)
        self.spectraPlot.plotSpectra(spectra)

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
                self._piccolo = piccolo2.client.PiccoloXbeeClient(data)
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

        # get the data dir
        self.updateMounted()

        # hook up integration times
        self._times.piccoloConnect(self._piccolo.piccolo)

        # hook up scheduler
        self._scheduledJobs.piccoloConnect(self._piccolo)

        self.outputDir.setText(self._piccolo.piccolo.getCurrentRun())
        
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
        if start!=None:
            self.startRecording(start=start,end=end,interval=interval)

    def quietTimeDialog(self):
        # get current settings
        se = self._piccolo.getQuietTime()
        se = QuietTimeDialog.getQuietTime(start_time=se[0],end_time=se[1])
        if se is not None:
            self._piccolo.setQuietTime(start_time=se[0],end_time=se[1])
        
    def savePlot(self):
        fname = QtGui.QFileDialog.getSaveFileName(self,'Save Spectra Plot',
                                                  "spectra.png",
                                                  "Images (*.png *.jpg *.pdf)")
        self.spectraPlot.save(str(fname))

def main(connection):
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    form.connect(connection[0],connection[1])
    app.exec_()
