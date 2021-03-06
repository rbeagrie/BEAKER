"""BEAKER is an open source program designed for modelling enzymatic reactions."""

import os, logging, cPickle, kinpy2, sys, random, csv
from numpy import array
from scipy import optimize
from types import *

class session():

    """
    Class for a BEAKER session

    The BEAKER session holds the model of the reaction, the experimental data
    and a 'solver' which finds solutions of the model that fit the data.
    """

    def __init__(self,name='New Project',debug='WARNING',directory=False,units='milli',project_file=False):

        """Initiate a new BEAKER session"""

        #Check the variables
        assert type(name) is StringType, 'Invalid project name "%s": project name must be a string' % name
        assert debug in set(['WARNING','DEBUG','INFO']), 'Invalid debugging level "%s": valid levels are "WARNING", "INFO" AND "DEBUG"' % debug
        assert directory is False or type(directory) is StringType, 'Invalid directory name "%s": directory name must be a string' % directory
        assert project_file is False or type(project_file) is StringType, 'Invalid project file name "%s": project file name must be a string' % project_file

        if project_file:
            self.load(project_file)
        else:
        
            #Set the project name
            self.name = name

            self.units = units

            self.data = False
            
            self.model = model(self)

            self.solutions = []

            #Set the home directory
            if not directory:
                directory = os.path.join(os.path.expanduser('~\\BEAKER\\'),self.name)
            self.directory = directory

            #Check the directory is given as an absolute path
            if not os.path.isabs(self.directory):
                raise BeakerException('Project directory path "%s" is invalid' % self.directory)

            #Check the home directory exists, if not create it
            if not os.path.isdir(directory):
                os.makedirs(directory)

            #Set the debugging level
            #log_level = getattr(logging, debug.upper())
            #if not isinstance(log_level, int):
            #    raise ValueError('Invalid log level: %s' % debug)
            #logging.basicConfig(level=log_level, filename=os.path.join(self.directory,'debug.log'),
            #    format='%(asctime)s %(levelname)s: %(message)s',
            #    datefmt='%Y-%m-%d %H:%M:%S')

            #Create a model_solver object and attach it to the session
            self.solver = model_solver(self)

            logging.info('Started a new BEAKER session')

    def initiate_data(self):

        """Initiate a new BEAKER data object"""

        #Create an empty data object and attach it to the session
        self.data = data(self)
        logging.info('Created a new data object')

    def save(self,save_file = False):

        """Save the current BEAKER session"""

        #Save the session object to a file by pickling it
        if not save_file:
            save_file = os.path.join(self.directory,self.name,'.bkr')
        sobject = SaveObject(self)
        f = open(save_file, 'w')
        cPickle.dump(sobject,f)
        f.close()
        logging.info('Saved all data to %s' % save_file)

    def load(self,project_file):
        
        f = open(project_file,'r')
        sobject = cPickle.load(f)
        f.close()

        #Set the project name
        self.name = sobject.name

        self.units = sobject.units

        self.directory = sobject.directory
        
        self.model = model(self)

        self.solutions = sobject.solutions

        if sobject.model_definition:

            self.model.import_definition(sobject.model_definition)

        if sobject.data:

            self.data = data(self,sobject.data)

        else:

            self.data = False

        #Create a model_solver object and attach it to the session
        self.solver = model_solver(self)

        logging.info('Loaded BEAKER session from "%s"' % project_file)

