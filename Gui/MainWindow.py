import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi, array
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkinter import *
from fonts import Fonts
import Tkinter as Tk
import beaker.Backend.beaker as beaker
import ttk, tkFileDialog, tkMessageBox, os, logging, cPickle, threading, time, traceback, subprocess

import beaker.refs as refs, beaker.version as version

def tryFloat(f):

    """Try to convert f to a float

    Any time we need the user to input a float, call this method to make sure their entry is valid."""
    
    try:
        return float(f)
    except:
        
        #If we couldn't convert to a float, raise a beaker exception
        raise beaker.BeakerException('%s is not a valid number.' % f)



class AutoScrollbar(Scrollbar):
    """Create a scrollbar that hides itself if it's not needed.

    only works if you use the grid geometry manager."""
    
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

class BkToplevel(Toplevel):
    """Create a toplevel window with the Beaker icon"""
    
    def __init__(self,parent):
        
        #Inherit from Toplevel
        Toplevel.__init__(self,parent)
        
        #Set the icon
        self.wm_iconbitmap(refs.iconpath)

class ScrolledCanvas(Frame):
    """Create a frame with an auto-scrollbar attached.

    Items to be added to the frame should be added to %OBJECT%.frame not to the parent %OBJECT% itself.

    Once all the items have been added to the inner frame, call update() to set the size of the canvas."""
    
    def __init__(self,parent):

        # Inherit from Frame
        Frame.__init__(self,parent)
        
        # Create two scrollbars for x and y
        vscrollbar = AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar = AutoScrollbar(self, orient=HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=E+W)

        # Create a canvas to attach the scrollbar to
        self.canvas = Canvas(self,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set)
        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)

        # Get rid of ugly canvas border
        self.canvas['highlightcolor'] = self.canvas['highlightbackground']

        # Attach the scrollbars to the canvas
        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)

        # Make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create an inner frame to hold the contents
        self.frame = Frame(self.canvas)
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(1, weight=1)

    def update(self,w=False,h=False):

        """Call this once all objects have been added to the inner frame

        set w or h to True to stop either the width or height of the canvas
        expanding to fill all the available space in the parent frame."""

        self.canvas.create_window(0, 0, anchor=NW, window=self.frame)

        self.frame.update_idletasks()

        if w:

            self.canvas['width'] = 170

            x,y,w,h = self.canvas.bbox("all")

            w += 10

            self.canvas['width'] = w

        if h:

            self.canvas['height'] = 50

            x,y,w,h = self.canvas.bbox("all")

            h += 10

            self.canvas['height'] = h

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

class statusHandler(logging.Handler):
    def __init__(self,main):
        level=logging.INFO
        logging.Handler.__init__(self,level)
        self.main = main

    def emit(self, record):
        self.main.statusPanel.statusText.set(record.msg)

class Blah():
    def __init__(self):
        self.bold = tkFont.Font(font='TkDefaultFont')
        self.bold['weight'] = 'bold'

