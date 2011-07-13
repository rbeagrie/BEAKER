"""BEAKER is an open source program designed for modelling enzymatic reactions."""

import os, logging, cPickle, kinpy, sys, csv, numpy as np
from scipy import optimize

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
            raise BeakerException('Model file does not exist')
        
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
            raise BeakerException('Could not determine the input file type')

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
        try:
            kinpy_code = __import__(filename)
        except:
            raise BeakerException('Not a valid kinpy code file')
        #Make sure module is most recent version
        reload(kinpy_code)
        #Remove parent directory from PYTHONPATH
        del sys.path[0]
        #Make a new reaction_model object
        self.kinpy_model = kinpy_code.reaction_model()
        #Make a shortcut to the reactants set
        self.reactants = self.kinpy_model.reactants

    def run(self,times,starting_concentrations,parameters):

        """Run the model and return concentrations and rates of change for all reactants"""

        #Create a dictionary to hold the results
        run_results = {}
        #Get concentrations for all reactants and time points
        concentrations = self.kinpy_model.run(starting_concentrations,times,parameters)
        #Get rates for all reactants and time points
        rates = self.get_rates(concentrations,parameters)
        concentrations = concentrations.transpose()
        rates = rates.transpose()
        #Assemble results into a dictionary
        for i,reactant in enumerate(self.reactants):
            run_results[reactant] = {}
            run_results[reactant]['conc'] = concentrations[i]
            run_results[reactant]['rate'] = rates[i]
            run_results[reactant]['time'] = times
        #Return the dictionary
        return run_results

    def get_rates(self,concentrations,parameters):

        """Run the model, returning rates of change for all reactants"""

        #Create a list to hold the results
        results = []
        for i,y in enumerate(concentrations):
            results.append(self.kinpy_model.dy(y,0,parameters))

        return np.array(results)

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

    def save_experiment(self,autocomplete=False):

        """Saves the current experiment into the experiments list"""

        #Check the experiment object
        self.current_experiment.check(autocomplete)
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
        #Erase concentration_times cache
        self.cached_time = False
        #Erase rate_times cache

    def new_data_dictionary(self):

        """Creates a new, empty data dictionary"""

        #Get the list of reactants for the model
        reactants = self.session.model.reactants
        #Create a dictionary
        reactant_dictionary = {}
        #Create an empty entry in the data dictionary for each of the reactants
        for reactant in reactants:
            reactant_dictionary[reactant] = False
        #Return the dictionary
        return reactant_dictionary

    def assign_reactant(self,reactant,reactant_data):

        """Assigns an initial_condition, time_series or rate object to a reactant in the dictionary"""

        #Check to make sure the reactant_data is valid
        if not isinstance(reactant_data,self.data_classes):
            raise BeakerException('Data supplied is not an initial_concentration, time_series or rate object.')
        #Assign the data to the reactant
        self.data[reactant] = reactant_data
        self.reset_flags()

    def set_starting_concentrations(self,concentrations):

        """Accepts a list of reactant:concentration pairs and assigns them to reactants"""

        for reactant in concentrations:
            self.data[reactant] = initial_concentration(concentrations[reactant])

    def check(self,autocomplete=False):

        """Checks the reactant dictionary to ensure all reactants are assigned correctly"""

        #If this experiment has been checked previously, don't check again
        if (self.checked): return True

        #If autocomplete is true, autocomplete before checking
        if autocomplete: self.auto_complete()

        #This experiment has been checked
        self.checked = True

        #Check the reactant set matches that of the model
        if not set(self.data.keys()) == set(self.session.model.reactants):
            raise BeakerException('Reactants are not all assigned for this reaction')
            #Failed the check
            self.checked = False
            return False

        #Check all reactants are set correctly
        for reactant in self.data:
            if not self.data[reactant]:
                print self.data[reactant]
                raise BeakerException('Assigned data is not an initial_concentration, time_series or rate object.')
                #Failed the check
                self.checked = False
                break

        return self.checked

    def auto_complete(self):

        """Sets all unassigned reactants to an initial concentration of 0"""

        #If experiment has been checked, it must be complete
        if self.checked:
            return True

        for reactant in self.data:
            if not self.data[reactant]:
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
            starting_concentrations.append(self.data[reactant].starting_concentration)
        
        #return the starting concentration list
        return starting_concentrations

    def times(self):

        """Return a list of the time points present in the experimental data"""

        #Make sure the experiment has passed a check
        if not self.check():
            return False

        #Check for a cached version
        if self.cached_time:
            return self.cached_time

        #Create an empty set to store the time points
        time_points = set()

        #Add time points to the set
        for reactant in self.data:
            if isinstance(self.data[reactant],time_series):
                for point in self.data[reactant].time_points:
                    time_points.add(point)
            elif isinstance(self.data[reactant],rate):
                time_points.add(self.data[reactant].time)

        #convert the set to a list and order it
        time_list = list(time_points)
        time_list.sort()

        #Cache the time points
        self.cached_time = time_list

        #Return the time points
        return self.cached_time

class time_series():

    """Stores a series of concentration measurements over time"""

    def __init__(self,times,concentrations,starting_concentration=False):

        """Initiates a new time_course object"""

        #Check that a starting concentration was provided
        if not starting_concentration:
            if times[0] == 0.0:
                starting_concentration = concentrations[0]
            else:
                raise BeakerException('No starting concentration provided.')

        #Check that time and concentration are the same length
        if not len(times) == len(concentrations):
            raise BeakerException('Time and concentration arrays must be the same length')
              
        #Create the variables
        self.time_points = times
        self.concentrations = concentrations
        self.starting_concentration = starting_concentration