class model():

    """
    Class to hold the reaction model

    This class holds a set of differential equations and variables 
    used to simulate a chemical reaction in silico. It contains fuctions
    to generate this model using an input file and the kinpy script (a source
    code generator provided by Akshay Srinivasan).
    """

    def __init__(self,session):

        """Initiate a new model object"""

        #Make the parent session object accessible
        self.session = session

        self.definition = False

        logging.info('Initialised the model object')

    def import_file(self,input_file):

        self.__read_file(input_file)
        self.__run_kinpy2()

        logging.info('Imported model from %s' % input_file)

    def import_definition(self,definition):

        self.definition = definition
        self.__run_kinpy2()

        logging.info('Set the model definition')

    def __read_file(self,input_file):

        """Checks the type of model file supplied and handles it appropriately"""
        
        logging.debug('Parsing model input file: %s' % input_file)

        assert type(input_file) is StringType, 'Invalid input file path "%s": inpu file path must be a string' % input_file

        #Check that the model file exists
        if not os.path.exists(input_file):
            raise BeakerException('Model file "%s" does not exist' % input_file)
        
        f = open(input_file,'r')
        self.definition = []
        for line in f:
            if not line.rstrip('\n') == '':
                self.definition.append(line.rstrip('\n'))
        f.close()
        
        logging.debug('Finished parsing model input file: %s' % input_file)

    def __run_kinpy2(self):

        logging.debug('Passing model definition to kinpy2')

        self.kinpy_model = kinpy2.model()
        try:
            self.kinpy_model.importer.import_definition(self.definition)
        except:
            raise BeakerException('Entry is not a valid model definition')
        self.reactants = self.kinpy_model.species
        self.session.initiate_data()

        logging.debug('Model definition compiled successfully')

    def run(self,times,starting_concentrations,parameters):

        """Run the model and return concentrations and rates of change for all reactants"""

        #assert type(times[0]) is FloatType, 'Times must be a subscriptable object containing floats.'
        assert type(starting_concentrations[0]) is FloatType, 'Starting Concentrations must be a subscriptable object containing floats.'
        

        #Create a dictionary to hold the results
        run_results = {}
        #Get concentrations for all reactants and time points
        logging.info('Running a simulation of the model reaction')
        logging.debug('Model parameters: %s' % parameters)
        logging.debug('Modelling time points: %s' % times)
        logging.debug('Reactant initial concentrations: %s' % starting_concentrations)
        concentrations = self.kinpy_model.run(starting_concentrations,times,parameters)
        #Get rates for all reactants and time points
        rates = self.__get_rates(concentrations,parameters)
        concentrations = concentrations.transpose()
        rates = rates.transpose()
        #Assemble results into a dictionary
        for i,reactant in enumerate(self.reactants):
            run_results[reactant] = {}
            run_results[reactant]['conc'] = concentrations[i]
            run_results[reactant]['rate'] = rates[i]
            run_results[reactant]['time'] = times
        #Return the dictionary
        logging.info('Finished simulating the model reaction')
        return run_results

    def __get_rates(self,concentrations,parameters):

        """Run the model, returning rates of change for all reactants"""

        #Create a list to hold the results
        results = []
        for i,y in enumerate(concentrations):
            results.append(self.kinpy_model.dy(y,0,parameters))

        return array(results)

class data():

    """
    Class to hold the experiment objects

    This class maintains a list of experiment objects and their unique identifiers. It implements
    functions to add and remove experiment objects.
    """

    def __init__(self,session,saveObject=False):

        """Initiates a new data object"""

        #Make the parent session object accessible
        self.session = session
            
        #Create an empty dictionary to hold experiment objects
        self.experiments = {}

        if saveObject:
            self.load(saveObject)
        else:
            #Initiate the id variable
            self.id_counter = 1
        
        #Initiate the importers
        self.concentration_importer = concentration_importer(self)
        self.rate_importer = rate_importer(self)

        logging.info('Initialised the data object')

    def __new_id(self):

        """Returns the next unique id and increments the id variable"""

        #Pick the next id
        next_id = self.id_counter
        #Increment the counter
        self.id_counter += 1
        #Return the new id
        logging.debug('Next experiment id is %s' % next_id)
        return next_id

    def add_experiment(self,new_experiment):

        """
        Add an experiment object to the experiments list

        An experiment object is added to the experiments list and given a unique id.
        """

        assert isinstance(new_experiment,experiment), 'Experiment "%s" is not a valid BEAKER experiment object' % experiment
        
        #Pick an id for the new experiment
        current_id = self.__new_id()
        #Create the experiment object
        self.experiments[current_id] = new_experiment

        logging.info('Experiment #%s added to experiments list' % current_id)

    def delete_experiment(self,experiment_id):

        """Removes an experiment from the experiments list"""

        del self.experiments[experiment_id]

        logging.info('Experiment #%s deleted from experiments list' % experiment_id)

    def save(self):

        logging.debug('Saving the data object')

        return DataSaveObject(self)

    def load(self,saveObject):

        logging.debug('Loading the data object')

        self.id_counter = saveObject.id_counter

        for xid in saveObject.experiments:
            self.experiments[xid] = experiment(self.session,saveObject.experiments[xid])
        

