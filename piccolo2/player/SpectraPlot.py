
__all__ = ['SpectraPlot']

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import time
from PyQt4 import QtCore

class SpectraPlot(FigureCanvas):
    def __init__(self,parent=None):
        super(SpectraPlot,self).__init__(Figure())
        self.setParent(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self._theplot = None

        self._lines = None
        self._spectra = None
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)
        # check every 5 second
        self.timer.start(5000)

    @property
    def theplot(self):
        if self._theplot == None:
            self._theplot = self.figure.add_subplot(111)
        return self._theplot

    def setTitle(self,title):
        self.theplot.clear()
        self.theplot.set_title(title)

    def plotSpectra(self,spectra):
        date=None

        self._spectra = spectra
        self._lines = []
        
        for s in self._spectra:
            if not s.complete:
                done = False
            l, = self.theplot.plot(s.waveLengths,s.pixels,label=s['SerialNumber'])
            self._lines.append(l)
            date=s['Datetime']
        if len(spectra)>0:
            t = self.theplot.get_title()
            self.theplot.set_title('{}\n{}'.format(t,date))
            self.theplot.legend()
        self.draw()

    def updatePlot(self):

        if self._spectra is None:
            return
        
        done = True
        for i in range(len(self._spectra)):
            if not self._spectra[i].complete:
                done = False
            self._lines[i].set_ydata(self._spectra[i].pixels)
        self.theplot.relim()
        self.theplot.autoscale_view()
        self.draw()

        if done:
            self._lines = None
            self._spectra = None

    def save(self,fname):
        self.figure.savefig(fname)

if __name__ == ['__main__']:
    pass
