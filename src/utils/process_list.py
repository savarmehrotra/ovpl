import subprocess

def list():
    l=[]
    p = subprocess.Popen('vzlist -a', shell=True, stdout=subprocess.PIPE,\
         stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        print line
        x=line.split()
        l.append(x[0])

list()
