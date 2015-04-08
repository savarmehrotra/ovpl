import sys
import os

ovpl_directory_path = os.path.dirname(os.path.abspath(__file__))
path_list = ovpl_directory_path.split("/")
path_list = path_list[:-1]  # remove 'tests' from the list
ovpl_directory_path = "/".join(path_list)
sys.path.insert(1, ovpl_directory_path)
