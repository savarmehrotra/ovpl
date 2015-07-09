import netaddr
import sh
import re

from __init__ import *
from utils.envsetup import EnvSetUp
from utils.execute_commands import execute_command
from httplogging.http_logger import logger
import settings

VZCTL = "/usr/sbin/vzctl"
VZLIST = "/usr/sbin/vzlist -a"
OVPL_DIR_PATH = EnvSetUp.Instance().get_ovpl_directory_path()

class BaseAdapter:
    def create_vm(lab_spec):
        raise Exception("BaseAdapter: unimplemented create_vm()")

    def init_vm(vm_id, lab_repo_name):
        raise Exception("BaseAdapter: unimplemented init_()")
        # success status, response string
        return (False, "unimplemented")


class AdapterDetails:
    pass


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
        # to check vm_id is already exist or not
        m = re.match(r'[0-9]+.[0-9]+.([0-9]+).([0-9]+)', ip)
        vm_id = str(int(m.group(1) + m.group(2)))
        command = (r'ssh -o "%s" %s "%s %s| grep %s"' %
                   (settings.NO_STRICT_CHECKING,
                    settings.BASE_IP_ADDRESS,
                    VZLIST, vm_id, vm_id))
        logger.debug("CentOSVZAdapter: vzlist command = %s" %
                     command)
        try:
            (ret_code, vzlist) = execute_command(command)
            if ret_code == 0:
                return False
            else:
                return True
        except Exception:
            logger.debug("No container found with vm id = %s" % vm_id)
            return True

    def is_ip_usable(ip):
        #  reject IP's like  192.0.2.0 or 192.0.2.255 for subnet 192.0.2.0/24
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


def get_adapter_details():
    adapter_details = AdapterDetails()
    env = EnvSetUp.Instance()
    config_spec = env.get_config_spec()
    adapter_details.create_uri = \
        config_spec["VMPOOL_CONFIGURATION"]["ADAPTER_ENDPOINTS"]["CREATE_URI"]
    adapter_details.destroy_uri = \
        config_spec["VMPOOL_CONFIGURATION"]["ADAPTER_ENDPOINTS"]["DESTROY_URI"]
    adapter_details.restart_uri = \
        config_spec["VMPOOL_CONFIGURATION"]["ADAPTER_ENDPOINTS"]["RESTART_URI"]
    pool_id = config_spec["ADAPTER_TO_USE"]["POOLID"] - 1
    adapter_id = config_spec["ADAPTER_TO_USE"]["ADAPTERID"] - 1
    adapter_details.port = \
        config_spec["VMPOOL_CONFIGURATION"]["VMPOOLS"][pool_id]["PORT"]
    adapter_details.module_name = \
        config_spec["VMPOOL_CONFIGURATION"]["VMPOOLS"][pool_id]["ADAPTERS"][adapter_id]["MODULE"]
    adapter_details.adapter_name = \
        config_spec["VMPOOL_CONFIGURATION"]["VMPOOLS"][pool_id]["ADAPTERS"][adapter_id]["ADAPTER"]

    return adapter_details

if __name__ == '__main__':
    def test_find_available_ip():
        ip = find_available_ip()
        logger.debug("IP = %s" % ip)

    test_find_available_ip()
