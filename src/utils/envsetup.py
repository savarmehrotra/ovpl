import os
import sys
print sys.path
import json
from adapters.settings import get_subnet
from singleton import Singleton


@Singleton
class EnvSetUp:
    __config_spec = None
    __ovpl_directory_path = None
    __http_proxy = None
    __https_proxy = None
    __no_proxy = ""

    def __init__(self):
        self.set_ovpl_directory_path()
        self.set_config_spec()
        self.setup_pythonpath()
        self.create_no_proxy_string()
        self.set_proxy_values()
        self.set_environment()

    def set_ovpl_directory_path(self):
        self.__ovpl_directroy_path = os.path.dirname(os.path.abspath(__file__))
        path_list = self.__ovpl_directroy_path.split("/")
        path_list = path_list[:-2]  # remove 'utils' and 'src' from the list
        self.__ovpl_directroy_path = "/".join(path_list)

    def set_config_spec(self):
        self.__config_spec = json.loads(open(self.__ovpl_directroy_path +
                                             "/config/config.json").read())

    def setup_pythonpath(self):
        sys.path.append(self.__ovpl_directroy_path)

    def create_no_proxy_string(self):

        for subnet in get_subnet():
            parts = subnet.split(".")
            parts[2] = parts[3] = "0"
            self.__no_proxy = ".".join(parts) + "/16,"

        self.__no_proxy += "localhost"

    def set_proxy_values(self):
        self.__http_proxy = self.__config_spec["ENVIRONMENT"]["HTTP_PROXY"]
        self.__https_proxy = self.__config_spec["ENVIRONMENT"]["HTTPS_PROXY"]

    def set_environment(self):
        os.environ["http_proxy"] = self.__http_proxy
        os.environ["https_proxy"] = self.__https_proxy
        os.environ["no_proxy"] = self.__no_proxy
        if "PYTHONPATH" in os.environ:
            if self.__ovpl_directroy_path not in os.environ["PYTHONPATH"]:
                os.environ["PYTHONPATH"] += ":"
                os.environ["PYTHONPATH"] += self.__ovpl_directroy_path
        else:
            os.environ["PYTHONPATH"] = self.__ovpl_directroy_path

    def get_config_spec(self):
        return self.__config_spec

    def get_ovpl_directory_path(self):
        return self.__ovpl_directroy_path

if __name__ == '__main__':
    env = EnvSetUp.Instance()
    print os.environ["http_proxy"]
    print os.environ["https_proxy"]
    print os.environ["no_proxy"]
    print os.environ["PYTHONPATH"]
    print "loc = " + (env.get_config_spec())["LABMANAGER_CONFIG"]["GIT_CLONE_LOC"]
