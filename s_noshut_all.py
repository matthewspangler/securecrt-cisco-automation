# $language = "Python3"
# $interface = "1.0"

import os
import sys
from ciscoconfparse import CiscoConfParse

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
import runners
from crt_automation.sessions import CrtSession
from crt_automation.utilities import expand_int_range

# Main function and script logic here:
def main():
    # This class more or less wraps around SecureCRT's Python API.
    scrt = CrtSession(crt)
    # Attempts to discover the OS and selects the corresponding "runner" class.
    scrt.active_session.start_cisco_session()
    # Raise exception if script is running on an incompatible OS
    scrt.active_session.validate_os(["IOS", "XE", "NXOS", "ASA", "WAAS"])
    # Make runner easier to type:
    nos = scrt.active_session.runner

    int_ranges = nos.crt.Dialog.Prompt("Please write interface ranges separated by spaces "
                                       "(syntax example: 'Gi1/1-4,6 Te1/1-5),"
                                       "or hit [enter] to run on all interfaces: ").split(" ") or None

    input_commands = nos.crt.Dialog.Prompt("Type any additional commands to enter for each interface, "
                                           "separated by commas: ") or None

    nos.priv_exec()

    # All interfaces
    if not int_ranges:
        interfaces = nos.get_intf_names()
        nos.set_prompt()
        nos.global_config()
        for intf_obj in interfaces:
            nos.send("int {} \r".format(intf_obj))
            nos.send("no shut \r")
            if input_commands is not None:
                for command in input_commands.split(","):
                    nos.send("{} \r".format(command))
    else:  # Interface ranges
        for range in int_ranges:
            nos.set_prompt()
            nos.global_config()
            int_list = expand_int_range(range)
            for int in int_list:
                nos.send("int {} \r".format(int))
                nos.send("no shut \r")
                if input_commands is not None:
                    for command in input_commands.split(","):
                        nos.send("{} \r".format(command))

    nos.priv_exec()
    nos.set_prompt()
    nos.save_changes()

    return


main()
