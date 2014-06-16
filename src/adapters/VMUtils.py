""" Utilities for use in OVPL application. """

__all__ = [
    'get_ram_swap',
    'get_disk_space',
    'convert_to_megs',
    ]

import re
import sh

RAM = "256M"
RAM_MAX = "2048M"
SWAP = "512M"
SWAP_MAX = "4096M"
DISK_SOFT = "2G"
DISK_SOFT_MAX = "200G"
DISK_HARD_MUL = 1.5


def get_ram_swap(ram, swap):
    ram = convert_to_megs(ram)
    if ram == 0: 
        ram = convert_to_megs(RAM)
    elif ram > convert_to_megs(RAM_MAX): 
        ram = convert_to_megs(RAM_MAX) 
    ram = str(ram) + "M"
    swap = convert_to_megs(swap)
    if swap == 0: 
        swap = convert_to_megs(SWAP) 
    elif swap > convert_to_megs(SWAP_MAX): 
        swap = convert_to_megs(SWAP_MAX)
    swap = str(swap) + "M"
    return (ram, swap)

def get_disk_space(disk_soft):
    disk_soft = convert_to_megs(disk_soft)
    if disk_soft == 0: 
        disk_soft = convert_to_megs(DISK_SOFT)
    elif disk_soft > convert_to_megs(DISK_SOFT_MAX): 
        disk_soft = convert_to_megs(DISK_SOFT_MAX)
    disk_soft = int(disk_soft / 1024)       # Converting to Gigs
    disk_hard = disk_soft * DISK_HARD_MUL
    disk_soft = str(disk_soft) + "G"
    disk_hard = str(disk_hard) + "G"
    return (disk_soft, disk_hard)

def convert_to_megs(value):
    if not value:
        return 0
    value = value.strip()
    m = re.match(r'([0-9]+)\s*([a-zA-Z]+)', value)
    if m == None:
        return 0
    quantity = int(m.group(1))
    unit = m.group(2)
    if "G" in unit.upper():     # Gigabytes
        quantity = quantity * 1024
    elif "K" in unit.upper():   # Kilobytes
        quantity = int(quantity / 1024)
    elif "M" in unit.upper():   # Megabytes
        pass
    else:                       # Invalid unit
        return 0
    return quantity

def test():
    test_unit_conversion()
    test_ram_swap()
    test_disk_space()

def test_ram_swap():
    assert (RAM, SWAP) == get_ram_swap(None, None)
    assert (RAM, SWAP) == get_ram_swap(0, 0)
    assert ("100M", "150M") == get_ram_swap("100 mb", " 150MB")
    assert (RAM_MAX, SWAP_MAX) == get_ram_swap("100 Gigabytes", "100 gigs")

def test_disk_space():
    (disk_soft, disk_hard) = get_disk_space(None)
    assert disk_soft == DISK_SOFT

def test_unit_conversion():
    assert convert_to_megs(None) == 0
    assert convert_to_megs("100Mb") == 100
    assert convert_to_megs("1 Gig") == 1024
    assert convert_to_megs("1024 K") == 1
    assert convert_to_megs(" 1mb  ") == 1
    assert convert_to_megs("some-nonsense") == 0

if __name__ == '__main__':
    test()
