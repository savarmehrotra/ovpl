# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" Representation of a VM specification. """

class VMSpec:
    """ Represents build and installation specifications of a VM. """
    def __init__(self, specs):
        # Temporarily setting defaults
        self.lab_ID = specs['lab_ID'] #"test99"
        self.os = specs.get('os', 'Ubuntu') #"Ubuntu"
        self.os_version = specs.get('os_version', '12.04') #"12.04"
        self.ram = specs.get('ram', '256M') #"256M"
        self.swap = specs.get('swap', '512M') #"512M"
        self.diskspace = specs.get('diskspace', '2G') #"2G"
