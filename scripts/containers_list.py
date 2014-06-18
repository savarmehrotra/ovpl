import sh
CTID=[]
containers_list=""

def get_containers_list():
    global CTID,containers_list
    CTID=[]
    containers_list=sh.vzlist("-a")
    container=containers_list.split("\n")
    container=container[1:]
    for index in range(len(container)-1):
        p=container[index].split()
        CTID.append(p[0])
    return CTID

def print_containers_list():
    global containers_list
    print containers_list


get_containers_list()
if __name__ == '__main__' :
    print_containers_list()

