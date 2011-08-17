from Tkinter import *
import ttk, tkFileDialog, tkMessageBox, beaker, os, logging, cPickle, threading, time



#Create the main window


'''
mainframe = ttk.Frame(root, padding="1 1 1 1")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
mainframe.rowconfigure(1, weight=0)
'''

class statusHandler(logging.Handler):
    def __init__(self,main):
        level=logging.INFO
        logging.Handler.__init__(self,level)
        self.main = main

    def emit(self, record):
        self.main.statusPanel.statusText.set(record.message)

class MainWindow():
    def __init__(self):
        self.root = Tk()
        self.root.geometry('1000x650')
        self.root.title('BEAKER: Easy Analysis of the Kinetics of Enzymatic Reactions')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.option_add('*tearOff', FALSE)

        self.project = False
        self.saveFile = False

        self.menu = MainMenu(self.root,self)

        self.displayPanel = DisplayPanel(self.root,self)

        self.statusPanel = StatusPanel(self.root,self)

        self.root.mainloop()

    def createProject(self,name,directory):

        logging.basicConfig(filename='C:\\Users\\Rob\\Documents\\Beaker\\debug.log',level=logging.INFO)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        handler = statusHandler(self)
        handler.setLevel(logging.INFO)

        self.logger.addHandler(handler)
        
        self.project = beaker.session(name,directory=directory)

        

