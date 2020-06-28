"""
TODO: 
1) Define message type.
"""

program = ["Switch1", "Switch2", "Switch3", "Switch4", "Switch5v1", "Switch5v2", "Switch6v1", "Switch6v2"]


fields = ["pt"]
 


#recursive_variables = {"@R(L)": "pt = 3 . pt <- 5 . @R(L) + pt = 4 . pt <- 6 . @R(L)"}

#recursive_variables = {"@Recursive< L >": "ifBlock[sequence[pt = 10 :seq: (pt <- 12 :seq: (@Send< X,pt = 2 . pt <- 1 > :seq: @Recursive< L >))] :if: (sequence[pt = 9 :seq: (pt <- 11 :seq: @Recursive< L >)] :if: (sequence[pt = 7 :seq: (pt <- 8 :seq: @Recursive< L >)] :if: (sequence[pt = 3 :seq: (pt <- 5 :seq: (@Receive< upS1,pt = 2 . pt <- 19 > :seq: @Recursive< L >))] :if: sequence[pt = 4 :seq: (pt <- 6 :seq: @Recursive< L >)])))]"}
#recursive_variables = {"Switch1v1": "ifBlock[sequence[@Receive< upS1, zero > :seq: @Recursive< Switch1v3 >] :if: (sequence[pt = 2 :seq: (pt <- 4 :seq: @Recursive< Switch1v1 >)] :if: sequence[@Receive< upS1,pt = 1 . pt <- 3 > :seq: @Recursive< Switch1v2 >])]"}

"""
recursive_variables = {"Switch1": "ifBlock[@Receive< upS1,zero > :if: sequence[pt = 2 :seq: (pt <- 4 :seq: @Recursive< Switch1 >)]]",
                       "Switch2": "ifBlock[@Receive< upS2,zero > :if: sequence[pt = 12 :seq: (pt <- 14 :seq: @Recursive< Switch2 >)]]",
                       "Switch3": "ifBlock[one :if: @Receive< upS3,pt = 1 . pt <- 3 >]",
                       "Switch4": "ifBlock[one :if: @Receive< upS4,pt = 11 . pt <- 13 >]",
                       "Switch5v1": "ifBlock[sequence[pt = 6 :seq: (pt <- 7 :seq: @Recursive< Switch5v1 >)] :if: sequence[@Receive< upS5,pt = 5 . pt <- 7 > :seq: @Recursive< Switch5v2 >]]",
                       "Switch5v2": "sequence[pt = 5 :seq: (pt <- 7 :seq: @Recursive< Switch5v2 >)]",
                       "Switch6v1": "ifBlock[sequence[pt = 8 :seq: (pt <- 10 :seq: @Recursive< Switch6v1 >)] :if: sequence[@Receive< upS6,pt = 8 . pt <- 9 > :seq: @Recursive< Switch6v2 >]]",
                       "Switch6v2": "sequence[pt = 8 :seq: (pt <- 9 :seq: @Recursive< Switch6v2 >)]"}
"""

recursive_variables = {"C1v1": "@Send< upS1, pt = 2 . pt <- 1 > "}

#components = [x.strip() for x in program.split('||')]



expression = ""
with open("input.txt") as file:
    expression = file.read()



message_var_name = "m"
message_counter = 0
messages = {}

def getMessageId(policy):
    global message_counter
    if policy in messages:
        return messages[policy]
    else:
        message_counter += 1
        messages[policy] = "M{}".format(message_counter)
        return messages[policy]


channels = set()     

def variable_typedef():
    term = "typedef Message {\n"
    for v in fields:
        term += "\tint test_{}\n".format(v)
        term += "\tint assign_{}\n".format(v)
    term += "};\n\n"

    for v in fields:
        term += "int {};\n".format(v) 
    term += "\n\n"

    return term

def channel_def():
    term = ""
    for c in channels:
        term += "chan {} = [0] of {{ Message }};\n".format(c)

    term += "\n\n"
    return term

def parse2proctype(recursive_variables):
    term = ""
    for k, i in recursive_variables.items():
        if k in program:
            term += "active proctype {}() {{\n".format(k)
        else:
            term += "proctype {}() {{\n".format(k)

        temp, variables = prefix_parser(i)

        if variables:
            term += "Message {};\n".format(message_var_name)

        
        term += temp + "}\n\n\n"
    

    return term

def parse2program(recursive_variables):
    term = ""

    variable_def = variable_typedef()

    proctypes = parse2proctype(recursive_variables)

    channels = channel_def()


    term = variable_def + channels + proctypes
    print(term)