class MainWindow(Tk.Tk):
    def __init__(self):
        Tk.Tk.__init__(self)
        self.geometry('1000x650')
        self.title('BEAKER: Easy Analysis of the Kinetics of Enzymatic Reactions')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.option_add('*tearOff', FALSE)
        self.report_callback_exception = self.report_callback_exception
        self.wm_iconbitmap(refs.iconpath)

        self.fonts = Fonts()

        self.project = False
        self.saveFile = False

        self.mu = u"\N{Greek Small Letter Mu}"

        self.units = {'pico':{
                                'rate' : 'pM / s',
                                'concentration' : 'pM'},
                      'nano':{
                                'rate' : 'nM / s',
                                'concentration' : 'pM'},
                      'micro':{
                                'rate' : '%sM / s' % self.mu,
                                'concentration' : '%sM' % self.mu},
                      'milli':{
                                'rate' : 'mM / s',
                                'concentration' : 'mM'},
                      'none':{
                                'rate' : 'M / s',
                                'concentration' : 'M'}}

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s :: %(name)s : %(levelname)s ::\t %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')

        self.status_handler = statusHandler(self)
        self.status_handler.setLevel(logging.INFO)
        self.status_handler.setFormatter(self.formatter)

        self.logger.addHandler(self.status_handler)

        self.newFileHandler(refs.userhomedir)

        self.menu = MainMenu(self,self)

        self.displayPanel = DisplayPanel(self,self)

        self.statusPanel = StatusPanel(self,self)

        self.refreshState()

        self.mainloop()

    def concUnit(self):
        return self.units[self.project.units]['concentration']

    def rateUnit(self):
        return self.units[self.project.units]['rate']

    def newFileHandler(self,directory):

        if len(self.logger.handlers) == 1:
            level = logging.WARNING
        else:
            level = self.logger.handlers[1].level
            if not type(self.logger.handlers[1].stream) is NoneType:
                self.logger.handlers[1].stream.close()
            self.logger.removeHandler(self.logger.handlers[1])

        newdebugpath = os.path.join(directory,'debug.log')
        file_handler = logging.FileHandler(newdebugpath,delay=True)
        file_handler.setLevel(level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def createProject(self,name,directory,units):

        self.newFileHandler(directory)
        self.project = beaker.session(name,directory=directory,units=units)

    def refreshState(self):
        if not self.project:
            self.setState('no_project')
        elif not self.project.model.definition:
            self.setState('no_model')
        elif not self.project.data.experiments:
            self.setState('no_data')
        elif len(self.project.solutions) == 0:
            self.setState('no_solutions')
        else:
            self.setState('complete')

    def setState(self,state):
        self.menu.setState(state)
        self.displayPanel.setState(state)

    def report_callback_exception(self, *args):
        t,e,x = args
        if t is type(beaker.BeakerException()):
            logging.warning(e)
            tkMessageBox.showwarning('Warning',e)
            for child in self.winfo_children():
                if isinstance(child,Toplevel):
                    child.lift()
        else:
            err = traceback.format_tb(x)
            err_tex = 'Traceback:\n\n'
            for l in err:
                err_tex += l
            logging.error(e)
            tkMessageBox.showerror('Exception','Error: %s' % e,detail=err_tex)
            for child in self.winfo_children():
                if isinstance(child,Toplevel):
                    child.lift()

    def setLogLevel(self,level):
        self.logger.handlers[1].setLevel(level)

    def destroy(self):
        
        if not type(self.logger.handlers[1].stream) is NoneType:
            self.logger.handlers[1].stream.close()
        Tk.Tk.destroy(self)        

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
        self.ModelChoices = Menu(self)
        self.menus['Model'].add_cascade(menu=self.ModelChoices, label='Pick Model')
        self.menus['Model'].add_command(label='Create New Model', command=self.newModel)
        self.menus['Model'].add_command(label='Import Model', command=self.importModel)
        self.menus['Model'].add_separator()
        self.menus['Model'].add_command(label='View/Edit Model', command=self.editModel)
        self.menus['Model'].add_command(label='Run Simulation', command=self.runModel)

        #Add 'Data' sub menu items
        self.removeExperiment = Menu(self)
        self.menus['Data'].add_command(label='Import Rate Data', command=self.importRates)
        self.menus['Data'].add_command(label='Import Concentration Data', command=self.importConcentrations)
        self.menus['Data'].add_separator()
        self.menus['Data'].add_cascade(menu=self.removeExperiment, label='Remove Experiment')

        #Add 'Solutions' sub menu items
        self.viewSolution = Menu(self)
        self.menus['Solve'].add_command(label='Quick Solution', command=self.quickSolve)
        self.menus['Solve'].add_command(label='Advanced Solution', command=self.advancedSolve)
        self.menus['Solve'].add_separator()
        self.menus['Solve'].add_cascade(menu=self.viewSolution, label='View Solution')

        #Add 'Help' sub menu items
        self.LoggingChoices = Menu(self)
        self.menus['Help'].add_command(label='Help', command=self.showHelp)
        self.menus['Help'].add_cascade(menu=self.LoggingChoices, label='Logging')
        self.menus['Help'].add_command(label='About', command=self.aboutBeaker)

        self.radio = StringVar()
        self.LoggingChoices.add_radiobutton(label='Debug', variable=self.radio, value='debug',command=self.getLoggingCommand(logging.DEBUG))
        self.LoggingChoices.add_radiobutton(label='Info', variable=self.radio, value='info',command=self.getLoggingCommand(logging.INFO))
        self.LoggingChoices.add_radiobutton(label='Warning', variable=self.radio, value='warning',command=self.getLoggingCommand(logging.WARNING))
        self.LoggingChoices.add_radiobutton(label='Error', variable=self.radio, value='error',command=self.getLoggingCommand(logging.ERROR))
        self.LoggingChoices.add_radiobutton(label='Critical', variable=self.radio, value='critical',command=self.getLoggingCommand(logging.CRITICAL))

        self.radio.set('warning')

        self.initialiseModels()

        for model in self.models:
            n = model
            self.ModelChoices.add_command(label=model, command=self.getModelCommand(model))
        
        self.initiateStates()

    #Actions for menu entries

    def newProject(self,*Args):
        NewProject(self.parent,self.main)

    def editProject(self,*Args):
        EditProject(self.parent,self.main)

    def openProject(self,*Args):
        project_file = str(tkFileDialog.askopenfilename(initialdir=refs.userhomedir))
        if not project_file == '':
            self.main.project = beaker.session(project_file=project_file)
            self.main.saveFile = project_file
            self.main.newFileHandler(self.main.project.directory)
            self.main.displayPanel.createPanes()
            self.main.refreshState()

    def saveProject(self,*Args):
        if not self.main.saveFile:
            newfile = os.path.join(self.main.project.directory,'%s.bkr'%self.main.project.name)
            saveFile = str(tkFileDialog.asksaveasfilename(initialdir=refs.userhomedir,
                                                          defaultextension='.bkr',
                                                          initialfile=newfile))
            if saveFile == '': return
            self.main.saveFile = saveFile
        self.main.project.save(self.main.saveFile)

    def saveProjectAs(self,*Args):
        save_file = str(tkFileDialog.asksaveasfilename(initialdir=refs.userhomedir,defaultextension='.bkr'))
        if save_file == '': return
        self.main.saveFile = save_file
        self.saveProject()

    def closeProject(self,*Args):
        self.main.newFileHandler(refs.userhomedir)
        self.main.project = False
        self.main.displayPanel.removePanes()
        self.main.refreshState()

    def exitBeaker(self,*Args):
        self.main.destroy()

    def newModel(self,*Args):
        if self.ModelCheck():
            EditModel(self.parent,self.main,new=True)

    def editModel(self,*Args):
        if self.ModelCheck():
            EditModel(self.parent,self.main)

    def importModel(self,*Args):
        if self.ModelCheck():
            model_file = tkFileDialog.askopenfilename(initialdir=refs.userhomedir)
            if model_file == '': return
            self.main.project.model.import_file(str(model_file))
            self.main.refreshState()

    def ModelCheck(self):
        if self.main.project.model.definition and self.main.project.data and self.main.project.data.experiments:
            message = 'Editing your model definition will cause ALL of your data and solutions to be destroyed. Are you sure you wish to continue?'
            if tkMessageBox.askquestion(title='Overwrite old model?', message=message) == 'yes':
                return True
            else:
                return False
        else:
            return True

    def runModel(self,*Args):
        RunModel(self.parent,self.main)

    def importRates(self,*Args):
        data_file = tkFileDialog.askopenfilename(initialdir=refs.userhomedir)
        if data_file == '': return
        self.main.project.data.rate_importer.import_text(str(data_file))
        AssignRates(self.parent,self.main,self.main.project.data.rate_importer.dictionary)

    def importConcentrations(self,*Args):
        data_file = tkFileDialog.askopenfilename(initialdir=refs.userhomedir)
        if data_file == '': return
        self.main.project.data.concentration_importer.import_text(str(data_file))
        AssignConcentrations(self.parent,self.main,self.main.project.data.concentration_importer.dictionary)

    def editData(self,*Args):
        EditData(self.parent,self.main)

    def quickSolve(self,*Args):
        solveWindow = QuickSolve(self.parent,self.main)
        solveWindow.solve()

    def advancedSolve(self,*Args):
        AdvancedSolve(self.parent,self.main)

    def viewSolutions(self,*Args):
        pass

    def showHelp(self,*Args):
        filepath = refs.helppath
        if os.name == 'mac':
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            subprocess.call(('start', filepath), shell=True)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))


    def viewLog(self,*Args):
        pass

    def aboutBeaker(self,*Args):
        About(self.parent,self.main)

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
                    'Remove Experiment'             : True },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }},
            
            'no_solutions' : {
                
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
                    'Remove Experiment'             : True },
                'Solve' : {
                    'Quick Solution'                : True,
                    'Advanced Solution'             : True,
                    'View Solution'                 : False },
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
                    'Remove Experiment'             : True },
                'Solve' : {
                    'Quick Solution'                : True,
                    'Advanced Solution'             : True,
                    'View Solution'                 : True },
                'Help' : {
                    'Logging'                       : True,
                    'About'                         : True }}}

        self.menuDict = {
            'File' : 0,
            'Model' : 1,
            'Data' : 2,
            'Solve' : 3,
            'Help' : 4}

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

        self.removeExperiment.delete(0,len(self.removeExperiment.children))

        if self.main.project and self.main.project.data and self.main.project.data.experiments:

            for experiment in self.main.project.data.experiments:
                self.removeExperiment.add_command(label='Experiment %i' % experiment, command=self.getRemoveCommand(experiment))

        self.viewSolution.delete(0,len(self.viewSolution.children))

        if self.main.project and len(self.main.project.solutions) > 0:

            for i,solution in enumerate(self.main.project.solutions):
                self.viewSolution.add_command(label='Solution %i' % (i+1), command=self.getSolutionCommand(solution.solution))

    def initialiseModels(self):
        self.models = {'Second Order Reaction':[
                           '#Some second order reaction',
                           '2*A <-> C'],
                       'Competing Reactions':[
                           '#Two competing reactions',
                           '2*A + B <-> C',
                           'A + C <-> D'],
                       'Bistable Reactions': [
                           '#Bistable reaction. See Chapter 10, Book of GENESIS.',
                           'Sx + X <-> SxX',
                           'SxX <-> Px + X',
                           'Sy + Y <-> SyY',
                           'SyY <-> Py + Y ',
                           'Yi + Px <-> Yia',
                           'Yia + Px <-> Y',
                           'Xi + Py <-> Xia',
                           'Xia + Py <-> X',
                           'Px <-> Sx',
                           'Py <-> Sy'],
                       'Michaelis-Menten': [
                           '#Michaelis-Menten enzyme kinetics.',
                           'Enzyme + Substrate <-> ES-Complex',
                           'ES-Complex <-> Enzyme + Product',
                           '!kf=Kcat;kr=0']}

    def setModel(self,model):
        if self.ModelCheck():
            self.main.project.model.import_definition(self.models[model])
            self.main.refreshState()

    def getModelCommand(self,model):
        return lambda :self.setModel(model)

    def getLoggingCommand(self,level):
        return lambda :self.main.setLogLevel(level)

    def getRemoveCommand(self,experiment):
        return lambda :self.doRemoveExperiment(experiment)

    def getSolutionCommand(self,solution):
        return lambda :RunModel(self.main,self.main,solution=solution)

    def doRemoveExperiment(self,experiment):
        del self.main.project.data.experiments[experiment]
        self.main.refreshState()

class DisplayPanel(Frame):
    def __init__(self,parent,main):
        
        Frame.__init__(self,parent)
        self.main = main
        self.grid(column=0,row=0, sticky=(N, W, E, S))

        self.panes = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.initialiseStates()

    def createPanes(self):
    
        self.paneHolder = ttk.Notebook(self)
        self.panes = []
        self.panes.append(ProjectPane(self.paneHolder,self.main))
        self.panes.append(ModelPane(self.paneHolder,self.main))
        self.panes.append(DataPane(self.paneHolder,self.main))
        self.panes.append(SolutionsPane(self.paneHolder,self.main))
        self.paneHolder.add(self.panes[0], text = 'Project')
        self.paneHolder.add(self.panes[1], text = 'Model')
        self.paneHolder.add(self.panes[2], text = 'Data')
        self.paneHolder.add(self.panes[3], text = 'Solutions')
        self.paneHolder.grid(column = 0, row= 0, sticky=(N,W,E,S))

    def removePanes(self):

        self.paneHolder.destroy()
        self.panes = []

    def initialiseStates(self):
        self.states = {
            'no_project' : {
                0 : False,
                1 : False,
                2 : False,
                3 : False},
            'no_model' : {
                0 : True,
                1 : False,
                2 : False,
                3 : False},
            'no_data' : {
                0 : True,
                1 : True,
                2 : False,
                3 : False},
            'no_solutions' : {
                0 : True,
                1 : True,
                2 : True,
                3 : False},
            'complete' : {
                0 : True,
                1 : True,
                2 : True,
                3 : True}}

    def setState(self,state):

        if self.panes:
                
            for tab_id in self.states[state]:
                if self.states[state][tab_id]:
                    self.paneHolder.tab(tab_id,state='normal')
                    self.panes[tab_id].refresh()
                else:
                    self.paneHolder.tab(tab_id,state='disabled')
            