class experiment():

    """A class to hold experimental data

    The experiment class holds experimental results for the system under a single specified set of
    conditions. Each chemical species (reactant) present in the model definition must be present in
    each experiment object. An initial concentration must be supplied for each chemical species, as
    these form the starting conditions for the modelling. Additionally, each chemical species may be
    associated with a concentration series or a rate of change if these data were collected. In this
    case the data is used to estimate kinetic rate constants for the model system.
    """

    def __init__(self,session,reactant_dictionary):

        """Initiate a new experiment object"""

        assert type(reactant_dictionary) is DictType, 'Reactant dictionary must be a dictionary'
        assert set(reactant_dictionary.keys()) == set(session.model.reactants), 'Keys of reaction dictionary must exactly match those of the model'
        
        self.data = reactant_dictionary
        self.load()
        self.times = self.__cache_times()
        self.session = session
        self.starting_concentrations = self.__cache_concentrations()

        logging.info('Created a new experiment object')

    def load(self):
        for r in self.data:
            if isinstance(self.data[r],RateSeriesSaveObject):
                self.data[r] = rate_series(load=self.data[r])

    def __cache_concentrations(self):

        """Returns a list of starting concentrations for passing to the modeller"""

        logging.debug('Setting starting concentrations for experiment')

        #Create an empty list to store the concentrations
        starting_concentrations = list()

        #Add each starting concentration in the order specified by the model
        for reactant in self.session.model.reactants:
            starting_concentrations.append(self.data[reactant].starting_concentration)

        logging.debug('Experiment starting concentrations are %s' % starting_concentrations)
        
        #return the starting concentration list
        return starting_concentrations

    def __cache_times(self):

        """Return a list of the time points present in the experimental data"""

        logging.debug('Setting time points for experiment')

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

        logging.debug('Experiment time points are %s' % time_list)

        #Return the time points
        return time_list

class time_series():

    """
    Class to store reactant concentration measurements

    This class stores a list of reactant concentration measurements as well as a list
    of time points at which they were collected. It can also store an initial concentration
    of the reactant (i.e. that amount which is known to have been present at t=0."""

    def __init__(self,times,concentrations,starting_concentration=False):

        """Initiates a new time_course object"""

        assert type(times[0]) is FloatType, 'Times must be a subscriptable object containing floats.'

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

        logging.info('Created new time_series object')

class rate_series():

    """Stores a series of reaction rates"""

    def __init__(self,time=0.0,load=False):

        """Initiates a new object"""

        if load:
            self.rates = load.rates
            self.time = load.time
            self.concentrations = load.concentrations
            self.starting_concentration = load.starting_concentration
            logging.info('Loaded a rate_series object')
        else:

            assert type(time) is FloatType, '%s is an invalid time. Time must be a float.' % time

            #Create the variables
            self.rates = False
            self.time = time
            self.concentrations = False
            self.starting_concentration = False

            logging.info('Created a new rate_series object')

    def set_rates(self,rate_data):

        """Assign rate_data to the rate series as a set of measured rates"""

        assert type(rate_data[0]) is FloatType, '%s is invalid. Rate Data must be a subscriptable object containing floats.' % rate_data[0]

        self.rates = rate_data

        logging.debug('Assigned a set of rate measurements to the rate_series object')

    def set_concentrations(self,conc_data):

        """Assign conc_data to the rate series as a set of starting concentrations"""

        assert type(conc_data[0]) is FloatType, '%s is invalid. Concentration Data must be a subscriptable object containing floats.' % conc_data[0]

        self.concentrations = conc_data
        self.starting_concentration = True

        logging.debug('Assigned a set of starting concentrations to the rate_series object')

    def get(self,i):

        """Return an experiment object for the i-th measured rate"""

        assert type(i) is IntType, 'Could not retrieve experiment "%s" - i must be an integer.'

        logging.debug('Returning object for measurement %s of the current rate series' % i)
        
        #Check that a starting concentration has been set
        if self.starting_concentration is False:
            raise BeakerExeption('Starting Concentration not yet set')

        #Choose the appropriate object to return depending on what experimental data has been set
        if not self.rates:
            if not self.concentrations:
                logging.debug('Measurement %s is a concentration (%s)' % (i,self.starting_concentration))
                return initial_concentration(self.starting_concentration)
            else:
                logging.debug('Measurement %s is a concentration (%s)' % (i,self.concentrations[i]))
                return initial_concentration(self.concentrations[i])
        else:
            if not self.concentrations:
                logging.debug('Measurement %s is a rate (%s). Starting concentration was %s' % (i,self.rates[i],self.starting_concentration))
                return rate(self.rates[i],self.time,self.starting_concentration)
            else:
                logging.debug('Measurement %s is a rate (%s). Starting concentration was %s' % (i,self.rates[i],self.concentrations[i]))
                return rate(self.rates[i],self.time,self.concentrations[i])

