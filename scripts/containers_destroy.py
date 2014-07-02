import sh
import containers_list


def containers_destroy():
    containers_id=containers_list.get_containers_list()
    for index in range(0,len(containers_id)):
        var=raw_input("do u want to destroy "+ \
            str(containers_id[index]) + " [Y/N] :  ")
        if var == "Y" :
            CTID=containers_id[index]
            sh.vzctl.stop(CTID)
            sh.vzctl.destroy(CTID)
        elif var == "N" :
            pass



containers_destroy()
