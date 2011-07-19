import scipy.integrate as itg

"""Bumpy is an open source program designed for modelling
enzymatic reactions."""

class model():

    """The bumpy model class holds a set of microscopic
    reactions that form a complete reaction system"""

    def __init__(self,input_file):

        """Initiate a new bumpy model"""

        self.system = {}
        self.species_mapping = False
        self.parameter_mapping = False
        self.dy_dict = False
        self.species = False
        self.parameters = False
        self.importer = importer(self,input_file)

    def fill_species(self):
        self.species = set()
        for reaction in self.system:
            for reactant in self.system[reaction].reactants:
                self.species.add(self.system[reaction].reactants[reactant].name)
            for product in self.system[reaction].products:
                self.species.add(self.system[reaction].products[product].name)

        self.species_mapping = {}
        
        for i,s in enumerate(list(self.species)):
            self.species_mapping[s] = i

    def fill_parameters(self):
        self.parameters = set()
        for reaction in self.system:
            self.parameters.add(str(self.system[reaction].r_id) + 'kf')
            self.parameters.add(str(self.system[reaction].r_id) + 'kr')

        self.parameter_mapping = {}
        
        for i,p in enumerate(list(self.parameters)):
            self.parameter_mapping[p] = i

    def dy(self, y, t, k):
        dy_array = []
        for i in range(len(y)):
            sp_dy = 0.0
            rates = self.dy_dict[i]
            for fw,order,r_id in rates:
                if fw:
                    sp_dy = sp_dy - self.system[r_id].rate(y,k)*order
                else:
                    sp_dy = sp_dy + self.system[r_id].rate(y,k)*order
            dy_array.append(sp_dy)
        return dy_array

    def run(self,y0,t,k):

        return itg.odeint(self.dy, y0, t, (k,))

class reaction():

    def __init__(self,r_id,model):

        self.reactants = {}
        self.products = {}
        self.parameters = []
        self.frate_dict = []
        self.rrate_dict = []
        self.model = model
        self.r_id = r_id

    def initiate_rates(self):
        for reactant in self.reactants:
            self.frate_dict.append(self.create_rate(self.reactants[reactant]))
        for product in self.products:
            self.rrate_dict.append(self.create_rate(self.products[product]))

    def create_rate(self,reactant):
        name = reactant.name
        order = reactant.order
        s_key = self.model.species_mapping[name]
        return lambda s: s[s_key]**order

    def rate(self,species,parameters):
        fp_key = self.model.parameter_mapping[str(self.r_id)+'kf']
        f_rate = parameters[fp_key]
        rp_key = self.model.parameter_mapping[str(self.r_id)+'kr']
        r_rate = parameters[rp_key]
        for f in self.frate_dict:
            f_rate = f_rate * f(species)
        for r in self.rrate_dict:
            r_rate = r_rate * r(species)
        return f_rate - r_rate

    def add_species(self,name,order,fw):
        if fw:
            self.reactants[name] = reactant(name,order)
        else:
            self.products[name] = reactant(name,order)

class reactant():

    def __init__(self,name,order):
        self.name = name
        self.order = order

class importer():

    def __init__(self,model,input_file):
        self.model = model
        raw_file = self.open_file(input_file)
        self.import_file(raw_file)
        self.model.fill_species()
        self.model.fill_parameters()
        self.fill_rates()
        self.fill_dy_dict()

    def open_file(self,input_file):
        return open(input_file, "r").read()

    def import_file(self,of):

        r_id = 0
        
        for line in of.splitlines():
            if line == '':
                continue
            elif line[0] == '#':
                continue
            else:

                new_reaction = reaction(r_id,self.model)
                Fw = True

                for term in line.split():
                    if term == '+':
                        continue
                    elif term == "<->":
                        Fw = False
                        continue
              
                    mol_list = term.split("*")
                    if len(mol_list) == 1:
                        new_reaction.add_species(mol_list[0],1,Fw)
                    else:
                        new_reaction.add_species(mol_list[1],int(mol_list[0]),Fw)

                self.model.system[r_id] = new_reaction
                r_id += 1

    def fill_rates(self):
        for reaction in self.model.system:
            self.model.system[reaction].initiate_rates()

    def fill_dy_dict(self):
        self.model.dy_dict = {}
        for species in self.model.species:
            key = self.model.species_mapping[species]
            self.model.dy_dict[key] = []
            for reaction in self.model.system:
                if species in self.model.system[reaction].reactants:
                    self.model.dy_dict[key].append((True,self.model.system[reaction].reactants[species].order,self.model.system[reaction].r_id))
                if species in self.model.system[reaction].products:
                    self.model.dy_dict[key].append((False,self.model.system[reaction].products[species].order,self.model.system[reaction].r_id))
                    