class ProjectPane(Frame):
    def __init__(self,parent,main):
        Frame.__init__(self,parent)
        self['padx'] = 10
        self['pady'] = 20

        self.main = main

    def refresh(self):
        
        for child in self.winfo_children():
            child.destroy()

        headings = []
        captions = []
        headings.append(ttk.Label(self,text = 'Project Name:',justify='left'))
        captions.append(ttk.Label(self,text = self.main.project.name,justify='left'))
        headings.append(ttk.Label(self,text = 'Project Units:',justify='left'))
        captions.append(ttk.Label(self,text = self.main.project.units,justify='left'))
        headings.append(ttk.Label(self,text = 'Project Directory:',justify='left'))
        captions.append(ttk.Label(self,text = self.main.project.directory,justify='left'))
        row = 0

        for i,h in enumerate(headings):
            h.grid(column = 0,row = row, sticky = 'we')
            h['font'] = 'BkXLargeBold'
            captions[i].grid(column = 1, row=row, sticky = 'we')
            captions[i]['font'] = 'BkXLarge'
            row += 1

        for child in self.winfo_children(): child.grid_configure(padx=5, pady=5)
        
        if not self.main.project.model.definition:
            self.project_text = 'A reaction model has not been defined.\n\n'
        else:
            self.project_text = 'Reaction model contains %i reactions, involving %i reactants.\n\n' % (len(self.main.project.model.kinpy_model.system),len(self.main.project.model.reactants))

        if self.main.project.data:
            expts = len(self.main.project.data.experiments)
            if expts == 0:
                self.project_text += 'No experimental data has been added.\n\n'
            elif expts == 1:
                self.project_text += '1 Experiment has been added.\n\n'
            else:
                self.project_text += '%i Experiments have been added.\n\n' % len(self.main.project.data.experiments)

        if len(self.main.project.solutions) > 0:
            self.project_text += '%i Solutions have been found.\n\n' % len(self.main.project.solutions)
            
        self.text_label = ttk.Label(self, text=self.project_text,font='BkXLarge')
        self.text_label.grid_configure(padx=5, pady=25)
        self.text_label.grid(column = 0,row=row,columnspan=2)



class ModelPane(ScrolledCanvas):
    def __init__(self,parent,main):
        ScrolledCanvas.__init__(self,parent)
        self.frame['padx'] = 10
        self.frame['pady'] = 20

        self.main = main
        self.model = self.main.project.model

    def refresh(self):
        for child in self.frame.winfo_children():
            child.destroy()
        self.heading = ttk.Label(self.frame,font='BkXLarge', text='Reaction model contains %i reactions, involving %i reactants.\n' % (len(self.model.kinpy_model.system),len(self.model.reactants)))
        self.heading.grid(column = 0, row = 0,columnspan=3)
        freactions = []
        fparams = []
        rparams = []
        rreactions = []
        t=False
        for i,line in enumerate(self.model.definition):
            if t==True:
                if line[0] == '!':
                    line = line.split(';')
                    line[0] = line[0].split('=')
                    line[1] = line[1].split('=')
                    fparams.append(line[0][1])
                    rparams.append(line[1][1])
                    t=False
                    continue
                else:
                    fparams.append('Kf%i' % (len(fparams)+1))
                    rparams.append('Kr%i' % (len(rparams)+1))
                    t=False
            if not (line == '' or line[0] == '#' or line[0] == '!'):
                line = line.split('<->')
                freactions.append(line[0])
                rreactions.append(line[1])
                t=True
        if t==True:
            if line[0] == '!':
                line = line.split(';')
                line[0] = line[0].split('=')
                line[1] = line[1].split('=')
                fparams.append(line[0][1])
                rparams.append(line[1][1])
            else:
                fparams.append('Kf%i' % (len(fparams)+1))
                rparams.append('Kr%i' % (len(rparams)+1))
        row = 1            
        for i,line in enumerate(freactions):
            ttk.Label(self.frame,font='BkXLargeBold',text='\nReaction %i:' % (i+1)).grid(column=0,row=row)
            row += 1
            ttk.Label(self.frame,font='BkXLarge', text=fparams[i]).grid(column=1,row=row)
            row += 1
            ttk.Label(self.frame,font='BkXLarge', text=freactions[i]).grid(column=0,row=row)
            EqmArrow(self.frame,60,20).grid(column=1,row=row)
            ttk.Label(self.frame,font='BkXLarge', text=rreactions[i]).grid(column=2,row=row)
            row += 1
            ttk.Label(self.frame,font='BkXLarge', text=rparams[i]).grid(column=1,row=row)
            row += 1

        self.update()



class DataPane(Frame):
    
    def __init__(self,parent,main):
        Frame.__init__(self,parent)
        self['padx'] = 10
        self['pady'] = 20
        self.columnconfigure(5,weight=1)

        self.main = main
        self.model = self.main.project.model

        self.main = main
        self.labels = []
    
    def refresh(self):
        
        for child in self.winfo_children():
            child.destroy()
            
        self.experiments = self.main.project.data.experiments

        self.dataframe = ttk.Frame(self, padding='15 0 0 0')
        self.dataframe.grid(column=2,row=2, sticky=(N,W,E,S))
        
        self.experiment_names = []
        for e in self.main.project.data.experiments:
            self.experiment_names.append('Experiment ' + str(e))

        ttk.Label(self,text='Experiments:',font='BkLargeBold').grid(column=0,row=0,sticky='NW')
        
        self.experiments = StringVar(value=tuple(self.experiment_names))
        self.selector = Listbox(self)
        self.selector.bind('<<ListboxSelect>>', self.change)
        self.selector['listvariable'] = self.experiments
        self.selector.grid(column=0,row=1,rowspan=10,sticky='NS')
        self.selector.selection_set(0)

        s = AutoScrollbar(self, orient=VERTICAL, command=self.selector.yview)
        s.grid(column=1, row=1, rowspan=10, sticky=(N,S))
        self.selector['yscrollcommand'] = s.set
        
        self.change()

    def change(self,*Args):

        self.dataframe.destroy()
        
        e = self.selector.curselection()[0]
        e_name = self.experiment_names[int(e)]
        e_name = e_name.split(' ')
        e_id = int(e_name[1])

        experiment = self.main.project.data.experiments[e_id]

        self.rawdata = []
        self.ratedata = []
        self.headings = []

        for l in self.labels:
            l.destroy()

        self.labels = []

        self.labels.append(ttk.Label(self,text='Starting Concentrations:',font='BkLargeBold', padding='15 0 0 10'))
        self.labels[len(self.labels)-1].grid(column=2,row=0,columnspan=2,sticky='NW')
        row=1
        for reactant in experiment.data:
            conc = experiment.data[reactant].starting_concentration
            self.labels.append(ttk.Label(self,text=reactant,font='BkBold', padding='15 5 0 0'))
            self.labels[len(self.labels)-1].grid(column=2,row=row,sticky='NW')
            self.labels.append(ttk.Label(self,text='= %.4f %s'% (conc,self.main.concUnit()), padding='15 5 0 0'))
            self.labels[len(self.labels)-1].grid(column=3,row=row,sticky='NW')
            row += 1

            if isinstance(experiment.data[reactant],beaker.time_series):
                self.rawdata.append(experiment.data[reactant].concentrations)
                self.headings.append(reactant)
            elif isinstance(experiment.data[reactant],beaker.rate):
                self.ratedata.append(experiment.data[reactant].rate)
                self.headings.append(reactant)

        if len(self.rawdata) > 0:

            self.labels.append(ttk.Label(self,text='Concentration Data:',font='BkLargeBold', padding='15 15 0 0'))
            self.labels[len(self.labels)-1].grid(column=2,row=row,columnspan=2,sticky='NW')
            row += 1

            self.dataframe = ttk.Frame(self, padding='15 15 0 0')
            self.dataframe.grid(column=2,row=row, sticky=(N,W,E,S),columnspan=4)
            self.dataframe.columnconfigure(0,weight=1)
            self.dataframe.rowconfigure(0,weight=1)
            self.rowconfigure(row,weight=1)
            row += 1

            columns = tuple(self.headings)

            self.datacolumns = ttk.Treeview(self.dataframe,columns=columns)
            for column in columns:
                self.datacolumns.heading(column, text='%s (%s)' % (column, self.main.concUnit()))
            self.datacolumns.heading('#0',text='Time (s)')
            self.datacolumns.grid(column=0,row=0, sticky=(N,W,E,S))

            self.rawdata = array(self.rawdata).transpose()
            
            for i in range(len(self.rawdata)):
                self.datacolumns.insert('','end',text=experiment.times[i],values=tuple(self.rawdata[i]))
            self.selector.focus()

            s = ttk.Scrollbar(self.dataframe, orient=VERTICAL, command=self.datacolumns.yview)
            s.grid(column=1, row=0, sticky=(N,S))
            self.datacolumns['yscrollcommand'] = s.set

        else:
            row = 0
            self.labels.append(ttk.Label(self,text='Rates of Change:',font='BkLargeBold', padding='35 0 0 10'))
            self.labels[len(self.labels)-1].grid(column=4,row=row,columnspan=2,sticky='NW')
            row += 1
            for i in range(len(self.headings)):
                self.labels.append(ttk.Label(self,text=self.headings[i],font='BkBold', padding='35 5 0 0'))
                self.labels[len(self.labels)-1].grid(column=4,row=row,sticky='NW')
                self.labels.append(ttk.Label(self,text='%.4f %s' % (self.ratedata[i],self.main.rateUnit()), padding='15 5 0 0'))
                self.labels[len(self.labels)-1].grid(column=5,row=row,sticky='NW')
                row += 1
            self.selector.focus()
        
