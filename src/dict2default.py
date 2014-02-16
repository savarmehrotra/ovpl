from collections import defaultdict

rec_dd = lambda: defaultdict(rec_dd)

def dict2default(mydict):
    mydefaultdict = defaultdict(rec_dd, mydict)
    for key in mydefaultdict.keys():
        if type(mydefaultdict[key]) == dict:
            mydefaultdict[key] = dict2default(mydefaultdict[key])
    return mydefaultdict