class rate():

    """Stores a reaction rate"""

    def __init__(self,rate,time,starting_concentration):

        """Initiates a new rate object"""

        #Create the variables
        self.rate = rate
        self.time = time
        self.starting_concentration = starting_concentration

class initial_concentration():

    """Stores an initial concentration"""

    def __init__(self,starting_concentration=0.0):

        """Initiates a new initial_concentration object"""

        #Create the variable
        self.starting_concentration = starting_concentration
    
class importer():

    """Handles the extraction of data from flat text files"""
    
    def __init__(self,experiment):

        """Initiates a new importer object"""

        #Make the parent experiment available
        self.experiment = experiment
        #Create the variable
        self.dictionary = False

    def text_to_dictionary(self,text_file,delimiter='\t'):

        """Converts a text file to a dictionary object"""

        #Open the text file
        text_file = open(text_file,'r')
        #Pass it to the csv reader
        data_object = csv.DictReader(text_file,delimiter=delimiter)

        #Create the dictionary object
        data_dictionary = {}
        for field in data_object.fieldnames:
            data_dictionary[field] = []

        #Read the data into the dictionary
        for row in data_object:
            for key in row:
                data_dictionary[key].append(float(row[key]))

        #Return the dictionary
        return data_dictionary

    def import_time_series(self,text_file,delimiter='\t',time_key='T'):

        """Converts a text file to a dictionary of time_series objects"""

        #Create the initial dictionary
        temp_dictionary = self.text_to_dictionary(text_file,delimiter=delimiter)

        #Create the storage dictionary
        self.dictionary = {}

        #Convert lists to time series
        for key in temp_dictionary:
            if not key == time_key:
                self.dictionary[key] = time_series(temp_dictionary[time_key],temp_dictionary[key])

    def assign(self,dictionary_key,model_key):

        """Assigns imported data to the experiment"""

        #Assign the data
        self.experiment.assign_reactant(model_key,self.dictionary[dictionary_key])
                
    
class model_solver():

    """Fits the provided data to the model to give a best fit set of model parameters"""
    
    def __init__(self,session):

        """Initiates the model_solver object"""

        #Make the session available
        self.session = session
        #create a dictionary of function solvers
        self.solver = {'simplex':optimize.fmin,'anneal':optimize.anneal}

    def solve(self,method='simplex',initial_guess=False):

        """Fit the session data to the model and return an estimate of the model parameters"""

        #Check to see if an initial guess for the parameters was given
        if not initial_guess:
            #if not, set every parameter to 1
            initial_guess = []
            for i in range(len(self.session.model.kinpy_model.debug_k)):
                initial_guess.append(1.0)

        #Check to ensure the initial_guess is of the correct length
        if not len(initial_guess) == len(self.session.model.kinpy_model.debug_k):
            raise BeakerException('Initial guess does not have the right number of elements')

        #Solve the model by minimizing the least square difference between the model and the data
        print self.solver[method](self.total_square_difference,initial_guess)

    def total_square_difference(self,parameters):

        """Calculate the square difference between the model and the data"""

        total = 0

        #Check to ensure none of the parameters is negative
        for i,v in enumerate(parameters):
            if v < 0:
                parameters[i] = 0 - v

        for id in self.session.data.experiments:

            #Get the experiment object 
            experiment = self.session.data.experiments[id]

            #Get the starting concentrations    
            starting_concentrations = experiment.starting_concentrations()

            #Run the model for the time points in the experimental data
            modelled_data = self.session.model.run(experiment.times(),starting_concentrations,parameters)

            #Calculate the difference between model and data for each reactant
            for reactant in self.session.model.reactants:
                observed = experiment.data[reactant]

                #Use concentration data if the reactant is a time_series
                if isinstance(experiment.data[reactant],time_series):
                    expected = self.subset_conc(modelled_data[reactant],observed)
                    #Calculate the square difference and add it to the running total
                    total += self.conc_square_difference(expected,observed)

                #Use rate data if the reactant is a rate object    
                elif isinstance(experiment.data[reactant],rate):
                    expected = self.subset_rate(modelled_data[reactant],observed)
                    #Calculate the suqare difference and add it to the running total
                    total += expected.sq_diff(observed)

        #Return the total squared difference
        return total

    def conc_square_difference(self,expected,observed):

        """Return the square difference between calculated and observed concentrations"""

        total = 0

        for i,a in enumerate(expected.concentrations):
            total += self.point_square_difference(a,observed.concentrations[i])

        return total

    def point_square_difference(self,a,b):

        """Return the square difference of a and b"""

        return ((a - b)**2)

    def subset_conc(self,expected,observed):

        """Return only the expected concentrations calculated for time points present in the observed concentrations"""

        data_subset = []
        
        for time in observed.time_points:
            data_subset.append(expected['conc'][expected['time'].index(time)])

        return time_series(observed.time_points,data_subset)

    def subset_rate(self,expected,observed):

        """Return only the expected rate calculated for time of the observed rate"""

        return expected['rate'][expected['time'].index(observed.time)]

        
        

class BeakerException(Exception):
    pass