class SolutionsPane(Frame):
    def __init__(self,parent,main):
        Frame.__init__(self,parent)

        self.main = main
        self.labels = []
        self.sol_pane = False
        self.disp = False
        self.displayLabels = False
        self.displayLines = False
        self.displayEntries = False

    def refresh(self):
        
        
        for child in self.winfo_children():
            child.destroy()
        
        self.solutions = self.main.project.solutions

        self.solution_names = []
        for s in range(1,len(self.solutions)+1):
            self.solution_names.append('Solution ' + str(s))

        ttk.Label(self,text='Solutions:',font='BkXLargeBold',padding='15 10 0 0').grid(column=0,row=0,sticky='NW')

        ttk.Label(self,text='Display:',font='BkXLargeBold',padding='15 10 20 0').grid(column=5,row=0,columnspan=3,sticky='NW')

        self.solutions = StringVar(value=tuple(self.solution_names))
        self.selector = Listbox(self)
        self.selector.grid_configure(pady=10,padx=15)
        self.selector.bind('<<ListboxSelect>>', self.change)
        self.selector['listvariable'] = self.solutions
        self.selector.grid(column=0,row=1,rowspan=10,sticky='N')
        self.selector.selection_set(0)

        

        
        self.experiment_names = []
        for e in self.main.project.data.experiments:
            self.experiment_names.append('Experiment ' + str(e))
        
        self.experimentchoice = StringVar()
        self.eselector = ttk.Combobox(self,textvariable=self.experimentchoice)
        self.eselector.grid_configure(pady=10)
        self.eselector.bind('<<ComboboxSelected>>', self.change)
        self.eselector['values'] = self.experiment_names
        self.eselector.grid(column=4,row=0,sticky='N')
        self.eselector.current(0)
        self.experimentchoice.set(self.experiment_names[0])
        
        self.change()

    def change(self,*Args):

        if len(self.selector.curselection())>0:
            s = self.selector.curselection()[0]
            s_name = self.solution_names[int(s)]
            s_name = s_name.split(' ')
            self.s_id = int(s_name[1])-1
        e_id = str(self.experimentchoice.get())
        e_id = e_id.split(' ')
        e_id = int(e_id[1])

        solution = self.main.project.solutions[self.s_id]

        row = 0

        for l in self.labels:
            l.destroy()

        self.labels = []

        self.labels.append(ttk.Label(self,text = 'Solution %i:' % (self.s_id+1), padding = '10 5 0 0', font = 'BkXLargeBold'))
        self.labels[len(self.labels)-1].grid(column = 1, row=row,columnspan=3)
        row += 1
        
        self.labels.append(ttk.Label(self,text = 'Parameter:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column = 1, row=row)
        
        self.labels.append(ttk.Label(self,text = 'Initial Guess:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column = 2, row=row)
        
        self.labels.append(ttk.Label(self,text = 'Final Value:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column = 3, row=row)
        row += 1

        
            
        for i,value in enumerate(solution.solution):
            self.labels.append(ttk.Label(self, text=str(list(self.main.project.model.kinpy_model.parameters)[i]), padding = '10 5 0 0', font = 'BkLarge'))
            self.labels[len(self.labels)-1].grid(column=1,row=row)
        
            self.labels.append(ttk.Label(self, text='%.5f' % solution.initial_guess[i], padding = '10 5 0 0', font = 'BkLarge'))
            self.labels[len(self.labels)-1].grid(column=2,row=row)
        
            self.labels.append(ttk.Label(self, text='%.5f' % solution.solution[i], padding = '10 5 0 0', font = 'BkLarge'))
            self.labels[len(self.labels)-1].grid(column=3,row=row)
            row += 1
            
        self.labels.append(ttk.Label(self, text='Squared Difference:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column=1,row=row,columnspan=2)
        self.labels.append(ttk.Label(self, text='%.5f' % solution.fopt, padding = '10 5 0 0', font = 'BkLarge'))
        self.labels[len(self.labels)-1].grid(column=3,row=row)
        row += 1
        self.labels.append(ttk.Label(self, text='Solver Iterations:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column=1,row=row,columnspan=2)
        self.labels.append(ttk.Label(self, text='%.5f' % solution.iter, padding = '10 5 0 0', font = 'BkLarge'))
        self.labels[len(self.labels)-1].grid(column=3,row=row)
        row += 1
        self.labels.append(ttk.Label(self, text='Function Calls:', padding = '10 5 0 0', font = 'BkLargeBold'))
        self.labels[len(self.labels)-1].grid(column=1,row=row,columnspan=2)
        self.labels.append(ttk.Label(self, text='%.5f' % solution.funcalls, padding = '10 5 0 0', font = 'BkLarge'))
        self.labels[len(self.labels)-1].grid(column=3,row=row)
        row += 1

        if self.sol_pane: self.sol_pane.destroy()
            
        
        self.sol_pane = ttk.Frame(self,padding = '20 0 0 20')
        self.sol_pane.grid(column=4,row=1,rowspan=row+2,sticky='NWES')
        self.rowconfigure(row+1,weight=1)
        self.columnconfigure(4,weight=1)

        self.draw_solution(self.s_id,e_id)
        

    def draw_solution(self,solution,experiment):

        self.solution = solution
        self.experiment = experiment

        self.f = Figure(figsize=(5,4), dpi=100)
        self.a = self.f.add_subplot(111)

        # a tk.DrawingArea
        canvas = FigureCanvasTkAgg(self.f, master=self.sol_pane)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg( canvas, self.sol_pane )
        toolbar.update()
        canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        self.a.clear()

        expt = self.main.project.data.experiments[experiment]
        self.rl = []

        if self.disp:
            for s in self.disp:
                del s

        if self.displayLabels:
            for s in self.displayLabels:
                s.destroy()

        if self.displayLines:
            for s in self.displayLines:
                s.destroy()

        if self.displayEntries:
            for s in self.displayEntries:
                s.destroy()
        
        
        self.disp = []
        self.displayLabels = []
        self.displayLines = []
        self.displayEntries = []

        self.rates = False

        
        self.displayColours = ['#1F78B4',
                               '#33A02C',
                               '#E31A1C',
                               '#FF7F00',
                               '#6A3D9A',
                               '#A6CEE3',
                               '#B2DF8A',
                               '#FB9A99',
                               '#FDBF6F',
                               '#CAB2D6']
        i = 0
        row = 2
        colour = 0
        for x in list(self.main.project.model.reactants):
            if not isinstance(expt.data[x],beaker.initial_concentration):
                self.rl.append(x)
                
                self.disp.append(BooleanVar())
                if i < 5:
                    self.disp[i].set(True)
                else:
                    self.disp[i].set(False)
                    
                self.displayLabels.append(ttk.Label(self, text=x,padding='5 5 0 0'))
                self.displayEntries.append(ttk.Checkbutton(self,variable=self.disp[i],command=self.update))
                self.displayLines.append(Canvas(self,width =20, height=20))
                if(self.disp[i].get()):
                    self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colour], width=2)
                    colour +=1
                self.displayLabels[i].grid(column=5,row=row)
                self.displayEntries[i].grid_configure(pady=5)
                self.displayEntries[i].grid(column=6,row=row)
                self.displayLines[i].grid_configure(padx=5,pady=5)
                self.displayLines[i].grid(column=7,row=row)

                if isinstance(expt.data[x],beaker.rate):
                    self.rates = True

                i  += 1
                row += 1

        self.update()

    def update(self):

        if not self.rates:

            expt = self.main.project.data.experiments[self.experiment]
                    
            t = expt.times

            sol = self.main.project.solutions[self.solution].solution
            y0 = expt.starting_concentrations

            pred = self.main.project.model.run(t,y0,sol)
            self.a.clear()
            colour = 0
            for i,r in enumerate(self.rl):
                self.displayLines[i].delete(ALL)
                if self.disp[i].get():
                    self.a.plot(t,pred[r]['conc'],color=self.displayColours[colour],linewidth=2,zorder=1)
                    self.a.scatter(t,expt.data[r].concentrations,color=self.displayColours[colour],s=10,edgecolor='black',zorder=5)
                    self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colour], width=2)
                    colour += 1
            self.f.canvas.draw()

        else:

            expt = self.main.project.data.experiments[self.experiment]

            rtime = expt.data[self.rl[0]].time

            step = rtime/15.
                    
            t = arange(0.0,2*rtime,step)
            
            sol = self.main.project.solutions[self.solution].solution
            y0 = expt.starting_concentrations

            pred = self.main.project.model.run(t,y0,sol)
            self.a.clear()
            colour = 0
            for i,r in enumerate(self.rl):
                self.displayLines[i].delete(ALL)
                if self.disp[i].get():
                    rat = expt.data[r].rate
                    #t = expt.data[r].time
                    rt = t*rat
                    c = pred[r]['conc'][15] - rt[15]
                    rt = rt + c
                    self.a.plot(t,pred[r]['conc'],color=self.displayColours[colour],zorder=1,linewidth=2)
                    self.a.plot(t[11:20],rt[11:20],color='black',zorder=5)
                    self.a.scatter(t[15],rt[15],color=self.displayColours[colour],s=10,edgecolor='black',alpha=1,zorder=10)
                    self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colour], width=2)
                    colour += 1
            self.f.canvas.draw()
        
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

class NewProject(BkToplevel):
    def __init__(self,parent,main):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent

        self.title('Create a new Beaker project')
        self.resizable(True,False)

        self.columnconfigure(0, weight=1)

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=5)
        self.frame.rowconfigure(0, weight=1)

        self.nameLabel = ttk.Label(self.frame, text="Project Name:")
        self.nameLabel.grid(column=0,row=0)

        self.projectName = StringVar()

        #self.projectName.set('T')

        self.nameEntry = ttk.Entry(self.frame, textvariable=self.projectName)
        self.nameEntry.grid(column=1,row=0,sticky=(W,E))

        self.unitLabel = ttk.Label(self.frame, text="Units:")
        self.unitLabel.grid(column=0,row=1)

        self.unitChoice = StringVar()
        self.units = StringVar()

        self.unitCombo = ttk.Combobox(self.frame, textvariable=self.unitChoice,state='readonly')
        
        self.unitCombo['values'] = ['Pico (pM, pL etc...)',
                                    'Nano (nM, nl etc...)',
                                    'Micro (%sM, %sl etc...)'%(self.main.mu,self.main.mu),
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

        self.projectDir.set(refs.userhomedir)

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
            directory = os.path.join(str(self.projectDir.get()),str(self.projectName.get()))
            self.main.createProject(str(self.projectName.get()),directory,str(self.units.get()))
            self.main.displayPanel.createPanes()
            self.main.refreshState()
            self.destroy()

    def validate(self):
        if self.projectName.get() == '':
            tkMessageBox.showinfo(message='Please enter a project name.')
            return False
        else:
            return True
        
class AssignConcentrations(BkToplevel):
    def __init__(self,parent,main,data):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.data = data

        self.title('Assign data to model parameters')
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Assign data columns:")
        self.Label.grid(column=0,row=0,columnspan=2)

        self.sc = ScrolledCanvas(self.frame)
        self.sc.grid(column=0, row=1, columnspan=2,sticky=(N,W,E,S))

        self.dataFrame = self.sc.frame

        assignOptions = list(self.main.project.model.reactants)

        assignOptions.insert(0,'Time')

        self.comboOptions = SmartCombo(assignOptions)

        colHeadings = self.data.keys()

        self.dataColumns = []

        for colHeading in colHeadings:
            self.dataColumns.append(ConcentrationColumn(self.dataFrame,self.main,self.data,colHeading,self.comboOptions,self))

        for i,col in enumerate(self.dataColumns):
            col.grid(column=i+1,row=0,sticky=(N,W,E,S))

        self.dataFrame.columnconfigure(0,weight=1)
        #self.dataFrame.columnconfigure(len(self.dataColumns)+1,weight=1)

        self.sc.update(h=True)

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=2)

        self.contButton = ttk.Button(self.frame, text='Continue', command=self.assignData, default='active')
        self.contButton.grid(column=1,row=2)

        self.bind('<Return>', self.assignData)
        x,y,w,h = self.sc.canvas.bbox("all")
        
        nw = int(w) + 70
        if nw < 800:

            self.geometry('%ix300' % nw)

        else:

            self.geometry('800x300')
         

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
            self.main.refreshState()
            self.cancel()
        else:
            AssignStartingConcentrations(self.parent,self.main,unset,self.main.project.data.concentration_importer)
            self.cancel()

    def refreshCombos(self):
        for col in self.dataColumns:
            col.refresh()

class ConcentrationColumn(Frame):
    def __init__(self,parent,main,data,heading,options,comboroot):
        Frame.__init__(self,parent)
        self.parent = parent
        self.main = main
        self.data = data
        self.heading = heading
        self.options = options
        self.comboroot = comboroot

        self.assignment = StringVar()

        self.assignmentCombo = ttk.Combobox(self, textvariable=self.assignment,state='readonly')
        
        self.assignmentCombo['values'] = self.options.get(self.heading)
        
        self.assignmentCombo.current(0)                   
        
        self.assignmentCombo.grid(column=0,row=0,sticky=(W,E))

        s = ttk.Style()
        s.configure('Data.TFrame',background='#FFFFFF')
        s.configure('Data.TLabel',background='#FFFFFF')
        
        
        self.dataFrame = ttk.Frame(self,relief='solid',style='Data.TFrame',padding='3 3 3 3')
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

        self.grid_configure(padx=5)

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
        self.comboroot.refreshCombos()

    def refresh(self):
        self.assignmentCombo['values'] = self.options.get(self.heading)

class AssignStartingConcentrations(BkToplevel):
    def __init__(self,parent,main,unset,importer):
        BkToplevel.__init__(self,parent)

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
            assignment[reactant] = tryFloat(self.unset_variables[reactant].get())

        self.importer.set_starting_concentrations(assignment)

        self.importer.save()
        self.main.refreshState()

        self.destroy()

class AssignRates(BkToplevel):
    def __init__(self,parent,main,data):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.data = data

        self.title('Assign data to model parameters')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Assign data columns:")
        self.Label.grid(column=0,row=0,columnspan=2)

        self.sc = ScrolledCanvas(self.frame)
        self.sc.grid(column=0, row=1, columnspan=2,sticky=(N,W,E,S))

        self.dataFrame = self.sc.frame

        reactants = list(self.main.project.model.reactants)

        assignOptions = []
        
        for reactant in reactants:
            assignOptions.append(reactant + ' Rate')
            assignOptions.append(reactant + ' Concentration')

        self.comboOptions = SmartCombo(assignOptions)

        colHeadings = self.data.keys()

        self.dataColumns = []

        for colHeading in colHeadings:
            self.dataColumns.append(RateColumn(self.dataFrame,self.main,self.data,colHeading,self.comboOptions,self))

        for i,col in enumerate(self.dataColumns):
            col.grid(column=i,row=0,sticky=(N,W,E,S))

        self.sc.update(h=True)

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=2)

        self.contButton = ttk.Button(self.frame, text='Continue', command=self.assignData, default='active')
        self.contButton.grid(column=1,row=2)

        self.bind('<Return>', self.assignData)
        
        x,y,w,h = self.sc.canvas.bbox("all")
        
        nw = int(w) + 70
        if nw < 800:

            self.geometry('%ix300' % nw)

        else:

            self.geometry('800x300')

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
            self.main.refreshState()
            self.cancel()
        else:
            AssignStartingConcentrations(self.parent,self.main,unset,self.main.project.data.rate_importer)
            self.cancel()

    def refreshCombos(self):
        for col in self.dataColumns:
            col.refresh()

class RateColumn(Frame):
    def __init__(self,parent,main,data,heading,options,comboroot):
        Frame.__init__(self,parent)
        self.parent = parent
        self.main = main
        self.data = data
        self.heading = heading
        self.options = options
        self.comboroot = comboroot

        self.assignment = StringVar()

        self.assignmentCombo = ttk.Combobox(self, textvariable=self.assignment,state='readonly')

        self.assignmentCombo['values'] = self.options.get(self.heading)
        
        self.assignmentCombo.current(0)                   
        
        self.assignmentCombo.grid(column=0,row=0,sticky=(W,E))

        s = ttk.Style()
        s.configure('Data.TFrame',background='#FFFFFF')
        s.configure('Data.TLabel',background='#FFFFFF')
        
        
        self.dataFrame = ttk.Frame(self,relief='solid',style='Data.TFrame',padding='3 3 3 3')
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

        self.grid_configure(padx=5)

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
        self.comboroot.refreshCombos()

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

class QuickSolve(BkToplevel):
    def __init__(self,parent,main,params=False,guess=False):

        BkToplevel.__init__(self,parent)

        if params:
            xtol,ftol,maxiter,maxfun = params
            self.params = {'xtol' : xtol,
                           'ftol' : ftol,
                           'maxiter' : maxiter,
                           'maxfun' : maxfun}
            self.soltext = "Solving the model with custom parameters.\n\nProgress:"
        else:
            self.params = False
            self.soltext = "Solving the model with default parameters.\n\nProgress:"

        self.main = main
        self.parent = parent
        self.guess = guess

        self.title('Solving the model')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text=self.soltext)
        self.Label.grid(column=0,row=0)

        if self.params:
            self.Bar = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=200, mode='determinate', maximum=self.params['maxiter'])
        else:
            self.Bar = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=200, mode='determinate', maximum=200)
        self.Bar.grid(column=0,row=1)

        self.solution = False

        #self.destroy()

    def updateBar(self,*Args):
        self.Bar.step()

    def solve(self):
        
        self.s = threading.Thread(target=self.blah)
        self.s.start()
        self.main.after(500,self.check)

    def multiSolve(self):
        self.s = threading.Thread(target=self.blah)
        self.s.start()

    def blah(self):
        try:
            self.solution = self.main.project.solver.solve(call=self.updateBar,params=self.params,initial_guess=self.guess)
        except:
            raise beaker.BeakerException('Solver terminated prematurely.')
        
    def check(self):
        if self.s.isAlive():
            #print 'Not done yet...'
            self.main.after(500,self.check)
        else:
            #print 'Done!'
            if self.solution:
                SolutionWindow(self.parent,self.main,self.solution)
            self.main.refreshState()
            self.destroy()
        
        
