# $language = "Python3"
# $interface = "1.0"

import os
import sys
import subprocess
import ipaddress
import platform
import socket
import struct

# A great module for parsing Cisco configs.
# Examples: https://github.com/mpenning/ciscoconfparse/tree/master/examples

# Avoids errors in IDE's that can't detect the crt variable:
global crt

# Adds script directory to PYTHONPATH,
# so we can import local modules when running common_tasks from SecureCRT
script_dir = None
if 'crt' in globals():
    script_dir, script_name = os.path.split(crt.ScriptFullName)
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    script_dir, script_name = os.path.split(os.path.realpath(__file__))

# Local import
from crt_automation.sessions import CrtSession
import crt_automation.utilities


def windows_pingtest(ip):
    """
    Pings through host OS, not in SecureCRT
    :param host: ip or hostname to ping
    :return:
    """
    try:
        output = subprocess.check_output(
            "ping -{} 1 {}".format('n' if platform.system().lower() == "windows" else 'c', ip), shell=True)
    except Exception as e:
        return False
    return True


def get_first_addr(cidr):
    """
    Find first usable address after the network address (often the default gateway address)
    :param cidr: the IP in CIDR format
    :return: first usable address on a subnet
    """
    return ipaddress.IPv4Network(cidr)[1]


def get_gateway(cidr):
    """
    Find the default gateway--assuming it's the first address.
    :param cidr: the IP in CIDR format
    :return: default gateway IP
    """
    return get_first_addr(cidr)


def cidr_to_netmask(cidr):
    """
    Converts CIDR format to [IP, netmask]
    :param cidr: the IP in CIDR format
    :return: A list with [IP, netmask]
    """
    network, net_bits = cidr.split('/')
    host_bits = 32 - int(net_bits)
    netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
    return network, netmask


def list_ip_in_range(cidr):
    return [str(ip) for ip in ipaddress.IPv4Network(cidr)]


def find_unused_ip(cidr):
    count = 0
    for ip in list_ip_in_range(cidr):
        # skip network address and default gateway:
        if count > 1:
            if not windows_pingtest(ip):
                return ip
        count += 1
    return None


def convert_cidr(cidr):
    available_ip = find_unused_ip(cidr)
    network, netmask = cidr_to_netmask(cidr)
    gateway = get_first_addr(cidr)
    return available_ip, netmask, network, gateway


def check_cidr(cidr):
    # TODO - implement this function
    return True


# Main function and script logic here:
def main():
    scrt = CrtSession(crt)
    # Discover OS:
    scrt.active_session.start_cisco_session()
    # Validate script is compatible with OS:
    scrt.active_session.validate_os(["IOS", "XE", "NXOS", "ASA", "WAAS"])
    # Make runner easier to type:
    net_os = scrt.active_session.runner

    # Used for get_command_output()
    net_os.response_timeout = 5  # 5 seconds

    # Switch to privileged exec mode:
    net_os.priv_exec()

    interface_list = net_os.get_intf_names()

    cidr = None
    valid_cidr = False
    while not valid_cidr:
        cidr = crt.Dialog.Prompt("Please enter a valid CIDR, ex: 192.168.1.0/24 ")
        if check_cidr(cidr):
            valid_cidr = True

    interface = None
    valid_interface = False
    while not valid_interface:
        interface = crt.Dialog.Prompt("Please enter a valid interface, ex: Gi1/1: ")
        # Convert interface abbreviation to full interface name:
        interface = crt_automation.utilities.long_int_from_int_list(interface, interface_list)
        if interface in interface_list:
            valid_interface = True

    net_os.goto_intf_config(interface)

    # NOTE: this command won't work correctly unless SecureCRT is on the same internal network as the Cisco device.
    # This is because it searches for unused IP's on the network through SecureCRT's host OS
    available_ip, netmask, network, gateway = convert_cidr(cidr)

    net_os.send("ip addr {0} {1} \r".format(available_ip, netmask))

    net_os.priv_exec()
    net_os.save_changes()


main()
