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
import crt_automation.utilities


# Main function and script logic here:
def main():
    scrt = CrtSession(crt)
    for session in scrt.sessions:
        session.focus_tab()
        # Attempts to discover the OS and selects the corresponding "runner" class.
        session.start_cisco_session()
        # Raise exception if script is running on an incompatible OS
        session.validate_os(["IOS", "XE", "NXOS", "ASA", "WAAS"])

        nos = session.runner
        nos.priv_exec()
        interfaces = nos.get_intf_names()
        nos.enable_cdp_global()
        for intf in interfaces:
            nos.enable_cdp_intf(intf)
        nos.priv_exec()
        nos.set_prompt()
        nos.save_changes()

    scrt.end_sessions()

    return


main()