class SolutionWindow(BkToplevel):
    def __init__(self,parent,main,solution):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.solution = solution.solution

        self.title('Solution Details')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.Label = ttk.Label(self.frame, text="Solution Found!")
        self.Label.grid(column=0,row=0,columnspan=2)

        self.paramNames = []
        self.paramValues = []

        for i,value in enumerate(self.solution):
            self.paramNames.append(ttk.Label(self.frame, text=str(list(self.main.project.model.kinpy_model.parameters)[i])+':'))
            self.paramValues.append(ttk.Label(self.frame, text='%.5f' % self.solution[i]))
        
        for i,lab in enumerate(self.paramNames):
            lab.grid(column=0,row=i+1)

        for i,val in enumerate(self.paramValues):
            val.grid(column=1,row=i+1)

        self.Button = ttk.Button(self.frame,text='OK',command=self.destroy)
        self.Button.grid(column=0,row=len(self.paramNames)+1,columnspan=2)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

class EditProject(BkToplevel):
    def __init__(self,parent,main):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent

        self.title('Edit project details')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.nameLabel = ttk.Label(self.frame, text="Project Name:")
        self.nameLabel.grid(column=0,row=0)

        self.projectName = StringVar()

        self.projectName.set(self.main.project.name)

        self.nameEntry = ttk.Entry(self.frame, textvariable=self.projectName)
        self.nameEntry.grid(column=1,row=0,sticky=(W,E))

        self.unitLabel = ttk.Label(self.frame, text="Units:")
        self.unitLabel.grid(column=0,row=1)

        self.unitChoice = StringVar()
        self.units = StringVar()     

        self.unitCombo = ttk.Combobox(self.frame, textvariable=self.unitChoice,state='readonly')  
        
        self.unitCombo['values'] = ['Pico (pM, pL etc...)',
                                    'Nano (nM, nl etc...)',
                                    'Micro (%sM, %sl etc...)'%(self.main.mu,self.main.mu),
                                    'Milli (mM, ml etc...)',
                                    'No Prefix (M, l etc)']

        self.unitChoices = { 'pico':0,
                             'nano':1,
                             'micro':2,
                             'milli':3,
                             'none':4 }

        self.translateUnits = { hash(self.unitCombo['values'][0]):'pico',
                                hash(self.unitCombo['values'][1]):'nano',
                                hash(self.unitCombo['values'][2]):'micro',
                                hash(self.unitCombo['values'][3]):'milli',
                                hash(self.unitCombo['values'][4]):'none' }
        
        self.unitCombo.current(self.unitChoices[self.main.project.units])
        self.units.set(self.main.project.units)          

        self.unitCombo.bind('<<ComboboxSelected>>', self.changeUnits)
        
        self.unitCombo.grid(column=1,row=1,sticky=(W,E))

        self.dirLabel = ttk.Label(self.frame, text="Project Directory:")
        self.dirLabel.grid(column=0,row=2)

        self.projectDir = StringVar()

        self.projectDir.set(self.main.project.directory)

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
            self.main.project.units = self.units.get()
            self.main.project.name = self.projectName.get()
            self.main.project.directory = self.projectDir.get()
            self.main.refreshState()
            self.destroy()

    def validate(self):
        if self.projectName.get() == '':
            tkMessageBox.showinfo(message='Please enter a project name.')
            return False
        else:
            return True

