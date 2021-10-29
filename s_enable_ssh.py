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
    net_os = scrt.active_session.runner



    return


main()
