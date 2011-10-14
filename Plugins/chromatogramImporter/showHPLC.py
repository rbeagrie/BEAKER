from Tkinter import *
import Tkinter as Tk
import peaker, tkFileDialog

class MainWindow():
    def __init__(self):
        self.root = Tk.Tk()
        self.q = True
        while self.q:
            f = str(tkFileDialog.askopenfilename())
            if not f == '':
                test = peaker.chromatography_importer(f,start='Raw Data:')
                test.assign_data('Time(min)','Value(mAU)')
                test.plot_peaks(raw=True)
            else:
                self.destroy()
        
        self.root.mainloop()

m = MainWindow()