class rate():

    """Stores a reaction rate"""

    def __init__(self,rate,time=0.0,starting_concentration=0.0):

        """Initiate a new rate object"""

        assert type(rate) is FloatType, '"%s" is not a valid rate. Rate must be a float.'
        assert type(time) is FloatType, '"%s" is not a valid time. Time must be a float.'
        assert type(starting_concentration) is FloatType, '"%s" is not a valid concentration. Concentration must be a float.'

        #Create the variables
        self.rate = rate
        
        #At time 0 there is no ES complex so rate of P formation is 0.
        #If the initial rate is required, give the system a second to reach steady state.
        if time == 0.0:
            time = 1.0
        self.time = time
        
        self.starting_concentration = starting_concentration

        logging.info('Created a new rate object')
            

class initial_concentration():

    """Store an initial concentration"""

    def __init__(self,starting_concentration=0.0):

        """Initiates a new initial_concentration object"""
        
        assert type(starting_concentration) is FloatType, '"%s" is not a valid concentration. Concentration must be a float."' % starting_concentration

        #Create the variable
        self.starting_concentration = starting_concentration

        logging.info('Created a new initial_concentration object')

class importer():

    """Base class containing methods common to concentration_importer and rate_importer"""
    
    def __init__(self,data):

        """Initiate a new importer object"""

        #Make the session's data object available
        self.session = data.session
        #Create the reactant dictionary
        self.reactants = self.new_data_dictionary()
        #Create a tuple of valid classes for data objects
        self.data_classes = self.allowed_classes()
        #Set the flags to an unchecked state
        self.__reset_flags()

        self.dictionary = False

    def import_text(self,text_file,delimiter='\t'):

        """Convert text_file to a dictionary object"""

        logging.info('Importing data from %s' % text_file)

        assert type(text_file) is StringType, '"%s" is not a valid file name. File name must be a string.' % text_file

        #Check that the model file exists
        if not os.path.exists(text_file):
            raise BeakerException('Text file "%s" does not exist' % text_file)

        #Open the text file
        text_file = open(text_file,'r')
        #Pass it to the csv reader
        logging.info('Parsing data in %s' % text_file)
        data_object = csv.DictReader(text_file,delimiter=delimiter)

        #Create the dictionary object
        data_dictionary = {}
        logging.debug('%s columns found: %s' % (len(data_object.fieldnames),data_object.fieldnames))
        for field in data_object.fieldnames:
            data_dictionary[field] = []

        #Read the data into the dictionary
        for row in data_object:
            for key in row:
                data_dictionary[key].append(float(row[key]))

        #Return the dictionary
        self.dictionary = data_dictionary

        logging.info('Finished importing data from %s' % text_file)

    def new_data_dictionary(self):

        """Create a new, empty data dictionary"""

        #Get the list of reactants for the model
        reactants = self.session.model.reactants
        #Create a dictionary
        reactant_dictionary = {}
        #Create an empty entry in the data dictionary for each of the reactants
        for reactant in reactants:
            reactant_dictionary[reactant] = False
        #Return the dictionary
        return reactant_dictionary

    def __reset_flags(self):

        """Resets various flags to ensure data is properly checked after changes have been made"""
        
        #This data has not been checked yet
        self.checked = False
        #This data has not had data added yet
        self.length = False

        logging.debug('Setting importer flags')
        
    def set_starting_concentrations(self,concentrations):

        """Accepts a dictionary of reactant:concentration pairs and assigns them to reactants"""

        assert set(concentrations.keys()) <= set(self.reactants), '"%s" are not valid reactants. Dictionary keys must be reactants present in the model.' % list(set(concentrations.keys()).difference(set(self.reactants)))

        for reactant in concentrations:
            assert type(concentrations[reactant]) is FloatType, '"%s" is not a valid concentration. Concentration must be a float."' % concentrations[reactant]
            if not self.reactants[reactant]:
                self.reactants[reactant] = initial_concentration(concentrations[reactant])
            else:
                self.reactants[reactant].starting_concentration = concentrations[reactant]
            logging.debug('Reactant "%s" concentration set to %s' % (reactant,concentrations[reactant]))

        logging.info('Reactant starting concentrations have been set')

    def get_unset_reactants(self):

        """Returns a list of reactants missing starting concentrations"""

        logging.info('Getting reactants missing starting concentrations')
        
        unset_reactants = []

        reactants = self.reactants.keys()

        for reactant in reactants:
            if not self.reactants[reactant]:
                unset_reactants.append(reactant)
            elif not self.reactants[reactant].starting_concentration:
                if type(self.reactants[reactant].starting_concentration) is FloatType: continue
                unset_reactants.append(reactant)

        logging.info('Found %i reactants missing starting concentrations' % len(unset_reactants))

        return unset_reactants

    def __check(self,autocomplete=False):

        """Checks the reactant dictionary to ensure all reactants are assigned correctly"""

        #If the data has been checked previously, don't check again
        if (self.checked): return True

        #If autocomplete is true, autocomplete before checking
        if autocomplete: self.__auto_complete()

        logging.debug('Checking the imported data to ensure all reactants are assigned correctly')

        #This experiment has been checked
        self.checked = True

        #Check the reactant set matches that of the model
        if not set(self.reactants.keys()) == set(self.session.model.reactants):
            
            #Failed the check
            logging.debug('The set of reactants does not match those defined in the model.')
            self.checked = False
            
            raise BeakerException('Reactants are not all assigned for this reaction. "%s" are missing' % set(self.session.model.reactants).difference(self.reactants.keys()))        

            return False

        #Check all reactants are set correctly
        for reactant in self.reactants:
            if not (self.reactants[reactant] and isinstance(self.reactants[reactant],self.data_classes)):
                
                #Failed the check
                logging.info('Some reactants are not set correctly')
                self.checked = False
                
                raise BeakerException('"%s" at reactant "%s" is not an initial_concentration, time_series or rate object.') % self.reactants[reactant],reactant
                
                break

            if self.reactants[reactant].starting_concentration is False:
                
                #Failed the check
                logging.info('Some reactants are missing initial concentrations')
                self.checked = False
                
                raise BeakerException('No initial concentration assigned for reactant "%s"' % reactant)
                break           

        return self.checked

    def __auto_complete(self):

        """Sets all unassigned reactants to an initial concentration of 0"""

        #If data has been checked, it must be complete
        if self.checked:
            return True

        #If a reactants starting concentration is unset, give it an value of 0
        for reactant in self.reactants:
            if not self.reactants[reactant]:
                self.reactants[reactant] = initial_concentration()
                logging.debug('Reactant "%s" concentration automatically set to 0.0' % reactant)
            if isinstance(self.reactants[reactant],rate_series) and not self.reactants[reactant].starting_concentration:
                self.reactants[reactant].starting_concentration = 0.0
                logging.debug('Reactant "%s" concentration automatically set to 0.0' % reactant)

        logging.info('All unset reactants automatically set to 0')
    
    
