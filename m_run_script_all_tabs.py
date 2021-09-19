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

from crt_automation.sessions import CrtSession
import crt_automation.scripting


def main():
    script_full_path = crt.Dialog.FileOpenDialog(title="Please select a script to run on all tabs",
                                                 filter="Python files (*.py)|*.py||")

    crt_automation.scripting.do_script_all_tabs(crt, script_full_path)


main()
