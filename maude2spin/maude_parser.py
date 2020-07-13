import subprocess
import re
import os 


direct = os.path.dirname(os.path.realpath(__file__))

default_timeout = -1
maude_file = direct + '/maude2spin.maude'
outfile = direct + '/output.txt'
maude_path = direct + '/Maude-3.0+yices2-linux/maude-Yices2.linux64'



def comm(program, cmd):
    proc = subprocess.Popen(['{} {} {}'.format(maude_path, program, cmd)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            cwd=direct)
    print('{} {} {}'.format(maude_path, program, cmd))

    return proc.communicate()[0]     

def process_solutions(output):
    solutions = output.decode('utf-8')

    print(solutions)

    split = re.search('result (.*?):', solutions).group(1)
    solutions = solutions.split('result {}:'.format(split), 1)[1]
    solutions = solutions.split('\nBye.\n', 1)[0]
    solutions = solutions.rstrip().lstrip()
    solutions = solutions.replace('\n', '').replace('    ', ' ')

    print(solutions)

    return solutions

def export_file(filename, terms):
    f = open(filename, "w")
    f.write(terms)
    f.close()

def parse(term):
    terms = 'rew in MAUDE2SPIN-FIRST-STEP : {} .'.format(term) 
    export_file(outfile, terms)
    output = comm(maude_file, outfile)
    output = process_solutions(output)

    terms = 'rew in MAUDE2SPIN-SECOND-STEP : {} .'.format(output) 
    export_file(outfile, terms)
    output = comm(maude_file, outfile)
    output = process_solutions(output)

    return output
