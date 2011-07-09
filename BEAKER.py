"""BEAKER is an open source program designed for modelling enzymatic reactions."""

import os, logging, cPickle, kinpy, sys

class session():

    """
    Class for a BEAKER session

    The BEAKER session holds the model of the reaction, the experimental data
    and a 'solver' which finds solutions of the model that fit the data.
    """

    def __init__(self,name,debug='WARNING',directory=False,project_file=False):

        """Initiates a new BEAKER session"""

        #Set the project name
        self.name = name

        #Set the home directory
        if not directory:
            directory = os.path.join(os.path.expanduser('~\\BEAKER\\'),self.name)
        self.directory = directory

        #Check the home directory exists, if not create it
        if not os.path.isdir(directory):
            os.makedirs(directory)

        #Set the debugging level
        log_level = getattr(logging, debug.upper())
        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % debug)
        logging.basicConfig(level=log_level, filename=os.path.join(self.directory,'debug.log'),
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        #Create a model_solver object and attach it to the session
        self.solver = model_solver(self)

        #If an existing project file is specified, load it.
        if project_file:
            logging.info('Loading previous project file: %s' % project_file)
            self.load(project_file)

    def initiate_model(self,model_file):

        """Initiates a new BEAKER model"""

        #Create a new model from the model file and attach it to the session
        logging.info('Creating a new model')
        self.model = model(self, model_file)

    def initiate_data(self):

        """Initiates a new BEAKER data object"""

        #Create an empty data object and attach it to the session
        logging.info('Creating a new data object')
        self.data = data(self)

    def save(self):

        """Saves the current BEAKER session"""

        #Save the session object to a file by pickling it
        logging.info('Saving all data')
        save_file = os.path.join(self.directory,self.name,'.bkr')
        f = open(save_file, 'w')
        cPickle.dump(self,f)
        f.close()

class model():

    """
    Class to hold the reaction model

    This class holds the set of differential equations and variables (or 'model')
    which we use to simulate a chemical reaction in silico. It contains fuctions
    to generate this model using an input file and the kinpy script (a source
    code generator provided by Akshay Srinivasan).
    """

    def __init__(self,session,input_file):

        """Initiates a new model object"""

        #Make the parent session object accessible
        self.session = session

        #Run a function to parse the input file
        self.parse_input_file(input_file)

    def parse_input_file(self,input_file):

        """Checks the type of model file supplied and handles it appropriately"""

        #Check that the model file exists
        if not os.path.exists(input_file):
            raise IOError('Model file does not exist')
        
        #Check the extension of the model file
        root,ext = os.path.splitext(input_file)
        if ext == '.k':
            #Input is a kinpy file, so run kinpy
            self.run_kinpy(input_file)
        elif ext == '.py':
            #Input is kinpy generated code, so import it
            self.import_kinpy(input_file)
        else:
            #Could not determine file type
            raise Exception('Could not determine the input file type')

    def run_kinpy(self,model_file):

        """Passes a kinpy file to kinpy, then imports the resulting source code"""

        #Set an output file
        output_file = os.path.join(self.session.directory,'kinpy_code.py')
        #Run kinpy
        kinpy.generate(model_file,output_file)
        #Import the kinpy code
        self.import_kinpy(output_file)

    def import_kinpy(self,code_file):

        """Imports the generated kinpy code as a new module"""

        #Get the path of the parent directory
        path, filename = os.path.split(code_file)
        #Get the module name
        filename, ext = os.path.splitext(filename)
        #Add the parent directory to the PYTHONPATH
        sys.path.insert(0, path)
        #Import the module
        kinpy_code = __import__(filename)
        #Make sure module is most recent version
        reload(kinpy_code)
        #Remove parent directory from PYTHONPATH
        del sys.path[0]
        #Make a new reaction_model object
        self.kinpy_model = kinpy_code.reaction_model()
        #Make a shortcut to the run function
        self.run = self.kinpy_model.run
        #Make a shortcut to the reactants set
        self.reactants = self.kinpy_model.reactants

class data():

    """
    Class to hold the experiment objects

    This class maintains a list of experiment objects and their unique identifiers. It implements
    functions to add and remove experiment objects.
    """

    def __init__(self,session):

        """Initiates a new data object"""

        #Make the parent session object accessible
        self.session = session
        #Create an empty dictionary to hold experiment objects
        self.experiments = {}
        #Initiate the id variable
        self.id_counter = 0

    def new_id(self):

        """Returns the next unique id and increments the id variable"""

        #Pick the next id
        next_id = self.id_counter
        #Increment the counter
        self.id_counter += 1
        #Return the new id
        return next_id

    def add_experiment(self):

        """
        Creates a new experiment object

        A new experiment object is created and stored temporarily in the current_experiment variable.
        The experiment is not added to the experiments list until the save() function is called.
        """

        #Pick an id for the new experiment
        current_id = self.new_id()
        #Create the experiment object
        self.current_experiment = experiment(self.session,current_id)

    def delete_experiment(self,experiment_id):

        """Removes an experiment from the experiments list"""

        del self.experiments[experiment_id]

    def modify_experiment(self,experiment_id):

        """Moves an experiment from the experiments list to the temporary store"""

        #Copy the experiment into the temporary store
        self.current_experiment = self.experiments[experiment_id]
        #Delete the experiment from the experiments list
        self.delete_experiment(experiment_id)

    def save_experiment(self):

        """Saves the current experiment into the experiments list"""

        #Check the experiment object
        self.current_experiment.check()
        #Copy to the experiment list
        self.experiments[self.current_experiment.id] = self.current_experiment
        #Clear the temporary store
        del self.current_experiment

class experiment():

    """A class to hold experimental data

    The experiment class holds experimental results for the system under a single specified set of
    conditions. Each chemical species (reactant) present in the model definition must be present in
    each experiment object. An initial concentration must be supplied for each chemical species, as
    these form the starting conditions for the modelling. Additionally, each chemical species may be
    associated with a concentration series or a rate of change if these data were collected. In this
    case the data is used to estimate kinetic rate constants for the model system.
    """

    def __init__(self,session,experiment_id):

        """Initiates a new experiment object"""

        #Make the parent session object accessible
        self.session = session

        #Set the experiment id
        self.id = experiment_id
        #Create the data dictionary
        self.data = self.new_data_dictionary()
        #Create the data importer
        self.importer = importer(self)
        #Create a tuple of valid classes for data objects
        self.data_classes = (initial_concentration,time_series,rate)
        #Set the flags to an unchecked state
        self.reset_flags()

    def reset_flags(self):

        """Resets various flags to ensure experiment is properly checked after changes have been made"""
        
        #This experiment has not been checked yet
        self.checked = False
        #Erase starting_concentration cache
        self.cached_concentrations = False
        #Erase time cache
        self.cached_time = False

    def new_data_dictionary(self):

        """Creates a new, empty data dictionary"""

        #Get the list of reactants for the model
        reactants = session.model.reactants
        #Create a dictionary
        reactant_dictionary = {}
        #Create an empty entry in the data dictionary for each of the reactants
        for reactant in reactants:
            reactant_dictionary[reactant] = None
        #Return the dictionary
        return reactant_dictionary

    def assign_reactant(self,reactant,reactant_data):

        """Assigns an initial_condition, time_series or rate object to a reactant in the dictionary"""

        #Check to make sure the reactant_data is valid
        if not isinstance(reactant_data,self.data_classes):
            raise Exception('Data supplied is not an initial_concentration, time_series or rate object.')
        #Assign the data to the reactant
        self.data[reactant] = reactant_data
        self.reset_flags()

    def check(self,autocomplete=False):

        """Checks the reactant dictionary to ensure all reactants are assigned correctly"""

        #If this experiment has been checked previously, don't check again
        if (self.checked): return True

        #If autocomplete is true, autocomplete before checking
        if autocomplete: self.autocomplete()

        #This experiment has been checked
        self.checked = True

        #Check the reactant set matches that of the model
        if not set(self.data.keys()) = set(self.session.model.reactants):
            raise Exception('Reactants are not all assigned for this reaction')
            #Failed the check
            self.checked = False
            return False

        #Check all reactants are set correctly
        for reactant_data in data:
            if not isinstance(reactant_data,self.data_classes):
                raise Exception('Assigned data is not an initial_concentration, time_series or rate object.')
                #Failed the check
                self.checked = False
                break

        return self.checked

    def auto_complete(self):

        """Sets all unassigned reactants to an initial concentration of 0"""

        #If experiment has been checked, it must be complete
        if self.checked:
            return True

        for reactant in self.data.keys()
            if type(self.data[reactant]) == None:
                self.data[reactant] = initial_concentration()

    def starting_concentrations(self):

        """Returns a list of starting concentrations for passing to the modeller"""

        #Make sure the experiment has passed a check
        if not self.check():
            return False

        #Check for a cached version
        if self.cached_concentrations:
            return self.cached_concentrations

        #Create an empty list to store the concentrations
        starting_concentrations = list()

        #Add each starting concentration in the order specified by the model
        for reactant in self.session.model.reactants:
            starting_concentrations.append(self.reactant_dictionary[reactant].starting_concentration())
        
        #return the starting concentration list
        return starting_concentrations

    def time_points(self):

        """Returns a list of all time points present in the experimental data"""

        #Make sure the experiment has passed a check
        if not self.check():
            return False

        #Check for a cached version
        if self.cached_time:
            return self.cached_time

        #Create an empty set to store the time points
        time_points = set()

        #Add time points to the set
        for reactant_data in self.data:
            for point in reactant_data.time_points()
                time_points.add(point)

        #convert the set to a list and order it
        sorted_time_points = list(time_points)
        sorted_time_points = sorted_time_points.sort()
        
        #return the starting concentration list
        return sorted_time_points
        
    
class model_solver():
    def __init__(self,session):
        self.blank = 'placeholder'
