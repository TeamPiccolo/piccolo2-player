
__all__ = ['SpectraPlot']

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SpectraPlot(FigureCanvas):
    def __init__(self,parent=None):
        super(SpectraPlot,self).__init__(Figure())
        self.setParent(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self._theplot = None

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
        for s in spectra:
            self.theplot.plot(s.waveLengths,s.pixels,label=s['SerialNumber'])
            date=s['Datetime']
        if len(spectra)>0:
            t = self.theplot.get_title()
            self.theplot.set_title('{}\n{}'.format(t,date))
            self.theplot.legend()
        self.draw()

    def save(self,fname):
        self.figure.savefig(fname)

if __name__ == ['__main__']:
    pass
