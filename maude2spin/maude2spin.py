import subprocess
import re
import os 
import maude_parser

fields = ["id", "typ", "dst", "pt", "sw"]


packet_var_name = "p"
message_var_name = "m"
message_counter = 0
messages = {}
channels = set()


def getMessageId(policy):
    global message_counter
    if policy in messages:
        return messages[policy]
    else:
        message_counter += 1
        messages[policy] = "M{}".format(message_counter)
        return messages[policy]

def variable_typedef():
    term = "typedef Packet {\n"

    for v in fields:
        term += "\tint {};\n".format(v) 
    term += "}\n\n"
    
    term += "Packet {};\n\n".format(packet_var_name)

    return term

def channel_def():
    term = ""
    for c in channels:
        term += "chan {} = [0] of {{ mtype }};\n".format(c)
    for c in recursive_variables:
        term += "chan ch_{} = [0] of {{ mtype }};\n".format(c)

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

        term += "mtype {};\n".format(message_var_name)

        
        term += temp
        
        term += "ch_{} ! m\n".format(k)
        term += "}\n\n\n"
    
    return term

def parse2program(recursive_variables):
    term = ""

    variable_def = variable_typedef()

    proctypes = parse2proctype(recursive_variables)

    channels = channel_def()

    term = variable_def + channels + proctypes

    return term 


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
        print("asd")
        print(atom)
        print(atom[atom.find("<")+1:atom.find(">")].replace(' ', '').split(','))
        
        channel, policy = atom[atom.find("<")+1:atom.find(">")].replace(' ', '').split(',')
        message_var_id = getMessageId(policy)
        def_variable = True
        channel_name = channel + "_" + message_var_id
        channels.add(channel_name)

        term += "\t\t:: " + channel_name + " ? {} -> \n".format(message_var_name)
        for p in policy.replace(' ', '').split('.'):
            if "=" in p:
                term += "\t\t\tif\n "
                field, value = p.split('=')
                term +=  "\t\t\t:: " + packet_var_name + "." + field + " == " + value + " -> skip;\n"
                term +=  "\t\t\tfi;\n"
            elif "<-" in p:
                field, value = p.split('<-')
                term += "\t\t\t" + packet_var_name + "." + field + " = " + value + ";\n"
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
        channel, policy = atom[atom.find("<")+1:atom.find(">")].replace(' ', '').split(',')
        message_var_id = getMessageId(policy)
        def_variable = True
        channel_name = channel + "_" + message_var_id
        channels.add(channel_name)
        term +=  "\t\t" + channel_name + " ! m;\n"
    elif '@Recursive' in atom:
        name = atom[atom.find("<")+1:atom.find(">")].strip()
        term += "\t\t" + "run {}()".format(name) + ";\n"
        term += "\t\t" + "if\n"
        term +=  "\t\t:: ch_{} ? m -> skip;\n".format(name)
        term +=  "\t\tfi;\n"
    elif '=' in atom:
        term += "\t\tif\n "
        field, value = atom.split('=')
        term +=  "\t\t:: " + packet_var_name + "." + field + " == " + value + " -> skip;\n"
        term +=  "\t\tfi;\n"
    elif "<-" in atom:
        field, value = atom.split('<-')
        term += "\t\t" + packet_var_name + "." + field + " = " + value + ";\n"
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




if __name__ == "__main__":
    program = ["Switch1v1", "Switch2v1", "Switch3v1", "Switch4v1", "Switch5v1", "Switch6v1", 
               "C1v1", "C1v2", "C1v3", "C2v1", "C2v2", "C2v3", "recL"]

    program_channels = ["upS1", "upS2", "upS3", "upS4", "upS5", "upS6"]

    recursive_variables = {"Switch1v1": "pt = 2 . pt <- 4 . Switch1v1 + (upS1 ? zero) . Switch1v2",
                           "Switch1v2": "zero . Switch1v2 + (upS1 ? zero) . Switch1v2",
                           "Switch2v1": "pt = 12 . pt <- 14 . Switch2v1 + (upS2 ? zero) . Switch2v2",
                           "Switch2v2": "zero . Switch2v2 + (upS2 ? zero) . Switch2v2",
                           "Switch3v1": "zero . Switch3v1 + (upS3 ? zero) . Switch3v1 + (upS3 ? (pt = 1 . pt <- 3)) . Switch3v2",
                           "Switch3v2": "pt = 1 . pt <- 3 . Switch3v2 + (upS3 ? zero) . Switch3v1 + (upS3 ? (pt = 11 . pt <- 13)) . Switch3v2",
                           "Switch4v1": "zero . Switch4v1 + (upS4 ? zero) . Switch4v1 + (upS4 ? (pt = 11 . pt <- 13)) . Switch4v2",
                           "Switch4v2": "pt = 11 . pt <- 13 . Switch4v2 + (upS4 ? zero) . Switch4v1 + (upS4 ? (pt = 11 . pt <- 13)) . Switch4v2",
                           "Switch5v1": "pt = 6 . pt <- 7 . Switch5v1 + (upS5 ? (pt = 5 . pt <- 7)) . Switch5v2 + (upS5 ? zero) . Switch5v3",
                           "Switch5v2": "pt = 5 . pt <- 7 . Switch5v2 + (upS5 ? (pt = 5 . pt <- 7)) . Switch5v2 + (upS5 ? zero) . Switch5v3",
                           "Switch5v3": "zero . Switch5v3 + (upS5 ? (pt = 5 . pt <- 7)) . Switch5v2 + (upS5 ? zero) . Switch5v3",
                           "Switch6v1": "pt = 8 . pt <- 10 . Switch6v1 + (upS6 ? (pt = 8 . pt <- 9)) . Switch6v2 + (upS6 ? zero) . Switch6v3",
                           "Switch6v2": "pt = 8 . pt <- 9 . Switch6v2 + (upS6 ? (pt = 8 . pt <- 9)) . Switch6v2 + (upS6 ? zero) . Switch6v3",
                           "Switch6v3": "zero . Switch6v3 + (upS6 ? (pt = 8 . pt <- 9)) . Switch6v2 + (upS6 ? zero) . Switch6v3",
                           "recL": "pt = 3 . pt <- 5 . recL + pt = 4 . pt <- 6 . recL + pt = 7 . pt <- 8 . recL + pt = 9 . pt <- 11 . recL + pt = 10 . pt <- 12 . recL",
                           "C1v1": "upS1 ! zero",
                           "C1v2": "upS3 ! (pt = 1 . pt <- 3)",
                           "C1v3": "upS5 ! (pt = 5 . pt <- 7)",
                           "C2v1": "upS2 ! zero",
                           "C2v2": "upS4 ! (pt = 11 . pt <- 13)",
                           "C2v3": "upS6 ! (pt = 8 . pt <- 9)"}


    parsed_terms = {}
    for k, v in recursive_variables.items():
        parsed_terms[k] = maude_parser.parse(v)

    print(parsed_terms)

    pml_program = parse2program(parsed_terms)
    print(pml_program)
    print(messages)

    maude_parser.export_file("program.pml", pml_program)