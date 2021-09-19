# $language = "Python3"
# $interface = "1.0"
# =========================================================================
#
# Secure CRT Cisco Automation                       ||        ||
#                                                   ||        ||
# Script: m_template.py                            ||||      ||||
#                                              ..:||||||:..:||||||:..
# Author: Matthew Spangler                    ------------------------
#                                             C i s c o  S y s t e m s
# Version: 0.1
#
# Description: Use this as a template for making your own scripts.
#
# =========================================================================

import os
import sys
# A great module for parsing Cisco configs.
# Examples: https://github.com/mpenning/ciscoconfparse/tree/master/examples
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
from crt_automation.sessions import CrtSession
import crt_automation.utilities


# Main function and script logic here:
def main():
    # This class more or less wraps around SecureCRT's Python API.
    scrt = CrtSession(crt)

    # Session() instances correspond to individual tabs.
    for session in scrt.sessions:
        # Focus
        session.focus_tab()
        # Attempts to discover the OS and selects the corresponding "runner" class.
        session.start_cisco_session()
        # Raise exception if script is running on an incompatible OS
        session.validate_os(["IOS", "XE"])

        runner = session.runner

        # Used for get_command_output()
        runner.response_timeout = 5  # 5 seconds

        # Avoid "boilerplate" nastiness by using prebuilt functions to enter configuration modes:
        runner.priv_exec()

        # Examples of information we can retrieve:
        interface_summary = runner.show_intf_brief()
        mgmt_vrf = runner.get_mgmt_vrf()
        host = runner.get_hostname()

        # Get a list of interface names. We could do this with CiscoConfParse too, technically.
        names = runner.get_intf_names()

        # Convert interface abbreviation: Gi0 --> GigabitEthernet0
        interface = "Gi0"
        try:
            intf = crt_automation.utilities.long_int_from_int_list(interface, names)
        except:  # Gi0 may not be a valid interface on whatever device you're running this template on
            pass  # just keep going.

        runner.global_config()

        runner.goto_intf_config(interface)

        # Unlike get_command_output(), send() requires \r to send the command.
        runner.send("no shut \r")

        runner.priv_exec()

        # copy run start
        runner.save_changes()

        sh_run_output = session.runner.get_command_output("sh run | b interface")

        # Let's try using CiscoConfParse now!
        parse = CiscoConfParse(sh_run_output)
        # Return a list of all active interfaces (i.e. not shutdown)
        active_intfs = parse.find_objects_wo_child(r"^interf", r"shutdown")

    return


main()
