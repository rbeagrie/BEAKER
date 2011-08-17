import scipy.integrate as itg
import re

"""Bumpy is an open source program designed for modelling
enzymatic reactions."""

class model():

    """The bumpy model class holds a set of microscopic
    reactions that form a complete reaction system"""

    def __init__(self):

        """Initiate a new bumpy model"""

        self.system = {}
        self.species_mapping = False
        self.parameter_mapping = False
        self.dy_dict = False
        self.species = False
        self.parameters = False
        self.importer = importer(self)

    def debug_variables(self):

        debug_k = []
        for i in range(len(self.parameters)):
            debug_k.append(1.0)
        self.debug_k = debug_k

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
        self.pstring = False
        self.frate_dict = []
        self.rrate_dict = []
        self.frate = False
        self.rrate = False
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
        
        f_rate = self.frate(parameters)
        r_rate = self.rrate(parameters)
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

    def __init__(self,model):
        self.model = model

    def import_file(self,input_file):
        raw_file = self.open_file(input_file)
        self.parse(raw_file)
        self.clean_up()

    def clean_up(self):
        self.model.fill_species()
        self.model.fill_parameters()
        self.fill_rates()
        self.fill_dy_dict()
        self.model.debug_variables()

    def import_definition(self,definition):
        self.parse(definition)
        self.clean_up()

    def open_file(self,input_file):
        return open(input_file, "r")

    def parse(self,definition):

        r_id = 0
        reac = False
        par = True
        params = set()
        
        for line in definition:
            if line == '':
                continue
            elif line[0] == '#':
                continue
            elif line[0] == '!':
                if not reaction:
                    continue
                params = params.union(self.get_params(r_id-1,line))
                self.model.system[r_id-1].pstring = line[1:]
                reac = False
                par = True
            else:
                if not par:
                    params = params.union(self.get_params(r_id-1))
                par = False
                reac = True
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
        if not par:
            params = params.union(self.get_params(r_id-1))
        self.model.parameters = params

    def get_params(self,r_id,line=False):
        params = set([str(r_id)+'kf',str(r_id)+'kr'])
        if line:
            line = line[1:]
            seps = ['+','-','/','*']
            stmts = line.split(';')
            for stmt in stmts:
                exps = stmt.split('=')
                if exps[0] == 'kf':
                    params = params - set([str(r_id)+'kf'])
                elif exps[0] == 'kr':
                    params = params - set([str(r_id)+'kr'])
                else:
                    continue
                s = re.split('[\*/+-]',exps[1])
                p = []
                for q in s:
                    if not self.test_param(q):
                        p.append(q)

                p = set(p)    
                if 'kf' in p:
                    p.add(str(r_id)+'kf')
                if 'kr' in p:
                    p.add(str(r_id)+'kr')
                p = p - set(['kf','kr'])
                params = params.union(p)
        
        return params

    def test_param(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False


    def fill_rates(self):
        for reaction in self.model.system:
            self.model.system[reaction].initiate_rates()
            if self.model.system[reaction].pstring:
                frate,rrate = self.parse_pstring(reaction,self.model.system[reaction].pstring)
            else:
                frate = self.default_frate(reaction)
                rrate = self.default_rrate(reaction)

            self.model.system[reaction].frate = frate
            self.model.system[reaction].rrate = rrate
            
    def default_frate(self,r_id):
        fp_key = self.model.parameter_mapping[str(r_id)+'kf']
        return lambda p: p[fp_key]
            
    def default_rrate(self,r_id):
        rp_key = self.model.parameter_mapping[str(r_id)+'kr']
        return lambda p: p[rp_key]

    def parse_pstring(self,r_id,pstring):
        frate = False
        rrate = False
        pexprs = pstring.split(';')
        for pexpr in pexprs:
            pstmts = pexpr.split('=')
            if pstmts[0] == 'kf':
                frate = self.parse_pexpr(r_id,pstmts[1])
            elif pstmts[0] == 'kr':
                rrate = self.parse_pexpr(r_id,pstmts[1])
        if not frate:
            frate = self.default_frate(r_id)
        if not rrate:
            rrate = self.default_rrate(r_id)

        return frate,rrate

    def parse_pexpr(self,r_id,pexpr):

        pexpr = pexpr.split('+',1)

        if len(pexpr) > 1:
            return self.k_add_gen(self.parse_pexpr(r_id,pexpr[0]),self.parse_pexpr(r_id,pexpr[1]))

        pexpr = pexpr[0].split('-',1)

        if len(pexpr) > 1:
            return self.k_sub_gen(self.parse_pexpr(r_id,pexpr[0]),self.parse_pexpr(r_id,pexpr[1]))

        pexpr = pexpr[0].split('*',1)

        if len(pexpr) > 1:
            return self.k_mult_gen(self.parse_pexpr(r_id,pexpr[0]),self.parse_pexpr(r_id,pexpr[1]))

        pexpr = pexpr[0].split('/',1)

        if len(pexpr) > 1:
            return self.k_div_gen(self.parse_pexpr(r_id,pexpr[0]),self.parse_pexpr(r_id,pexpr[1]))

        pexpr = pexpr[0]

        if self.test_param(pexpr):
            return lambda p:float(pexpr)

        if pexpr in ['kf', 'kr']:
            pexpr = str(r_id) + pexpr

        pkey = self.model.parameter_mapping[pexpr]

        return lambda p:p[pkey]

    def k_div_gen(self,a,b):
        return lambda p:a(p)/b(p)

    def k_mult_gen(self,a,b):
        return lambda p:a(p)*b(p)

    def k_sub_gen(self,a,b):
        return lambda p:a(p)-b(p)

    def k_add_gen(self,a,b):
        return lambda p:a(p)+b(p)

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
                    
