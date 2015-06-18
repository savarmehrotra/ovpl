import os
import sys

__all__ = ['set_import_search_path']


def set_import_search_path():
    # The assumption here is that this script is in the src directory
    # which is one directory above ovpl
    ovpl_directory_path = os.path.dirname(os.path.abspath(__file__))
    path_list = ovpl_directory_path.split("/")
    path_list = path_list[:-2]  # remove src - till ovpl
    ovpl_directory_path = "/".join(path_list)
    src_path = ovpl_directory_path + "/src"
    utils_path = src_path + "/utils"
    adapters_path = src_path + "/adapters"
    httplogging_path = src_path + "/httplogging"
    vmmanager_path = src_path + "/vmmanager"

    if ovpl_directory_path not in sys.path:
        sys.path.append(ovpl_directory_path)
    if src_path not in sys.path:
        sys.path.append(src_path)
    if utils_path not in sys.path:
        sys.path.append(utils_path)
    if adapters_path not in sys.path:
        sys.path.append(adapters_path)
    if httplogging_path not in sys.path:
        sys.path.append(httplogging_path)
    if vmmanager_path not in sys.path:
        sys.path.append(vmmanager_path)

set_import_search_path()