class MainMenu(Menu):
    def __init__(self,parent,main):
        #Set up the main menu
        Menu.__init__(self,parent)
        self.parent = parent
        self.main = main
        self.parent['menu'] = self

        self.menus = {}

        #Add top menu items
        self.menus['File'] = Menu(self)
        self.menus['Model'] = Menu(self)
        self.menus['Data'] = Menu(self)
        self.menus['Solve'] = Menu(self)
        self.menus['Help'] = Menu(self)
        self.add_cascade(menu=self.menus['File'], label='File')
        self.add_cascade(menu=self.menus['Model'], label='Model')
        self.add_cascade(menu=self.menus['Data'], label='Data')
        self.add_cascade(menu=self.menus['Solve'], label='Solutions')
        self.add_cascade(menu=self.menus['Help'], label='Help')

        #Add 'File' sub menu items
        self.menus['File'].add_command(label='New Project', command=self.newProject)
        self.menus['File'].add_command(label='Edit Project', command=self.editProject)
        self.menus['File'].add_separator()
        self.menus['File'].add_command(label='Open Project', command=self.openProject)
        self.menus['File'].add_command(label='Save Project', command=self.saveProject)
        self.menus['File'].add_command(label='Save Project As', command=self.saveProjectAs)
        self.menus['File'].add_command(label='Close Project', command=self.closeProject)
        self.menus['File'].add_separator()
        self.menus['File'].add_command(label='Exit Beaker', command=self.exitBeaker)

        #Add 'Model' sub menu items
        self.menus['Model'].add_command(label='Pick Model', command=self.pickModel)
        self.menus['Model'].add_command(label='Create New Model', command=self.newModel)
        self.menus['Model'].add_command(label='View/Edit Model', command=self.editModel)
        self.menus['Model'].add_command(label='Import Model', command=self.importModel)
        self.menus['Model'].add_separator()
        self.menus['Model'].add_command(label='Run Simulation', command=self.runModel)

        #Add 'Data' sub menu items
        self.menus['Data'].add_command(label='Import Rate Data', command=self.importRates)
        self.menus['Data'].add_command(label='Import Concentration Data', command=self.importConcentrations)
        self.menus['Data'].add_separator()
        self.menus['Data'].add_command(label='View/Edit Data', command=self.editData)

        #Add 'Solutions' sub menu items
        self.menus['Solve'].add_command(label='Quick Solution', command=self.quickSolve)
        self.menus['Solve'].add_command(label='Advanced Solution', command=self.advancedSolve)
        self.menus['Solve'].add_separator()
        self.menus['Solve'].add_command(label='Saved Solutions', command=self.viewSolutions)

        #Add 'Help' sub menu items
        self.menus['Help'].add_command(label='Logging', command=self.viewLog)
        self.menus['Help'].add_command(label='About', command=self.aboutBeaker)
        
        self.initiateStates()
        self.refreshState()

    #Actions for menu entries

    def newProject(self,*Args):
        NewProject(self.parent,self.main)

    def editProject(self,*Args):
        pass

    def openProject(self,*Args):
        project_file = str(tkFileDialog.askopenfilename())
        self.main.project = beaker.session(project_file=project_file)
        self.main.saveFile = project_file
        self.refreshState()

    def saveProject(self,*Args):
        if not self.main.saveFile:
            self.main.saveFile = str(tkFileDialog.asksaveasfilename())
        self.main.project.save(self.main.saveFile)

    def saveProjectAs(self,*Args):
        save_file = str(tkFileDialog.asksaveasfilename())
        self.main.saveFile = save_file
        self.saveProject()

    def closeProject(self,*Args):
        self.project = False
        self.refreshState()

    def exitBeaker(self,*Args):
        self.main.destroy()

    def pickModel(self,*Args):
        pass

    def newModel(self,*Args):
        pass

    def editModel(self,*Args):
        pass

    def importModel(self,*Args):
        model_file = tkFileDialog.askopenfilename()
        self.main.project.initiate_model(str(model_file))
        self.main.project.initiate_data()
        self.refreshState()

    def runModel(self,*Args):
        pass

    def importRates(self,*Args):
        data_file = tkFileDialog.askopenfilename()
        self.main.project.data.rate_importer.import_text(str(data_file))
        AssignRates(self.parent,self.main,self.main.project.data.rate_importer.dictionary)

    def importConcentrations(self,*Args):
        data_file = tkFileDialog.askopenfilename()
        self.main.project.data.concentration_importer.import_text(str(data_file))
        AssignConcentrations(self.parent,self.main,self.main.project.data.concentration_importer.dictionary)

    def editData(self,*Args):
        pass

    def quickSolve(self,*Args):
        solveWindow = QuickSolve(self.parent,self.main)
        solveWindow.solve()
        

    def advancedSolve(self,*Args):
        pass

    def viewSolutions(self,*Args):
        pass

    def viewLog(self,*Args):
        pass

    def aboutBeaker(self,*Args):
        pass

    def initiateStates(self):
        self.states = {
            'no_project' : {
                'File' : {
                    'New Project'                   : True,
                    'Edit Project'                  : False,
                    'Open Project'                  : True,
                    'Save Project'                  : False,
                    'Save Project As'               : False,
                    'Close Project'                 : False,
                    'Exit Beaker'                   : True },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }},
            
            'no_model' : {
                
                'File' : {
                    'New Project'                   : True,
                    'Edit Project'                  : True,
                    'Open Project'                  : True,
                    'Save Project'                  : True,
                    'Save Project As'               : True,
                    'Close Project'                 : True,
                    'Exit Beaker'                   : True },
                'Model' : {
                    'Pick Model'                    : True,
                    'Create New Model'              : True,
                    'View/Edit Model'               : False,
                    'Import Model'                  : True,
                    'Run Simulation'                : False },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }},
            
            'no_data' : {
                
                'File' : {
                    'New Project'                   : True,
                    'Edit Project'                  : True,
                    'Open Project'                  : True,
                    'Save Project'                  : True,
                    'Save Project As'               : True,
                    'Close Project'                 : True,
                    'Exit Beaker'                   : True },
                'Model' : {
                    'Pick Model'                    : True,
                    'Create New Model'              : True,
                    'View/Edit Model'               : True,
                    'Import Model'                  : True,
                    'Run Simulation'                : True },
                'Data' : {
                    'Import Rate Data'              : True,
                    'Import Concentration Data'     : True,
                    'View/Edit Data'                : False },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }},
            
            'complete' : {
                
                'File' : {
                    'New Project'                   : True,
                    'Edit Project'                  : True,
                    'Open Project'                  : True,
                    'Save Project'                  : True,
                    'Save Project As'               : True,
                    'Close Project'                 : True,
                    'Exit Beaker'                   : True },
                'Model' : {
                    'Pick Model'                    : True,
                    'Create New Model'              : True,
                    'View/Edit Model'               : True,
                    'Import Model'                  : True,
                    'Run Simulation'                : True },
                'Data' : {
                    'Import Rate Data'              : True,
                    'Import Concentration Data'     : True,
                    'View/Edit Data'                : True },
                'Solve' : {
                    'Quick Solution'                : True,
                    'Advanced Solution'             : True,
                    'Saved Solutions'               : True },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }}}

        self.menuDict = {
            'File' : 0,
            'Model' : 1,
            'Data' : 2,
            'Solve' : 3,
            'Help' : 4}

    def refreshState(self):
        if not self.main.project:
            self.setState('no_project')
        elif not self.main.project.model:
            self.setState('no_model')
        elif not self.main.project.data.experiments:
            self.setState('no_data')
        else:
            self.setState('complete')

    def setState(self,state):

        for menu_name in self.menus:
            if menu_name in self.states[state]:
                self.entryconfigure(self.menuDict[menu_name],state='normal')
                for option_name in self.states[state][menu_name]:
                    if self.states[state][menu_name][option_name]:
                        self.menus[menu_name].entryconfigure(option_name,state='normal')
                    else:
                        self.menus[menu_name].entryconfigure(option_name,state='disabled')
            else:
                self.entryconfigure(self.menuDict[menu_name],state=DISABLED)