class concentration_importer(importer):

    """Handles the extraction of concentration data from flat text files"""

    def allowed_classes(self):

        """Return a tuple of allowed classes"""
        
        return (initial_concentration,time_series)

    def assign(self,dictionary):

        """Takes a dictionary of model_key : dictionary_key pairs and performs assignments"""

        logging.info('Assigning imported concentration data to the model')

        if not 'time' in dictionary.keys():
            raise BeakerExeption('No time key specified')

        assert dictionary['time'] in self.dictionary, '"%s" is not a valid key. Time key must correspond to a column heading in the data file.' % dictionary[key]

        self.__assign_time(dictionary['time'])

        for key in dictionary:
            if key != 'time':

                assert key in self.reactants, '"%s" is not a valid reactant. Dictionary keys must be reactants defined in the model.' % key
                assert dictionary[key] in self.dictionary, '"%s" is not a valid key. Dictionary values must correspond to column headings in the data file.' % dictionary[key]
                
                self.__assign_concentration(dictionary[key],key)

    def __assign_time(self,time_key='T'):

        """Converts a dictionary of lists to time_series objects"""

        logging.debug('Setting %s as the time column' % time_key)

        #Convert lists to time series
        for key in self.dictionary:
            if not key == time_key:
                self.dictionary[key] = time_series(self.dictionary[time_key],self.dictionary[key])

    def __assign_concentration(self,dictionary_key,model_key):

        """Assigns imported data to the experiment"""

        #Assign the data
        self.reactants[model_key] = self.dictionary[dictionary_key]

        logging.debug('Column "%s" assigned to reactant "%s"' % (dictionary_key,model_key))

        logging.debug('"%s" concentration measurements are %s' % (model_key,self.dictionary[dictionary_key]))

    def save(self,autocomplete=False):

        """Saves the entered data"""

        #Check the data
        self._importer__check(autocomplete)

        #Create a new experiment from the assigned data
        new_experiment = experiment(self.session,self.reactants)

        #Save the experiment to the session
        self.session.data.add_experiment(new_experiment)
        
        #Reset the reactant dictionary
        self.reactants = self.new_data_dictionary()

        logging.info('Saved the imported concentration data to a new experiment')

