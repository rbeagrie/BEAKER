def sgn(bo):
    if bo:
        return -1
    else:
        return 1

def generate(input_file,output_file):

    st = open(input_file, "r").read()

    of = open(output_file, "w")

    chem_dict = {}
    reac_dict = {}
    i = -1
    j = -1

    R = True

    reac_list = []

    for line in st.splitlines():
        if line == '':
            continue
        elif line[0] == '#':
            continue
        else:
            reac = []
            mol_reac = []
            mol_prod = []
            prod = []
            rate_str = ""
            v_str = ""
            R = True
            N = False
            for term in line.split():
                if term == '+':
                    continue
                elif term == "<->":
                    R = False
                    continue
          
                mol_list = term.split("*")
                if len(mol_list) == 1:
                    mol_list = [1] + mol_list
                else:
                    mol_list = [int(mol_list[0])] + mol_list[1:]
                mol = mol_list[1]
                stoi = int(mol_list[0])
                
                if not chem_dict.has_key(mol):
                    i += 1
                    chem_dict.update({mol : i})
                    reac_dict.update({chem_dict[mol] : ""})

                if R:
                    reac.append(mol_list)
                    mol_reac.append(mol)
                else:
                    prod.append(mol_list)
                    mol_prod.append(mol)

            j += 1
            reac_args = list(set(mol_reac + mol_prod)) #Remove repeating elements
            
            rate_str = "v_" + str(j) + "("
            for term in reac_args:
                rate_str += "y[" + str(chem_dict[term]) + "], "        
            rate_str = rate_str[0:-2] + ")"

            for term in reac:
                reac_dict[chem_dict[term[1]]] += " -" + str(term[0]) + "*" + rate_str
                
            for term in prod:
                reac_dict[chem_dict[term[1]]] += " +" + str(term[0]) + "*" + rate_str

            v_str = "#" + line + "\n        "
            v_str += "v_" + str(j) + " = lambda "
            for term in reac_args:
                v_str += term + ", "
            v_str = v_str[0:-2] + " : "
            
            v_str += "k" + str(j) + " * "
        
            for term in reac:
                v_str += term[1] + "**" + str(term[0]) +  " * "
            v_str = v_str[0:-3]
                
            v_str += " - k" + str(j) + "r * "
            for term in prod:
                v_str += term[1] + "**" + str(term[0]) + " * "
            v_str = v_str[0:-3]

            v_str += "\n        k" + str(j) + " = k[" + str(j*2) + "]"
            v_str += "\n        k" + str(j) + "r = k[" + str(1+j*2) + "]"

            reac_list.append(v_str)

    ofstr = "from scipy import *\nimport scipy.integrate as itg\n\n"
    ofstr += "'''\n## Reaction ##\n\n"
    ofstr += st + "\n\n"

    ofstr += "## Mapping ##\n\n"

    chem_dict_r = {}
    for term in chem_dict:
        chem_dict_r.update({chem_dict[term] : term})

    for term in reac_dict:
        ofstr += chem_dict_r[term] + "\t" + str(term) + "\t" + reac_dict[term] + "\n"
    ofstr += "'''\n\n"

    ofstr += "class reaction_model():\n\n"
        
    ofstr += "    def dy(self, params, t):\n\n        y,k = params\n\n        "

    for term in reac_list:
        ofstr += term + "\n\n        "

    ost = "return array([\\\n        "

    for term in reac_dict:
        ost += reac_dict[term] + ",\\\n        "
        
    ost = ost[0:-3] + "    \\\n        ])"

    ofstr += ost

    ofstr += "\n\n    def __init__(self):\n\n        self.debug_y0 = array([\\\n        "        
    for n in range(0, i + 1):
        if n != i:
            ofstr += "#" + chem_dict_r[n] + "\n        "
            ofstr += "0.0,\\\n        "
        else:
            ofstr += "#" + chem_dict_r[n] + "\n        "
            ofstr += "0.0,\\\n        ])\n\n        "
    #ofstr = ofstr[0:-3] + "\\\n])"

    ofstr += "\n\n        self.debug_k = array([\\\n        "        
    for n in range(0, (j + 1)*2):
        if n != (j*2)+1:
            ofstr += "1.0,\\\n        "
        else:
            ofstr += "1.0,\\\n        ])\n\n        "

    ofstr += "\n\n        self.reactants = set(\n        "        
    for n in range(0, i + 1):
        if n != i:
            ofstr += "'" + chem_dict_r[n] + "',\n        "
        else:
            ofstr += "'" + chem_dict_r[n] + "')\n        "

    ofstr += "\n    def run(self,y0,k,t):\n\n        "

    ofstr += "return itg.odeint(dy, (y0,k), t)"

    #print ofstr
    of.write(ofstr)
    of.close()
            

        