class RunModel(Toplevel):
    def __init__(self,parent,main,solution=False):

        Toplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.model = self.main.project.model.kinpy_model
        self.geometry('800x430')

        self.title('Simulate Reaction in Silico')

        self.frame = ttk.Frame(self, padding='20 20 20 20',relief='solid')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.panes =ttk.PanedWindow(self.frame,orient='horizontal')
        self.pands = ScrolledCanvas(self.panes)
        self.pands.grid(column=0,row=0,sticky=(N,W,E,S))
        
        self.result = ttk.Labelframe(self.panes, text='Result', width=300, height=100)
        self.display = ttk.Labelframe(self.panes, text='Display', width=150, height=100)
        self.panes.add(self.pands,weight=0)
        self.panes.add(self.result,weight=1)
        self.panes.add(self.display,weight=0)
        self.panes.grid(column=0,row=0,sticky=(N,W,E,S))

        #self.pands.canvas.columnconfigure(0,weight=1)

        self.parameters = ttk.Labelframe(self.pands.frame, text='Parameters')
        self.parameters.grid(column=0,row=0,sticky=(W,E))
        self.parameters.columnconfigure(1,weight=1)

        self.species = ttk.Labelframe(self.pands.frame, text='Species')
        self.species.grid_configure(pady=5)
        self.species.grid(column=0,row=1,sticky=(W,E))
        self.species.columnconfigure(1,weight=1)

        self.time = ttk.Labelframe(self.pands.frame, text='Time')
        self.time.grid_configure(pady=5)
        self.time.grid(column=0,row=2,sticky=(W,E))
        self.time.columnconfigure(1,weight=1)

        #self.resultframe = ttk.Frame(self.result)
        #self.resultframe.grid(column=0,row=0,sticky=(N,W,E,S))

        self.params = []
        self.parameterLabels = []
        self.parameterEntries = []

        row = 0

        for i in range(len(self.model.parameters)):
            self.params.append(StringVar())
            if not type(solution) is BooleanType:
                self.params[i].set(solution[i])
            else:
                self.params[i].set(1.)
            self.parameterLabels.append(ttk.Label(self.parameters, text=list(self.model.parameters)[i]))
            self.parameterEntries.append(ttk.Entry(self.parameters, textvariable=self.params[i]))
            self.parameterLabels[i].grid(column=0,row=row)
            self.parameterEntries[i].grid(column=1,row=row,sticky='E')
            row += 1

        for child in self.parameters.winfo_children(): child.grid_configure(padx=5, pady=5)

        self.spec = []
        self.speciesLabels = []
        self.speciesEntries = []

        row = 0

        for i in range(len(self.model.species)):
            self.spec.append(StringVar())
            self.spec[i].set(1.)
            self.speciesLabels.append(ttk.Label(self.species, text=list(self.model.species)[i]))
            self.speciesEntries.append(ttk.Entry(self.species, textvariable=self.spec[i]))
            self.speciesLabels[i].grid(column=0,row=row)
            self.speciesEntries[i].grid(column=1,row=row,sticky='E')
            row += 1

        for child in self.species.winfo_children(): child.grid_configure(padx=5, pady=5)

        self.tstart = StringVar(value=0)
        ttk.Label(self.time,text='Start:').grid(column=0,row=0)
        ttk.Entry(self.time, textvariable=self.tstart).grid(column=1,row=0,sticky='E')

        self.tend = StringVar(value=30)
        ttk.Label(self.time,text='End:').grid(column=0,row=1)
        ttk.Entry(self.time, textvariable=self.tend).grid(column=1,row=1,sticky='E')

        for child in self.time.winfo_children(): child.grid_configure(padx=5, pady=5)
        

        self.paramChange = ttk.Button(self.pands.frame,text='Update',command=self.update)
        self.paramChange.grid_configure(pady=5)
        self.paramChange.grid(column=0,row=3)

        self.pands.update(w=True)

        self.disp = []
        self.displayLabels = []
        self.displayEntries = []
        self.displayLines = []
        self.displayColours = ['#1F78B4',
                               '#33A02C',
                               '#E31A1C',
                               '#FF7F00',
                               '#6A3D9A',
                               '#A6CEE3',
                               '#B2DF8A',
                               '#FB9A99',
                               '#FDBF6F',
                               '#CAB2D6']

        row = 0
        colours = 0

        for i in range(len(self.model.species)):
            if i < 5:
                self.disp.append(BooleanVar())
                self.disp[i].set(True)
                self.displayLabels.append(ttk.Label(self.display, text=list(self.model.species)[i]))
                self.displayEntries.append(ttk.Checkbutton(self.display,variable=self.disp[i],command=self.update))
                self.displayLines.append(Canvas(self.display,width =20, height=20))
                if(self.disp[i]):
                    self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colours], width=2)
                    colours +=1
                self.displayLabels[i].grid(column=0,row=row)
                self.displayEntries[i].grid(column=1,row=row)
                self.displayLines[i].grid(column=2,row=row)
                row += 1
            else:
                self.disp.append(BooleanVar())
                self.disp[i].set(False)
                self.displayLabels.append(ttk.Label(self.display, text=list(self.model.species)[i]))
                self.displayEntries.append(ttk.Checkbutton(self.display,variable=self.disp[i],command=self.update))
                self.displayLines.append(Canvas(self.display,width =20, height=20))
                if(self.disp[i].get()):
                    self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colours], width=2)
                    colours +=1
                self.displayLabels[i].grid(column=0,row=row)
                self.displayEntries[i].grid(column=1,row=row)
                self.displayLines[i].grid(column=2,row=row)
                row += 1

        self.f = Figure(figsize=(4,3), dpi=100)
        self.a = self.f.add_subplot(111)


        # a tk.DrawingArea
        canvas = FigureCanvasTkAgg(self.f, master=self.result)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg( canvas, self.result )
        toolbar.update()
        canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        
        self.update()
        
        self.wm_iconbitmap(refs.iconpath)

    def update(self):
        tstart = tryFloat(self.tstart.get())
        tend = tryFloat(self.tend.get())
        tstep = (tend-tstart)/300.
        t = arange(tstart,tend,tstep)
        r = self.model.run(self.get_species(),t,self.get_params())
        r = r.transpose()
        s = sin(2*pi*t)
        self.a.clear()
        colour = 0
        show_lines = self.get_display()
        total_display = 0
        for i in show_lines:
            if i: total_display += 1
        for i,disp in enumerate(show_lines):

            self.displayLines[i].delete(ALL)
            if disp:
                self.a.plot(t,r[i],color=self.displayColours[colour],linewidth=2)
                self.displayLines[i].create_line(0,10,20,10,fill=self.displayColours[colour], width=2)
                colour += 1
            elif total_display == 10:
                if not disp:
                    self.displayEntries[i]['state'] = 'disabled'
            else:
                self.displayEntries[i]['state'] = 'normal'
        
        self.f.canvas.draw()

    def get_params(self):
        params = []
        for par in self.params:
            params.append(tryFloat(par.get()))
        return params

    def get_species(self):
        species = []
        for sp in self.spec:
            species.append(tryFloat(sp.get()))
        return species

    def get_display(self):
        species = []
        for sp in self.disp:
            species.append(sp.get())
        return species