class rate_importer(importer):

    """Handles the extraction of concentration data from flat text files"""

    def allowed_classes(self):

        """Return a tuple of allowed classes"""
        
        return (initial_concentration,rate_series)

    def assign_rates(self,assignments):

        """Assign a dictionary of model_key:dictionary_key pairs"""

        logging.info('Assigning imported rate data to the model')

        for model_key in assignments:

            assert model_key in self.reactants, '"%s" is not a valid reactant. Dictionary keys must be reactants defined in the model.' % model_key
            assert assignments[model_key] in self.dictionary, '"%s" is not a valid key. Dictionary values must correspond to column headings in the data file.' % dictionary[model_key]
                
            self.__assign_rate(model_key,assignments[model_key])

    def __assign_rate(self,model_key,dictionary_key):

        """Assigns a list to the reactant dictionary as a rate_series object"""

        #Check length
        self.__check_length(dictionary_key)

        #Check if the reactant has already been set in the dictionary
        if not isinstance(self.reactants[model_key],rate_series):
            #If not, initialise it
            self.reactants[model_key] = rate_series()
            
        #Assign the data
        self.reactants[model_key].set_rates(self.dictionary[dictionary_key])
        logging.debug('Column "%s" assigned to reactant "%s" as a set of rate measurements' % (dictionary_key,model_key))
        logging.debug('Reactant "%s" rate measurements are %s' % (model_key,self.dictionary[dictionary_key]))

    def assign_concentrations(self,assignments):

        """Assign a dictionary of model_key:dictionary_key pairs"""

        logging.info('Assigning imported concentration data to the model')

        for model_key in assignments:

            assert model_key in self.reactants, '"%s" is not a valid reactant. Dictionary keys must be reactants defined in the model.' % model_key
            assert assignments[model_key] in self.dictionary, '"%s" is not a valid key. Dictionary values must correspond to column headings in the data file.' % dictionary[model_key]
            
            self.__assign_concentration(model_key,assignments[model_key])

    def __assign_concentration(self,model_key,dictionary_key):

        """Assigns imported data to the experiment"""

        #Check length
        self.__check_length(dictionary_key)

        #Check the dictionary
        if not isinstance(self.reactants[model_key],rate_series):
            self.reactants[model_key] = rate_series()
            
        #Assign the data
        self.reactants[model_key].set_concentrations(self.dictionary[dictionary_key])
        
        logging.debug('Column "%s" assigned to reactant "%s" as a set of starting concentrations' % (dictionary_key,model_key))
        logging.debug('Reactant "%s" starting concentrations are %s' % (model_key,self.dictionary[dictionary_key]))

    def __check_length(self,dictionary_key):

        """Checks the length of data to import"""

        logging.info('Checking all data series contain the same number of entries')

        #Check if data has been imported before
        if not self.length:
            self.length = len(self.dictionary[dictionary_key])

        #Check that the length of the new data matches that of the previous
        if not self.length == len(self.dictionary[dictionary_key]):
            raise BeakerException('Data length does not match')
        
    def save(self,autocomplete=False):

        """Saves the entered data"""

        logging.info('Saving imported rate data to the session')

        #Check the data
        self._importer__check(autocomplete)

        #Loop over data to create experiments
        for i in range(self.length):
            temp_dictionary = self.new_data_dictionary()
            for reactant in self.reactants:
                if isinstance(self.reactants[reactant],initial_concentration):
                    temp_dictionary[reactant] = self.reactants[reactant]
                else:
                    temp_dictionary[reactant] = self.reactants[reactant].get(i)

            #Save the new experiment to the session        
            self.session.data.add_experiment(experiment(self.session,temp_dictionary))

            logging.info('Saving a new experiment')
        
        #Reset the reactant dictionary
        self.reactants = self.new_data_dictionary()
                
                
    