class DisplayPanel(Frame):
    def __init__(self,parent,main):
        
        Frame.__init__(self,parent)
        self.grid(column=0,row=0, sticky=(N, W, E, S))

class StatusPanel(Frame):
    def __init__(self,parent,main):

        Frame.__init__(self,parent)

        
        self.grid(column=0,row=1, sticky=(W, E))

        self['borderwidth'] = 1
        self['relief'] = 'raised'
        self["height"] = 20

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.statusText = StringVar()

        self.statusText.set('Welcome to BEAKER!')

        self.statusLabel = ttk.Label(self, textvariable=self.statusText)
        self.statusLabel.grid(column=0,row=0,sticky=(W,E))

class NewProject(Toplevel):
    def __init__(self,parent,main):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent

        self.title('Create a new Beaker project')

        self.mu = u"\N{Greek Small Letter Mu}"

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.nameLabel = ttk.Label(self.frame, text="Project Name:")
        self.nameLabel.grid(column=0,row=0)

        self.projectName = StringVar()

        self.projectName.set('T')

        self.nameEntry = ttk.Entry(self.frame, textvariable=self.projectName)
        self.nameEntry.grid(column=1,row=0,sticky=(W,E))

        self.unitLabel = ttk.Label(self.frame, text="Units:")
        self.unitLabel.grid(column=0,row=1)

        self.unitChoice = StringVar()
        self.units = StringVar()

        self.unitCombo = ttk.Combobox(self.frame, textvariable=self.unitChoice,state='readonly')
        
        self.unitCombo['values'] = ['Pico (pM, pL etc...)',
                                    'Nano (nM, nl etc...)',
                                    'Micro (%sM, %sl etc...)'%(self.mu,self.mu),
                                    'Milli (mM, ml etc...)',
                                    'No Prefix (M, l etc)']

        self.translateUnits = { hash(self.unitCombo['values'][0]):'pico',
                                hash(self.unitCombo['values'][1]):'nano',
                                hash(self.unitCombo['values'][2]):'micro',
                                hash(self.unitCombo['values'][3]):'milli',
                                hash(self.unitCombo['values'][4]):'none' }
        
        self.unitChoice.set(self.unitCombo['values'][2])
        self.units.set('milli')
        self.unitCombo.current(3)                   

        self.unitCombo.bind('<<ComboboxSelected>>', self.changeUnits)
        
        self.unitCombo.grid(column=1,row=1,sticky=(W,E))

        self.dirLabel = ttk.Label(self.frame, text="Project Directory:")
        self.dirLabel.grid(column=0,row=2)

        self.projectDir = StringVar()

        self.projectDir.set(os.path.expanduser('~\\Documents\\Beaker'))

        self.dirEntry = ttk.Entry(self.frame, textvariable=self.projectDir)
        self.dirEntry.grid(column=1,row=2,sticky=(W,E))

        self.dirButton = ttk.Button(self.frame, text='...', command=self.dirDialog, width=4)
        self.dirButton.grid(column=2,row=2,sticky=(W))

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=3)

        self.saveButton = ttk.Button(self.frame, text='Save', command=self.save, default='active')
        self.saveButton.grid(column=1,row=3,columnspan=2)

        self.nameEntry.focus()
        self.bind('<Return>', self.save)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    def dirDialog(self):
        self.projectDir.set(tkFileDialog.askdirectory(parent=self))

    def changeUnits(self,*Args):
        self.units.set(self.translateUnits[hash(self.unitChoice.get())])

    def cancel(self):
        self.destroy()

    def save(self,*Args):
        if self.validate():
            self.main.units = self.units.get()
            self.main.createProject(self.projectName.get(),self.projectDir.get())
            self.main.menu.refreshState()
            self.destroy()

    def validate(self):
        if self.projectName.get() == '':
            tkMessageBox.showinfo(message='Please enter a project name.')
            return False
        else:
            return True
        
