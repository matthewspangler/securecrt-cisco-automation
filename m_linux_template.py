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
from crt_automation.sessions import CrtSession


# Main function and script logic here:
def main():
    # This class more or less wraps around SecureCRT's Python API.
    scrt = CrtSession(crt)

    # Session() instances correspond to individual tabs.
    for session in scrt.sessions:
        # Focus
        session.focus_tab()
        # Attempts to discover the OS and selects the corresponding "runner" class.
        session.start_linux_session()
        # Raise exception if script is running on an incompatible OS
        session.validate_os(["Linux"])

        output = session.runner.get_command_output("ping 8.8.8.8 \r")
        scrt.message_box(output)

    return


main()