class EditModel(BkToplevel):
    
    def __init__(self,parent,main,new=False):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.model = self.main.project.model
        self.geometry('700x400')

        self.title('Edit Reaction Model')

        self.frame = ttk.Frame(self, padding='20 20 20 20',relief='solid')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        model_text = ''

        if not new:

            for line in self.model.definition:
                model_text += line + '\n\n'

        self.text = Text(self.frame)
        self.text.grid(column=0,row=0,columnspan=2, sticky=(N,W,E,S))

        self.text.insert('end',model_text)

        s = ttk.Scrollbar(self.frame, orient=VERTICAL, command=self.text.yview)
        s.grid(column=2, row=0, sticky=(N,S))
        self.text['yscrollcommand'] = s.set

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=1)

        self.saveButton = ttk.Button(self.frame, text='Save', command=self.save, default='active')
        self.saveButton.grid(column=1,row=1)

    def cancel(self):
        self.destroy()

    def save(self):
        text = self.text.get(1.0,'end')
        text = text.split('\n')
        definition = []
        for line in text:
            if str(line) != '':
                definition.append(str(line))
        self.main.project.model.import_definition(definition)
        self.main.refreshState()
        self.cancel()
                                  
class AdvancedSolve(BkToplevel):
    def __init__(self,parent,main):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent

        self.title('Advanced Solution Finder')

        self.frame = ttk.Frame(self, padding='20 20 20 20')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.parameterLabel = ttk.Label(self.frame, text = 'Initial parameter values:')
        self.parameterLabel.grid(column=0,row=0,columnspan=2)

        self.paramType = StringVar(value='random')
        self.paramRandom = ttk.Radiobutton(self.frame, text = 'Random', variable=self.paramType, value = 'random', command = self.changeParamType)
        self.paramRandom.grid(column=0,row=1,columnspan=2)
        #self.paramRandom.bind('<ButtonPress-1>', self.changeParamType)
        self.paramSpecified = ttk.Radiobutton(self.frame, text = 'Specified', variable=self.paramType, value = 'specified', command = self.changeParamType)
        self.paramSpecified.grid(column=0,row=2,columnspan=2)
        #self.paramSpecified.bind('<ButtonPress-1>', self.changeParamType)

        self.param = []
        self.paramLabels = []
        self.paramEntries = []

        row = 3

        for i in range(len(self.main.project.model.kinpy_model.parameters)):
            self.param.append(StringVar(value=1.))
            self.paramLabels.append(ttk.Label(self.frame, text=list(self.main.project.model.kinpy_model.parameters)[i]))
            self.paramEntries.append(ttk.Entry(self.frame, textvariable=self.param[i]))
            self.paramLabels[i].grid(column=0,row=row)
            self.paramEntries[i].grid(column=1,row=row)
            row += 1

        self.number = StringVar(value=1)
        ttk.Label(self.frame, text='Number of solutions:').grid(column=0,row=row)
        self.numEntry = ttk.Entry(self.frame, textvariable = self.number)
        self.numEntry.grid(column=1,row=row)
        row +=1

        self.algoLabel = ttk.Label(self.frame, text="Algorithm:")
        self.algoLabel.grid(column=0,row=row)

        self.algoName = StringVar()
        self.algorithm = StringVar()

        self.algoCombo = ttk.Combobox(self.frame, textvariable=self.algoName,state='readonly')

        self.algoCombo['values'] = ['Downhill Simplex',
                                    'Simulated Annealing']

        self.translateUnits = { hash(self.algoCombo['values'][0]):'simplex',
                                hash(self.algoCombo['values'][1]):'anneal'}
        
        self.algoName.set(self.algoCombo['values'][0])
        self.algorithm.set('simplex')
        self.algoCombo.current(0)                   

        self.algoCombo.bind('<<ComboboxSelected>>', self.changeUnits)
        
        self.algoCombo.grid(column=1,row=row,sticky=(W,E))
        row += 1

        self.xtolLabel = ttk.Label(self.frame, text="xtol:")
        self.xtolLabel.grid(column=0,row=row)
        self.xtol = StringVar(value='0.0001')
        self.xtolEntry = ttk.Entry(self.frame, textvariable=self.xtol)
        self.xtolEntry.grid(column=1,row=row)
        row += 1

        self.ftolLabel = ttk.Label(self.frame, text="ftol:")
        self.ftolLabel.grid(column=0,row=row)
        self.ftol = StringVar(value='0.0001')
        self.ftolEntry = ttk.Entry(self.frame, textvariable=self.ftol)
        self.ftolEntry.grid(column=1,row=row)
        row += 1

        self.maxiterLabel = ttk.Label(self.frame, text="maxiter:")
        self.maxiterLabel.grid(column=0,row=row)
        self.maxiter = StringVar(value='None')
        self.maxiterEntry = ttk.Entry(self.frame, textvariable=self.maxiter)
        self.maxiterEntry.grid(column=1,row=row)
        row += 1

        self.maxfunLabel = ttk.Label(self.frame, text="maxfun:")
        self.maxfunLabel.grid(column=0,row=row)
        self.maxfun = StringVar(value='None')
        self.maxfunEntry = ttk.Entry(self.frame, textvariable=self.maxfun)
        self.maxfunEntry.grid(column=1,row=row)
        row += 1
        

        self.cancelButton = ttk.Button(self.frame, text='Cancel', command=self.cancel)
        self.cancelButton.grid(column=0,row=row)

        self.saveButton = ttk.Button(self.frame, text='Save', command=self.save, default='active')
        self.saveButton.grid(column=1,row=row)
        row += 1

        self.algoCombo.focus()
        self.bind('<Return>', self.save)

        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

        self.changeParamType()
        
    def changeUnits(self,*Args):
        self.algorithm.set(self.translateUnits[hash(self.algoName.get())])

    def changeParamType(self,*Args):
        if str(self.paramType.get()) == 'random':
            for entry in self.paramEntries:
                entry.state(['disabled'])
            self.numEntry.state(['!disabled'])
        else:
            for entry in self.paramEntries:
                entry.state(['!disabled'])
            self.number.set(1)
            self.numEntry.state(['disabled'])
    
    def getGuess(self):
        if str(self.paramType.get()) == 'random':
            return 'random'
        else:
            guess = []
            for param in self.param:
                guess.append(tryFloat(param.get()))
            return guess

    def save(self):
        if self.validate():
            number = int(self.number.get())
            if number == 1:
                solveWindow = QuickSolve(self.parent,self.main,params=self.params,guess=self.getGuess())
                solveWindow.solve()
                self.destroy()
            else:
                MultiSolve(self.parent,self.main,params=self.params,guess=self.getGuess(),number=number)
                self.destroy()
                    

    def validate(self):
        xtol = tryFloat(self.xtol.get())
        ftol = tryFloat(self.ftol.get())
        if str(self.maxiter.get()) == 'None':
            maxiter = None
        else:
            maxiter = int(self.maxiter.get())
        if str(self.maxfun.get()) == 'None':
            maxfun = None
        else:
            maxfun = int(self.maxfun.get())

        self.params = (xtol,ftol,maxiter,maxfun)

        return True

    def cancel(self):
        self.destroy()

