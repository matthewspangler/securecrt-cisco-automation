# $language = "Python3"
# $interface = "1.0"

import os
import sys

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

    # Avoid "boilerplate" nastiness by using prebuilt functions to enter configuration modes:
    net_os.priv_exec()

    net_os.write_output_to_file("show running-config", "running-config.txt")

    return net_os  # return OS class so we can run commands on it from other common_tasks, and see gathered information.


main()
