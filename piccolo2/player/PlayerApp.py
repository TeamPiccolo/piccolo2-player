__all__ = ['main']

import piccolo_client

from PyQt4 import QtGui, QtCore
import player
import connect
from ScheduleList import *
from Schedule import ScheduleDialog

class IntegrationTimes(QtGui.QStandardItemModel):
    def __init__(self,*args,**keywords):

        QtGui.QStandardItemModel.__init__(self,*args,**keywords)

        self._shutters = None
        self._spectrometers = None
        self._piccolo = None

        self.itemChanged.connect(self.updateIntegrationTime)


    def updateIntegrationTime(self,index):
        try:
            data = float(index.text())
        except:
            index.setForeground(QtGui.QBrush(QtGui.QColor('red')))
            return
        index.setForeground(QtGui.QBrush(QtGui.QColor('black')))
        self._piccolo.setIntegrationTime(shutter=self._shutters[index.column()],
                                         spectrometer=self._spectrometers[index.row()],
                                         milliseconds=data)

    def piccoloConnect(self,piccolo):
        self._piccolo = piccolo
        self._shutters = self._piccolo.getShutterList()
        self._spectrometers = self._piccolo.getSpectrometerList()

        self.setRowCount(len(self._spectrometers))
        self.setColumnCount(len(self._shutters))

        for i in range(len(self._shutters)):
            self.setHorizontalHeaderItem(i,QtGui.QStandardItem(self._shutters[i]))
        for j in range(len(self._spectrometers)):
            self.setVerticalHeaderItem(j,QtGui.QStandardItem(self._spectrometers[j]))

        for j in range(len(self._spectrometers)):
            for i in range(len(self._shutters)):
                data = self._piccolo.getIntegrationTime(shutter=self._shutters[i],
                                                        spectrometer=self._spectrometers[j])
                self.setItem(j,i,QtGui.QStandardItem(str(data)))



class ConnectDialog(QtGui.QDialog,connect.Ui_ConnectDialog):
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

class PlayerApp(QtGui.QMainWindow, player.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PlayerApp, self).__init__(parent)
        self.setupUi(self)

        # the piccolo connection
        self._piccolo = None
        self._connectionType = 'http'
        self._connectionData = 'http://localhost:8080'

        # the integration times
        self._times = IntegrationTimes()
        self.integrationTimeView.setModel(self._times)

        # connect recording buttons
        self.startRecordingButton.clicked.connect(self.startRecording)
        self.stopRecordingButton.clicked.connect(self.stopRecording)
        self.pauseRecordingButton.clicked.connect(self.pauseRecording)

        # connect spectra load boxes
        self._spectraList = None
        self._updateSpectraFile = True
        self._spectra = None
        self._selectedDirection = None
        self.selectSpectrum.addItems(['Light','Dark'])
        self._selectedSpectrum = self.selectSpectrum.currentText()
        self.refreshSpectraListButton.clicked.connect(self.getSpectraList)
        self.selectFile.currentIndexChanged.connect(self.downloadSpectra)
        self.selectShutter.currentIndexChanged.connect(self.setDirection)
        self.selectSpectrum.currentIndexChanged.connect(self.setSpectrum)

        # hook up scheduler
        self._scheduledJobs = PiccoloSchedule()
        self._scheduledJobsDialog = ScheduleListDialog(scheduledJobs = self._scheduledJobs)

        # hook up menu
        self.action_Connect.triggered.connect(self.connectDialog)
        self.action_Quit.triggered.connect(QtGui.qApp.quit)
        self.action_Add_Schedule.triggered.connect(self.addSchedule)
        self.actionList_Schedules.triggered.connect(self.scheduledJobsDialog)

        # periodically check status
        self.statusLabel = QtGui.QLabel()
        self.statusbar.addWidget(self.statusLabel)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.status)
        # check every second
        self.timer.start(1000)

    def status(self):
        state = 'red'
        status = 'disconnected'
        if self._piccolo != None:
            status = 'connected'
            state = 'green'
            (busy,paused) = self._piccolo.piccolo.status()
            if busy:
                status = 'busy'
                state = 'orange'
            if paused:
                status += ', paused'
                self.pauseRecordingButton.setText("Unpause")
            else:
                self.pauseRecordingButton.setText("Pause")

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
        if start not in [None, False]:
            kwds['at_time'] = start
        if interval!=None:
            kwds['interval'] = interval
        if end!=None:
            kwds['end_time'] = end
        self._piccolo.piccolo.record(**kwds)

    def pauseRecording(self):
        self._piccolo.piccolo.pause()

    def stopRecording(self):
        self._piccolo.piccolo.abort()

    def getSpectraList(self):
        if self._piccolo!=None:
            self._spectraList = self._piccolo.piccolo.getSpectraList()

            # check if we have some items in the list already
            # if so clear existing list but ignore change
            if self.selectFile.count() > 0:
                self._updateSpectraFile = False
                curSelection = self.selectFile.currentText()
                self.selectFile.clear()

            self.selectFile.addItems(self._spectraList)

            if not self._updateSpectraFile:
                idx = self.selectFile.findText(curSelection)
                self.selectFile.setCurrentIndex(idx)
                self._updateSpectraFile = True

    def downloadSpectra(self,idx):
        if self._spectraList!=None and self._updateSpectraFile:
             data = self._piccolo.piccolo.getSpectra(fname=self._spectraList[idx])
             self._spectra = piccolo_client.PiccoloSpectraList(data=data)
             # set directions
             self.selectShutter.clear()
             self.selectShutter.addItems(self._spectra.directions)

    def setDirection(self,idx):
        self._selectedDirection = self.selectShutter.currentText()
        self.showSpectra()

    def setSpectrum(self,idx):
        self._selectedSpectrum = self.selectSpectrum.currentText()
        self.showSpectra()

    def showSpectra(self):
        print self._selectedDirection, self._selectedSpectrum
        spectra = self._spectra.getSpectra(self._selectedDirection, self._selectedSpectrum)
        print spectra

    def connect(self,connection,data):
        ok = True
        if connection == 'http':
            self._connectionType = 'http'
            self._connectionData = data
            try:
                self._piccolo = piccolo_client.PiccoloJSONRPCClient(data)
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

        # hook up integration times
        self._times.piccoloConnect(self._piccolo.piccolo)

        # hook up scheduler
        self._scheduledJobs.piccoloConnect(self._piccolo)


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

def main(connection):
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    form.connect(connection[0],connection[1])
    app.exec_()
