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

    
class model_solver():
    def __init__(self,session):
        self.blank = 'placeholder'