def prefix_parser(expression):
    operators = ['_=_', '_+_', '_._', '_<-_', '_!_', '_?_']
    tags = ['@Channel', '@Recursive', '@Field']

    term = ""
    temp = expression

    if 'ifBlock' in temp[:temp.find("[")]:
        summands = [x.strip().replace('(','').replace(')','') for x in temp[temp.find("[")+1:temp.rfind(']')].split(':if:')] 
        term, variables = create_if_block(summands)
    elif 'sequence' in temp[:temp.find("[")]:
        components = [x.strip().replace('(','').replace(')','') for x in temp[temp.find("[")+1:temp.rfind(']')].split(':seq:')] 
        term, variables = create_seq_block(components)
    else:
        term, variables = parse_atoms(temp)
    return term, variables


def parse_atoms(atom):
    term = ""
    def_variable = False

    if "@Receive" in atom:
        term += "\t\tif\n"
        channel, policy = atom[atom.find("<")+1:atom.find(">")].strip().split(',')
        message_var_id = getMessageId(policy)
        def_variable = True
        channel_name = channel + "_" + message_var_id
        channels.add(channel_name)

        term += "\t\t:: " + channel_name + " ? {} -> \n".format(message_var_name)
        for p in policy.replace(' ', '').split('.'):
            if "=" in p:
                term += "\t\t\tif\n "
                field, value = p.split('=')
                term +=  "\t\t\t:: " + field + " == " + value + " -> skip;\n"
                term +=  "\t\t\tfi;\n"
            elif "<-" in p:
                field, value = p.split('<-')
                term += "\t\t\t" + field + " = " + value + ";\n"
            elif "zero" in p:
                term += "\t\t\tif\n "
                term +=  "\t\t\t:: false -> skip;\n"
                term +=  "\t\t\tfi;\n"
            elif "one" in p:
                term += "\t\t\tif\n "
                term +=  "\t\t\t:: true -> skip;\n"
                term +=  "\t\t\tfi;\n"
        term +=  "\t\tfi;\n"
    elif "@Send" in atom:
        channel, policy = atom[atom.find("<")+1:atom.find(">")].strip().split(',')
        message_var_id = getMessageId(policy)
        def_variable = True
        channel_name = channel + "_" + message_var_id
        channels.add(channel_name)

        term += "\t\tatomic{" 
        for p in policy.replace(' ', '').split('.'):
            if "=" in p:
                field, value = p.split('=')
                term += "{}.test_{} = {}; ".format(message_var_name, field, value)
            elif "<-" in p:
                field, value = p.split('<-')
                term += "{}.assign_{} = {}; ".format(message_var_name, field, value)
        term +=  channel_name + " ! m };\n"
    elif '@Recursive' in atom:
        name = atom[atom.find("<")+1:atom.find(">")].strip()
        term += "\t\t" + "run {}()".format(name) + ";\n"
    elif '=' in atom:
        term += "\t\tif\n "
        field, value = atom.split('=')
        term +=  "\t\t:: " + field + " == " + value + " -> skip;\n"
        term +=  "\t\tfi;\n"
    elif "<-" in atom:
        field, value = atom.split('<-')
        term += "\t\t" + field + " = " + value + ";\n"
    elif "zero" in atom:
        term += "\t\tif\n "
        term +=  "\t\t:: false -> skip;\n"
        term +=  "\t\tfi;\n"
    elif "one" in atom:
        term += "\t\tif\n "
        term +=  "\t\t:: true -> skip;\n"
        term +=  "\t\tfi;\n"

    return term, def_variable

def create_if_block(elements):
    def_variable = False

    term = "if\n"
    for x in elements:
        term += ":: true ->\n"
        if 'sequence' in x[:x.find("[")]:
            atoms = [x.strip().replace('[','').replace(']','') for x in x[x.find("["):].split(':seq:')]
            for i, a in enumerate(atoms):
                temp_term, temp_def_variable = parse_atoms(a)
                if temp_def_variable == True:
                    def_variable = True
                term += temp_term
        else:
            temp_term, temp_def_variable = parse_atoms(x)
            if temp_def_variable == True:
                def_variable = True
            term += temp_term

    term += "fi;\n"
    return term, def_variable

def create_seq_block(atoms):
    def_variable = False
    term = ""
    for i, a in enumerate(atoms):
        temp_term, temp_def_variable = parse_atoms(a)
        if temp_def_variable == True:
            def_variable = True
        term += temp_term

    term += "\n"
    return term, def_variable

#prefix_parser(expression)
parse2program(recursive_variables)