class AssignConcentrations(Toplevel):
    def __init__(self,parent,main,data):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.data = data

        self.title('Assign data to model parameters')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Assign data columns:")
        self.Label.grid(column=0,row=0,columnspan=2)

        self.dataFrame = ttk.Frame(self.frame)
        self.dataFrame.grid(column=1, row=1,sticky=(N,W,E,S))

        assignOptions = list(self.main.project.model.reactants)

        assignOptions.insert(0,'Time')

        self.comboOptions = SmartCombo(assignOptions)

        colHeadings = self.data.keys()

        self.dataColumns = []

        for colHeading in colHeadings:
            self.dataColumns.append(ConcentrationColumn(self,self.main,self.data,colHeading,self.comboOptions))

        for i,col in enumerate(self.dataColumns):
            col.frame.grid(column=i,row=0,sticky=(N,W,E,S))                               

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=2)

        self.contButton = ttk.Button(self.frame, text='Continue', command=self.assignData, default='active')
        self.contButton.grid(column=2,row=2)

        self.bind('<Return>', self.assignData)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    def cancel(self):
        self.destroy()

    def assignData(self,*Args):
        assignment = {}
        for col in self.dataColumns:
            data_key,model_key = col.assign()
            if model_key:
                assignment[model_key] = data_key
        self.main.project.data.concentration_importer.assign(assignment)
        unset = self.main.project.data.concentration_importer.get_unset_reactants()
        if len(unset) == 0:
            self.main.project.data.concentration_importer.save()
            self.main.menu.refreshState()
            self.cancel()
        else:
            AssignStartingConcentrations(self.parent,self.main,unset,self.main.project.data.concentration_importer)
            self.cancel()

    def refreshCombos(self):
        for col in self.dataColumns:
            col.refresh()

class ConcentrationColumn():
    def __init__(self,parent,main,data,heading,options):
        #ttk.Frame.__init__(parent)
        self.frame = ttk.Frame(parent.dataFrame)
        self.parent = parent
        self.main = main
        self.data = data
        self.heading = heading
        self.options = options

        self.assignment = StringVar()

        self.assignmentCombo = ttk.Combobox(self.frame, textvariable=self.assignment,state='readonly')
        
        self.assignmentCombo['values'] = self.options.get(self.heading)
        
        self.assignmentCombo.current(0)                   
        
        self.assignmentCombo.grid(column=0,row=0,sticky=(W,E))

        s = ttk.Style()
        s.configure('Data.TFrame',background='#FFFFFF')
        s.configure('Data.TLabel',background='#FFFFFF')
        
        
        self.dataFrame = ttk.Frame(self.frame,relief='solid',style='Data.TFrame',padding='3 3 3 3')
        self.dataFrame.grid(column=0,row=1,sticky=(W,E))
        self.dataFrame.columnconfigure(0, weight=1)
        self.dataFrame.rowconfigure(0, weight=1)
        self.dataFrame.rowconfigure(1, weight=1)

        self.HeadingLabel = ttk.Label(self.dataFrame, text=heading,style='Data.TLabel')
        self.HeadingLabel.grid(column=0,row=0)

        dataRows = self.data[heading]

        dataText = ''

        if len(dataRows) > 4:
            dataRows = dataRows[:4]
            for i in range(len(dataRows)):
                dataText += '%.4f\n' % dataRows[i]
            dataText += '...'
        else:
            for i in range(len(dataRows)):
                dataText += '%.4f\n' % dataRows[i]
            extra = len(dataRows) - 4
            for i in range(extra):
                dataText += '\n'
            dataText += ''
        
        self.dataBox = ttk.Label(self.dataFrame, text=dataText,style='Data.TLabel')
        self.dataBox.grid(column=0,row=1)

        self.frame.grid_configure(padx=5)

        self.assignmentCombo.bind('<<ComboboxSelected>>', self.changeSelection)

    def assign(self):
        assignment = str(self.assignment.get())
        if assignment == 'Time': assignment = 'time'
        if assignment != '':
            return self.heading,assignment
        else:
            return self.heading,False

    def changeSelection(self,*Args):
        self.options.select(self.heading,self.assignmentCombo.get())
        self.parent.refreshCombos()

    def refresh(self):
        self.assignmentCombo['values'] = self.options.get(self.heading)

