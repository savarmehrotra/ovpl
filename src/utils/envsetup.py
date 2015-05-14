import os
import sys
import json
from src.adapters.settings import get_subnet
from src.singleton import Singleton


@Singleton
class EnvSetUp:
    config_spec = None
    ovpl_directory_path = None
    http_proxy = None
    https_proxy = None
    no_proxy = ""

    def __init__(self):
        self.set_ovpl_directory_path()
        self.set_config_spec()
        self.setup_pythonpath()
        self.create_no_proxy_string()
        self.get_proxy_values()
        self.set_environment()

    def set_ovpl_directory_path(self):
        self.ovpl_directory_path = os.path.dirname(os.path.abspath(__file__))
        path_list = self.ovpl_directory_path.split("/")
        path_list = path_list[:-2]  # remove 'utils' and 'src' from the list
        self.ovpl_directory_path = "/".join(path_list)

    def set_config_spec(self):
        self.config_spec = json.loads(open(self.ovpl_directory_path +
                                           "/config/config.json").read())

    def get_ovpl_directory_path(self):
        return self.ovpl_directory_path

    def setup_pythonpath(self):
        sys.path.append(self.ovpl_directory_path)

    def create_no_proxy_string(self):

        for subnet in get_subnet():
            parts = subnet.split(".")
            parts[2] = parts[3] = "0"
            self.no_proxy = ".".join(parts) + "/16,"

        self.no_proxy += "localhost"

    def get_proxy_values(self):
        self.http_proxy = self.config_spec["ENVIRONMENT"]["HTTP_PROXY"]
        self.https_proxy = self.config_spec["ENVIRONMENT"]["HTTPS_PROXY"]

    def set_environment(self):
        os.environ["http_proxy"] = self.http_proxy
        os.environ["https_proxy"] = self.https_proxy
        os.environ["no_proxy"] = self.no_proxy
        print os.environ["PYTHONPATH"]
        if "PYTHONPATH" in os.environ:
            if self.ovpl_directory_path not in os.environ["PYTHONPATH"]:
                os.environ["PYTHONPATH"] += ":"
                os.environ["PYTHONPATH"] += self.ovpl_directory_path
        else:
            os.environ["PYTHONPATH"] = self.ovpl_directory_path


if __name__ == '__main__':
    e = EnvSetUp.Instance()
#    print e.ovpl_directory_path
#    print e.no_proxy
#    print e.http_proxy
#    print e.https_proxy
    print os.environ["http_proxy"]
    print os.environ["https_proxy"]
    print os.environ["no_proxy"]
    print os.environ["PYTHONPATH"]
