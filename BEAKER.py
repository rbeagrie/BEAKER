"""BEAKER is an open source program designed for modelling enzymatic reactions."""

import os, logging, cPickle

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
            directory = os.path.expanduser('~\\BEAKER\\' + name)
        self.directory = directory

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
        