class model_solver():

    """Fits the provided data to the model to give a best fit set of model parameters"""
    
    def __init__(self,session):

        """Initiates the model_solver object"""

        #Make the session available
        self.session = session
        #create a dictionary of function solvers
        logging.debug('Loading the list of solving algorithms')
        self.solver = {'simplex':optimize.fmin,'anneal':optimize.anneal}

    def solve(self,method='simplex',initial_guess=False,call=None,params=False):

        """Fit the session data to the model and return an estimate of the model parameters"""

        logging.info('Preparing to solve the model.')

        assert method in self.solver.keys(), '"%s" is not a valid method for solving the model. Accepted parameters are: %s' % (method, self.solver.keys())

        logging.info('Solving the model using the "%s" function' % method)

        #Check to see if an initial guess for the parameters was given
        if not initial_guess:
            #if not, set every parameter to 1
            logging.debug('No initial guess provided, using default value (1.0)')
            initial_guess = []
            for i in range(len(self.session.model.kinpy_model.debug_k)):
                initial_guess.append(1.0)
    
        #Check to see if a random guess is required
        elif initial_guess == 'random':
            logging.debug('Generating a random initial guess')
            initial_guess = self.random_guess()

        #Check to ensure the initial_guess is of the correct length
        if not len(initial_guess) == len(self.session.model.kinpy_model.debug_k):
            raise BeakerException('Initial guess does not have the right number of elements')

        logging.debug('Initial guess for the model parameters is %s' % initial_guess)

        #Solve the model by minimizing the least square difference between the model and the data
        if params:
            logging.debug('Custom parameters provided: xtol = %(xtol)s, ftol = %(ftol)s, maxiter = %(maxiter)s, maxfun = %(maxfun)s' % params)
            try:
                sol = solution(self.solver[method](self.__total_square_difference,
                                                   initial_guess,
                                                   disp=False,
                                                   full_output=True,
                                                   xtol=params['xtol'],
                                                   ftol=params['ftol'],
                                                   maxiter=params['maxiter'],
                                                   maxfun=params['maxfun'],
                                                   args=(call,)),
                               initial_guess)
            except:
                sol = False
        else:
            logging.debug('Using default parameters')
            try:
                sol = solution(self.solver[method](self.__total_square_difference,
                                                   initial_guess,
                                                   disp=False,
                                                   full_output=True,
                                                   args=(call,)),
                               initial_guess)
            except:
                sol=False
            
        if sol:
            logging.info('Solution found!')
            self.session.solutions.append(sol)
        else:
            logging.warning('Solver terminated prematurely')
        return sol

    def __total_square_difference(self,parameters,call=False):

        """Calculate the square difference between the model and the data"""
        try:
            call()
        except:
            raise BeakerException('Solver terminated prematurely')
        
        #Start a running total
        total = 0

        #Check to ensure none of the parameters is negative
        for i,v in enumerate(parameters):
            if v < 0:
                #If it is, take its modulo
                parameters[i] = 0 - v

        #Loop over experiments
        for id in self.session.data.experiments:

            #Get the experiment object 
            experiment = self.session.data.experiments[id]

            #Get the starting concentrations    
            starting_concentrations = experiment.starting_concentrations

            #Get the times    
            times = experiment.times

            #Check the times include 0
            if not 0.0 in times:
                times.insert(0,0.0)

            #Run the model for the time points in the experimental data
            modelled_data = self.session.model.run(times,starting_concentrations,parameters)

            #Calculate the difference between model and data for each reactant
            for reactant in self.session.model.reactants:
                observed = experiment.data[reactant]

                #Use concentration data if the reactant is a time_series
                if isinstance(experiment.data[reactant],time_series):
                    expected = self.__subset_conc(modelled_data[reactant],observed)
                    #Calculate the square difference and add it to the running total
                    total += self.__conc_square_difference(expected,observed)

                #Use rate data if the reactant is a rate object    
                elif isinstance(experiment.data[reactant],rate):
                    expected = self.__subset_rate(modelled_data[reactant],observed)
                    #Calculate the suqare difference and add it to the running total
                    total += self.__point_square_difference(observed.rate,expected)

        #Return the total squared difference
        logging.debug('Using parameters of "%s", total squared difference between the data and the model is %s' % (parameters, total))
        return total

    def __conc_square_difference(self,expected,observed):

        """Return the square difference between calculated and observed concentrations"""

        total = 0

        for i,a in enumerate(expected.concentrations):
            total += self.__point_square_difference(a,observed.concentrations[i])

        return total

    def __point_square_difference(self,a,b):

        """Return the square difference of a and b"""

        return ((a - b)**2)

    def __subset_conc(self,expected,observed):

        """Return only the expected concentrations calculated for time points present in the observed concentrations"""

        data_subset = []
        
        for time in observed.time_points:
            data_subset.append(expected['conc'][expected['time'].index(time)])

        return time_series(observed.time_points,data_subset)

    def __subset_rate(self,expected,observed):

        """Return only the expected rate calculated for time of the observed rate"""

        return expected['rate'][expected['time'].index(observed.time)]

    def random_guess(self):

        """Return a random initial guess"""

        logging.info('Generating a random initial guess at the model parameters')

        #Make an empty list to hold the guesses
        initial_guess = []
        for i in range(len(self.session.model.kinpy_model.debug_k)):

            #Each guess is a random integer between 0 and 9
            #added to a random float between 0 and 1
            #and raised to a random exponent between -3 and 3
            
            integer = random.randint(0,9)
            float = random.random()
            exponent = random.randint(0,5) - 3
            
            initial_guess.append((integer+float)*10**exponent)

        logging.debug('Randomly generated parameters are: %s' % initial_guess)
        return initial_guess

    def threadsafe_callback(self,callback):
        #try:
        callback()
        #except:
        #    pass

class SaveObject():
    def __init__(self,session):
        self.name = session.name
        self.units = session.units
        self.directory = session.directory
        self.model_definition = session.model.definition
        self.solutions = session.solutions
        if session.data:
            self.data = session.data.save()
        else:
            self.data = False

class DataSaveObject():
    def __init__(self,data):
        self.id_counter = data.id_counter
        self.experiments = {}
        for xid in data.experiments:
            sexp = data.rate_importer.new_data_dictionary()
            for r in sexp:
                if isinstance(data.experiments[xid].data[r],rate_series):
                    sexp[r] = RateSeriesSaveObject(data.experiments[xid].data[r])
                else:
                    sexp[r] = data.experiments[xid].data[r]
            self.experiments[xid] = sexp

class RateSeriesSaveObject():
    def __init__(self,series):
        self.rates = series.rates
        self.time = series.time
        self.concentrations = series.concentrations
        self.starting_concentration = self.starting_concentration

class BeakerException(Exception):
    pass

class SilentException(Exception):
    pass

class solution():
    def __init__(self,solver_output,initial_guess):
        self.solution, self.fopt, self.iter, self.funcalls, self.warnflag = solver_output
        self.initial_guess = initial_guess