class AssignStartingConcentrations(Toplevel):
    def __init__(self,parent,main,unset,importer):
        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.unset = unset
        self.importer = importer

        self.title('Assign starting concentrations')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.unset_entries = []
        self.unset_labels = []
        self.unset_variables = {}

        for reactant in unset:
            label = ttk.Label(self.frame, text=reactant)
            self.unset_labels.append(label)

            var = StringVar()
            var.set('0.0')
            self.unset_variables[reactant] = var
            
            entry = ttk.Entry(self.frame,textvariable=self.unset_variables[reactant])
            self.unset_entries.append(entry)

        for i,entry in enumerate(self.unset_entries):
            self.unset_labels[i].grid(column=0,row=i)
            entry.grid(column=1,row=i)

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=len(self.unset_variables))

        self.saveButton = ttk.Button(self.frame, text='Save', command=self.save, default='active')
        self.saveButton.grid(column=1,row=len(self.unset_variables))

        self.unset_entries[0].focus()
        self.bind('<Return>', self.save)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    def cancel(self):
        self.destroy()

    def save(self):

        assignment = {}

        for reactant in self.unset:
            assignment[reactant] = float(self.unset_variables[reactant].get())

        self.importer.set_starting_concentrations(assignment)

        self.importer.save()
        self.main.menu.refreshState()

        self.destroy()

class AssignRates(Toplevel):
    def __init__(self,parent,main,data):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.data = data

        self.title('Assign data to model parameters')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Assign data columns:")
        self.Label.grid(column=0,row=0,columnspan=2)

        self.dataFrame = ttk.Frame(self.frame)
        self.dataFrame.grid(column=1, row=1,sticky=(N,W,E,S))

        reactants = list(self.main.project.model.reactants)

        assignOptions = []
        
        for reactant in reactants:
            assignOptions.append(reactant + ' Rate')
            assignOptions.append(reactant + ' Concentration')

        self.comboOptions = SmartCombo(assignOptions)

        colHeadings = self.data.keys()

        self.dataColumns = []

        for colHeading in colHeadings:
            self.dataColumns.append(RateColumn(self,self.main,self.data,colHeading,self.comboOptions))

        for i,col in enumerate(self.dataColumns):
            col.frame.grid(column=i,row=0,sticky=(N,W,E,S))                               

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=2)

        self.contButton = ttk.Button(self.frame, text='Continue', command=self.assignData, default='active')
        self.contButton.grid(column=2,row=2)

        self.bind('<Return>', self.assignData)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    def cancel(self):
        self.destroy()

    def assignData(self,*Args):
        assignment = {'Rate':{},'Concentration':{}}
        for col in self.dataColumns:
            data_key,model_key,key_type = col.assign()
            if model_key:
                assignment[key_type][model_key] = data_key
        self.main.project.data.rate_importer.assign_concentrations(assignment['Concentration'])
        self.main.project.data.rate_importer.assign_rates(assignment['Rate'])
        unset = self.main.project.data.rate_importer.get_unset_reactants()
        if len(unset) == 0:
            self.main.project.data.rate_importer.save()
            self.main.menu.refreshState()
            self.cancel()
        else:
            AssignStartingConcentrations(self.parent,self.main,unset,self.main.project.data.rate_importer)
            self.cancel()

    def refreshCombos(self):
        for col in self.dataColumns:
            col.refresh()