class MultiSolve(BkToplevel):
    
    def __init__(self,parent,main,params,guess,number):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.params = params
        self.guess = guess
        self.number = number

        self.title('Multiple Solution Finder')

        self.labeltext = '%i of %i solutions found'

        self.label = False

        self.i = 0

        self.update()            

    def update(self):

        if self.i < self.number:

            if self.label:
                self.label.destroy()

            self.label = ttk.Label(self,text=self.labeltext % (self.i, self.number))
            self.label.grid(column=0,row=0)

            self.solveWindow = QuickSolve(self.parent,self.main,params=self.params,guess=self.guess)
            self.solveWindow.multiSolve()

            self.main.after(500,self.check)

            self.main.after(500,self.liftWindows)

        else:
            self.destroy()

    def check(self):
        if self.solveWindow.s.isAlive():
            self.main.after(500,self.check)
        else:            
            self.solveWindow.destroy()
            self.main.refreshState()
            self.i += 1
            self.update()

    def liftWindows(self):
        
        self.lift()
        self.solveWindow.lift()

class EqmArrow(Canvas):
    def __init__(self,parent,w,h):
        Canvas.__init__(self,parent,width=w,height=h)
        h1 = int(h/2+2)
        h2 = int(h/2-2)
        self.create_line(0,h1,w,h1)
        self.create_polygon(0,h1,8,h1,8,h1+5)
        self.create_line(0,h2,w,h2)
        self.create_polygon(60,h2,52,h2,52,h2-5)

class About(BkToplevel):
    
    def __init__(self,parent,main):

        BkToplevel.__init__(self,parent)

        self.main = main
        self.parent = parent
        self.geometry('500x400')

        self.title('About Beaker')

        self.frame = ttk.Frame(self, padding='20 20 20 20',relief='solid')
        self.frame.grid(column=0,row=0, sticky=(N,W,E,S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)
        ttk.Label(self.frame,text='About:',font='BkXLargeBold').grid(column=1,row=0)
        vtext = 'Version: %s.%s - revision %s' % (tuple(version.versionString.split('.')))
        ttk.Label(self.frame,text=vtext,font='BkLargeBold',padding='0 0 0 15').grid(column=1,row=1)

        self.textBox = Text(self.frame,width=25,height=15)
        self.textBox.grid(column=1,row=2,sticky='NWES')

        self.textBox.insert('end', 'Beaker is free software; you can redistribute it and/or modify it under the terms of the GNU General ')
        self.textBox.insert('end', 'Public Licence as published by the Free Software Foundation; either version 2 of the Licence, or (at ')
        self.textBox.insert('end', 'your option) any later version.\n\n')

        self.textBox.insert('end', 'Beaker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the ')
        self.textBox.insert('end', 'implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public ')
        self.textBox.insert('end', 'Licence for more details.\n\n')

        self.textBox.insert('end', 'Beaker was written by Rob Beagrie, with the support of the Ben Luisi Group (especially Prof. Luisi ')
        self.textBox.insert('end', 'and Dr. Steven Hardwick). Beaker incorporates some code from the kinpy project ')
        self.textBox.insert('end', '(http://code.google.com/p/kinpy/) which was written by Akshay Srinivasan of the National Institute of ')
        self.textBox.insert('end', 'Technology Karnataka, Surathkal, India.')

        self.textBox['state'] = 'disabled'
        self.textBox['background'] = Canvas()['highlightbackground']
        self.textBox['wrap'] = 'word'
        self.textBox['font'] = 'BkDefaultFont'
        self.image = PhotoImage(file=refs.gifpath)
        self.label = ttk.Label(self.frame,image=self.image)
        self.label.grid(column=0,row=0,rowspan=3)
        
