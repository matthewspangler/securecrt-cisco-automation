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
    # Attempts to discover the OS and selects the corresponding "runner" class.
    scrt.active_session.start_cisco_session()
    # Raise exception if script is running on an incompatible OS
    scrt.active_session.validate_os(["IOS", "XE", "NXOS", "ASA"])
    # This makes it easier to type:
    runner = scrt.active_session.runner

    image_full_path = crt.Dialog.FileOpenDialog(title="Please select a Cisco configuration text file to upload.")

    config_file = open(image_full_path, "r")

    running_config = []
    for line in config_file:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        running_config.append(line_list)
    config_file.close()

    runner.global_config()
    for line in running_config:
        runner.send("{} \r".format(line))

    runner.priv_exec()

    runner.save_changes()

    return


main()