class RateColumn():
    def __init__(self,parent,main,data,heading,options):
        #ttk.Frame.__init__(parent)
        self.frame = ttk.Frame(parent.dataFrame)
        self.parent = parent
        self.main = main
        self.data = data
        self.heading = heading
        self.options = options

        self.assignment = StringVar()

        self.assignmentCombo = ttk.Combobox(self.frame, textvariable=self.assignment,state='readonly')

        self.assignmentCombo['values'] = self.options.get(self.heading)
        
        self.assignmentCombo.current(0)                   
        
        self.assignmentCombo.grid(column=0,row=0,sticky=(W,E))

        s = ttk.Style()
        s.configure('Data.TFrame',background='#FFFFFF')
        s.configure('Data.TLabel',background='#FFFFFF')
        
        
        self.dataFrame = ttk.Frame(self.frame,relief='solid',style='Data.TFrame',padding='3 3 3 3')
        self.dataFrame.grid(column=0,row=1,sticky=(W,E))
        self.dataFrame.columnconfigure(0, weight=1)
        self.dataFrame.rowconfigure(0, weight=1)
        self.dataFrame.rowconfigure(1, weight=1)

        self.HeadingLabel = ttk.Label(self.dataFrame, text=heading,style='Data.TLabel')
        self.HeadingLabel.grid(column=0,row=0)

        dataRows = self.data[heading]

        dataText = ''

        if len(dataRows) > 4:
            dataRows = dataRows[:4]
            for i in range(len(dataRows)):
                dataText += '%.4f\n' % dataRows[i]
            dataText += '...'
        else:
            for i in range(len(dataRows)):
                dataText += '%.4f\n' % dataRows[i]
            extra = len(dataRows) - 4
            for i in range(extra):
                dataText += '\n'
            dataText += ''
        
        self.dataBox = ttk.Label(self.dataFrame, text=dataText,style='Data.TLabel')
        self.dataBox.grid(column=0,row=1)

        self.frame.grid_configure(padx=5)

        self.assignmentCombo.bind('<<ComboboxSelected>>', self.changeSelection)

    def assign(self):
        assignments = str(self.assignment.get())

        assignments = assignments.split()

        assignment = assignments[0]
        
        if assignment != '':

            astype = assignments[1]
            return self.heading,assignment,astype
        else:
            return self.heading,False ,False

    def changeSelection(self,*Args):
        self.options.select(self.heading,self.assignmentCombo.get())
        self.parent.refreshCombos()

    def refresh(self):
        self.assignmentCombo['values'] = self.options.get(self.heading)

class SmartCombo():
    def __init__(self,values):
        self.values = values
        self.selections = {}

    def select(self,key,value):
        self.selections[key] = value

    def get(self,key):

        free_values = ['']
        taken_values = []
        for combo in self.selections:
            if not combo == key:
                taken_values.append(self.selections[combo])
        for value in self.values:
            if not value in taken_values:
                free_values.append(value)

        return free_values

class QuickSolve(Toplevel):
    def __init__(self,parent,main):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent

        self.title('Solving the model')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Solving the model with default parameters.\n\nProgress:")
        self.Label.grid(column=0,row=0)

        self.Bar = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=200, mode='determinate', maximum=200)
        self.Bar.grid(column=0,row=1)

        self.solution = False

        #self.destroy()

    def updateBar(self,*Args):
        self.Bar.step()

    def solve(self):
        
        self.s = threading.Thread(target=self.blah)
        self.s.start()
        self.main.root.after(500,self.check)

    def blah(self):
        self.solution = self.main.project.solver.solve(call=self.updateBar)

    def check(self):
        if self.s.isAlive():
            #print 'Not done yet...'
            self.main.root.after(500,self.check)
        else:
            #print 'Done!'
            SolutionWindow(self.parent,self.main,self.solution)
            self.destroy()
        
        
class SolutionWindow(Toplevel):
    def __init__(self,parent,main,solution):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.solution = solution[0]

        self.title('Solution Details')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Solution Found!")
        self.Label.grid(column=0,row=0)

        self.Label = ttk.Label(self.frame, text=self.solution[0])
        self.Label.grid(column=0,row=1)
        

m=MainWindow()
