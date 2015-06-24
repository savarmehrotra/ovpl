class BaseAdapter:
    def create_vm(lab_spec):
        raise Exception("BaseAdapter: unimplemented create_vm()")

    def init_vm(vm_id, lab_repo_name):
        raise Exception("BaseAdapter: unimplemented init_()")
        # success status, response string
        return (False, "unimplemented")


import netaddr
import sh
import settings
import re
from utils.execute_commands import *
from utils.envsetup import EnvSetUp
import json
import os
VZCTL = "/usr/sbin/vzctl"
VZLIST = "/usr/sbin/vzlist -a"

def find_available_ip():
    # try and ping. if the IP does not respond, (gives wrong return code)
    # return the IP as free
    def is_ip_free(ip):
        try:
            sh.ping(str(ip), c=1)
        except sh.ErrorReturnCode:
            if is_ctid_free(str(ip)):
                return True
            else:
                return False
    def is_ctid_free(ip):
        m = re.match(r'[0-9]+.[0-9]+.([0-9]+).([0-9]+)', ip)
        vm_id = str(int(m.group(1) + m.group(2)))
        command = (r'ssh -o "%s" %s "%s %s| grep %s"' %
                   (settings.NO_STRICT_CHECKING,
                    settings.BASE_IP_ADDRESS,
                    VZLIST, vm_id, vm_id))
        logger.debug("CentOSVZAdapter: vzlist command = %s" %
                     command)
        """
        try:
            (ret_code, vzlist) = execute_command(command)
            if ret_code == 0:
                return False
            else:
                return True
        except Exception, e:
            #return True
            raise e
        """
        ret_code = os.system(command)
        if ret_code == 0:
            return False
        else:
            return True
            
    def is_ip_usable(ip):
            # reject IP's like  192.0.2.0 or 192.0.2.255 for subnet 192.0.2.0/24
            return not (ip == ip_network.network or ip == ip_network.broadcast)

    for subnet in settings.get_subnet():
        ip_network = netaddr.IPNetwork(subnet)
        ip_addrs = list(ip_network)
        # logger.debug("ip addresses: %s" % str(ip_addrs))
        for ip in ip_addrs:
            if is_ip_usable(ip) and is_ip_free(ip):
                return str(ip)

    raise Exception("unable to find free ip in subnet ", settings.get_subnet())
    return None
