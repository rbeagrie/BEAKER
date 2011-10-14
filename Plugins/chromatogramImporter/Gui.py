import peaker, ttk, tkFileDialog
from Tkinter import *
from beaker.Gui.MainWindow import ScrolledCanvas,AssignConcentrations

def Start(root,project):
    print 'Started!'
    Times(tkFileDialog.askopenfilenames(),root,project)

class Main(Toplevel):
    def __init__(self,root,project):
        print names
        Toplevel.__init__(self,root)
        #ttk.Label(text='hello').grid(0,0)

class Times(Toplevel):
    def __init__(self,files,root,project):
        self.root = root
        files = str(files).split('} {')
        files[0] = files[0][1:]
        files[-1] = files[-1][:-1]
        print files
        self.files = files
        self.root = root
        self.project = project
        Toplevel.__init__(self,root)
        ttk.Label(self,text='At what time were the chromatograms collected?').grid(
            column=0,
            row=0,
            columnspan=2)
        ttk.Label(self,text='Filename:').grid(column=0,row=1)
        ttk.Label(self,text='Time (s):').grid(column=1,row=1)

        row = 2
        self.entries = []
        self.variables = []
        for i,f in enumerate(files):
            ttk.Label(self,text=f).grid(column=0,row=row)
            self.variables.append(StringVar(value=0))
            self.entries.append(ttk.Entry(self,textvariable=self.variables[i]))
            self.entries[i].grid(column=1,row=row)
            row += 1

        ttk.Label(self,text='Data starts after:').grid(column=0,row=row,columnspan=2)
        row += 1
        self.datastart = StringVar(value='Raw Data:')
        ttk.Entry(self,textvariable=self.datastart).grid(column=0,row=row,columnspan=2)
        row += 1

        ttk.Label(self,text='Time Header:').grid(column=0,row=row)
        ttk.Label(self,text='Intensity Header:').grid(column=1,row=row)
        row += 1
        self.t_head = StringVar(value='Time(min)')
        self.i_head = StringVar(value='Value(mAU)')
        ttk.Entry(self,textvariable=self.t_head).grid(column=0,row=row)
        ttk.Entry(self,textvariable=self.i_head).grid(column=1,row=row)
        row += 1

        ttk.Button(self,text='Continue',command=self.save).grid(column=1,row=row)

    def save(self):
        times = []
        for i,v in enumerate(self.variables):
            times.append(float(self.variables[i].get()))
        self.importer = peaker.series_importer(self.files)
        self.importer.set_times(times)
        print self.importer.times
        self.importer.import_files(str(self.datastart.get()))
        self.importer.assign_data(str(self.t_head.get()),str(self.i_head.get()))
        self.importer.data[0].set_parameters(95,92,4)
        self.importer.data[1].set_parameters(95,76,3)
        self.importer.data[2].set_parameters(95,82,4)
        self.importer.data[3].set_parameters(95,82,3)
        self.importer.data[4].set_parameters(95,80,3)
        self.set_params(0)

    def set_params(self,i):
        if i == len(self.importer.data):
            PeakAssign(self.root,self.importer)
            self.destroy()
        else:
            self.i = i
            self.c = CheckParams(self.root,self.files[i],self.importer.data[i])
            self.after(500,self.next_params)

    def next_params(self):
        try:
            self.c.lift()
        except:
            return
        if self.c.done:
            self.set_params(self.i + 1)
        else:
            self.after(500, self.next_params)
        
class CheckParams(Toplevel):
    def __init__(self,root,filename,importer):
        self.importer = importer
        Toplevel.__init__(self,root)
        ttk.Label(self,text=filename).grid(column=0,row=0)
        
        ttk.Label(self,text='Threshold:').grid(column=0,row=1)
        self.threshold = StringVar(value=self.importer.threshold_value)
        ttk.Entry(self,textvariable=self.threshold).grid(column=1,row=1)
        
        ttk.Label(self,text='Baseline:').grid(column=0,row=2)
        self.baseline = StringVar(value=self.importer.baseline_value)
        ttk.Entry(self,textvariable=self.baseline).grid(column=1,row=2)
        
        ttk.Label(self,text='Minima:').grid(column=0,row=3)
        self.minima = StringVar(value=self.importer.minima_value)
        ttk.Entry(self,textvariable=self.minima).grid(column=1,row=3)
        
        ttk.Button(self,text='Check parameters',command=self.check).grid(column=0,row=4)
        
        ttk.Button(self,text='Continue',command=self.done).grid(column=1,row=4)
        self.done = False

    def check(self):
        self.importer.set_parameters(float(self.baseline.get()),float(self.threshold.get()),float(self.minima.get()))
        self.importer.plot_peaks()

    def done(self):
        self.done = True
        self.after(500,self.destroy)

class PeakAssign(Toplevel):
    def __init__(self,root,importer):
        self.importer = importer
        self.root = root
        Toplevel.__init__(self)
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        self.importer.find_species()
        self.species_rows = False
        self.update()

    def update(self):
        if self.species_rows:
            for s in self.species_rows:
                s.update()
        self.importer.fill_species()
        self.data = self.importer.get_data()
        self.species_rows = []
        self.sc = ScrolledCanvas(self)
        self.dataframe = self.sc.frame
        self.sc.grid(column=0,row=0,sticky='NWES',columnspan=3)
        column=0
        ttk.Label(self.dataframe,text='Species Name').grid(column=column,row=0)
        column += 1
        for i,p in enumerate(self.data['time']):
            ttk.Button(self.dataframe,text=p,command=self.importer.data[i].plot_peaks).grid(column=column,row=0)
            column += 1
        ttk.Label(self.dataframe,text='Selected').grid(column=column,row=0)
        row=1
        for i,s in enumerate(self.importer.species):
            self.species_rows.append(SpeciesRow(self.dataframe,s,self.data))
            self.species_rows[i].grid(row)
            row += 1
        ttk.Button(self,text='Merge Selected Peaks',command=self.mergeSpecies).grid(column=0,row=1)
        ttk.Button(self,text='Ignore Selected Peaks',command=self.ignoreSpecies).grid(column=1,row=1)
        ttk.Button(self,text='Continue',command=self.done).grid(column=2,row=1)
        self.sc.update()

    def getSelected(self):
        j = []
        for i,s in enumerate(self.species_rows):
            if s.selected.get():
                j.append(self.importer.species[i])
        return j

    def ignoreSpecies(self):
        species = self.getSelected()
        for s in species:
            self.importer.species.remove(s)
        self.update()

    def mergeSpecies(self):
        species = self.getSelected()
        points = []
        for s in species:
            if s.point:
                points.append(s.point)
            else:
                points.append(s.start)
                points.append(s.end)
            self.importer.species.remove(s)
        self.importer.species.append(peaker.species((min(points),max(points)),2))
        self.update()

    def done(self):
        for s in self.species_rows:
            s.update()
        data = self.importer.get_data()
        self.root.project.data.concentration_importer.dictionary = data
        AssignConcentrations(self.root,self.root,data)
            

class SpeciesRow():
    def __init__(self,parent,species,data):
        self.name = StringVar(value=species.name)
        self.species = species
        self.columns=[]
        self.columns.append(ttk.Entry(parent,textvariable=self.name))
        for q in data[species.name]:
            self.columns.append(ttk.Label(parent,text='%.3f'%q))
        self.selected = BooleanVar(value=False)
        self.columns.append(ttk.Checkbutton(parent,variable=self.selected))

    def update(self):
        self.species.name = str(self.name.get())

    def grid(self,row):
        for i,c in enumerate(self.columns):
            c.grid(column=i,row=row)
