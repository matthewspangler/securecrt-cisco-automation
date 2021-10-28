# $language = "Python3"
# $interface = "1.0"

import os
import sys
from ftplib import FTP
# A great module for parsing Cisco configs.
# Examples: https://github.com/mpenning/ciscoconfparse/tree/master/examples
from ciscoconfparse import CiscoConfParse

# Avoids errors in IDE's that can't detect the crt variable:
global crt

# Adds script directory to PYTHONPATH,
# so we can import local modules when running scripts from SecureCRT
script_dir = None
if 'crt' in globals():
    script_dir, script_name = os.path.split(crt.ScriptFullName)
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    script_dir, script_name = os.path.split(os.path.realpath(__file__))

# Local import
from common_tasks.cisco_scripts import CiscoScripts
from crt_automation.sessions import CrtSession


# Main function and script logic here:
def main():
    scrt = CrtSession(crt)
    # Discover OS:
    scrt.active_session.start_cisco_session()
    # Validate script is compatible with OS:
    scrt.active_session.validate_os(["IOS", "XE", "NXOS", "ASA", "WAAS"])
    # Make runner easier to type:
    runner = scrt.active_session.runner

    # Used for get_command_output()
    runner.response_timeout = 5  # 5 seconds

    scrt.message_box(runner.get_image_version())
    scrt.message_box(runner.get_model())

    return runner  # return OS class so we can run commands on it from other scripts, and see gathered information.


main()
