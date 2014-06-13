import subprocess

def destroy():
    l=[]
    p=subprocess.Popen('vzlist -a', shell=True, stdout=subprocess.PIPE,\
         stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        x=line.split()
        l.append(x[0])
    l=l[1:]
    for i in range(0,len(l)):
        var=raw_input("do u want to destroy "+str(l[i]) +" [Y/N] :  ")
        if var == "Y" :
            m='vzctl stop ' + str(l[i])
            k='vzctl destroy ' + str(l[i])
            n=subprocess.call(m,shell=True)
            q= subprocess.call(k,shell=True)

        elif var == "N" :
            pass


destroy()
