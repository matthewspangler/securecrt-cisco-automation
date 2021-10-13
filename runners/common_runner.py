# $language = "Python3"
# $interface = "1.0"

import os
import re
import logging
from logging.config import fileConfig

# Setup logging configuration
logger = logging.getLogger()
handler = logging.StreamHandler()
script_dir, script_name = os.path.split(os.path.realpath(__file__))
log_fname = os.path.join(script_dir, '../scrt_script.log')
file_handler = logging.FileHandler(log_fname)
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class CommonRunner:
    """
    Class containing common methods and functions used for interacting with
    ssh/telnet connections in SecureCRT. CommonRunner is OS agnostic, but subclasses could be OS specific.

    :param self.read_until:
        Used for the self.send_command function to differentiate user input from command output.
    """

    def __init__(self, crt, current_tab):
        self.crt = crt
        self.crt.Synchronous = True
        self.prompt = None
        self.current_tab = current_tab
        self.host = current_tab.Caption
        self.current_tab.Screen.Synchronous = True
        self.response_timeout = 5
        self.skip_exceptions = True
        # self.current_tab.Screen.IgnoreEscape = True
        self.user_id = os.environ.get('USERNAME')
        self.hostname = None
        self.read_until = "#"
        self.line_matches = ["\r\n", '\r', '\n', '--More--']

    def __str__(self):
        return '<Class: CommonRunner>'

    def is_connected(self):
        """
        Determines if the current tab has an active connection to a device.
        :return: a boolean representing whether the connection in the current tab is active or not
        """
        if self.current_tab.Session.Connected:
            return True
        else:
            return False

    def set_prompt(self):
        """
        Method to set the self.prompt variable, which contains the entire prompt.
        Keeping track of the prompt is important, it allows us to distinguish input from output.
        """
        result = ''
        attempts = 0
        while result == '' and attempts < 3:
            test_string = "\n!&%\b\b\b"
            self.current_tab.Screen.Send(test_string)
            result = self.current_tab.Screen.ReadString("!&%", self.response_timeout)
            attempts += 1
            logger.debug("<CONNECT> Attempt {0}: Prompt result = {1}".format(attempts, result))

        prompt = result.strip(u"\r\n\b ")
        if prompt == '':
            prompt = 'UNKNOWN'
            logger.debug("<GET PROMPT> Prompt discovery failed.  Raising exception.")
            raise Exception("Unable to discover device prompt")

        logger.debug("<GET PROMPT> Discovered prompt as '{0}'.".format(prompt))

        self.current_tab.Caption = prompt
        self.prompt = prompt
        logger.debug("self.prompt set to '{}'".format(self.prompt))
        return prompt

    def get_command_output(self, command):
        """
        Function to send a command to a device and return the output.

        :param command: the command to send to the current SecureCRT tab
        :type command: str
        :returns: the shell output of the command sent
        :rtype: str
        """
        # TODO - flesh out this function, return output as list, handle --more-- output.
        self.crt.Screen.Send(command + "\r\n")
        self.current_tab.Screen.WaitForString(command + "\r\n")

        # This will cause ReadString() to capture data until we see the szPrompt
        # value.
        output = self.current_tab.Screen.ReadString(self.read_until)

        # For testing - display the results in a messagebox:
        self.crt.Dialog.MessageBox(output)

        return output

    # TODO: write equivalent of send() and send_wait_for_strings() for this class - or for the Bash class.

    def crt_send(self, command):
        """
        Most basic send command, doesn't wait for output, simply logs the action.
        Basically wraps Send() function from SecureCRT API.
        This function is good for entering masked passwords,
        because it doesn't check if the command was entered/received.
        :param command:
        :return:
        """
        self.current_tab.Screen.Send(command)
        logger.debug("Sent command {} to device/tab.".format(command))

    def send(self, command, wait_for=None, timeout=None):
        """
        Simplified send command. Does not check for self.prompt, making it useful for
        switching between configuration modes when get_command_output() will get stuck!
        This function also doesn't have to wait for output like get_command_output() does,
        making it useful for IOS commands that have no output.
        This function either waits for wait_for or the command itself if no wait_for string is provided.
        This function does not work for sending masked passwords, use crt_send() instead.
        :param command: the command to send to self.current_tab
        :param wait_for: string to wait for in session output before continuing
        :return:
        """
        if timeout is None:
            timeout = self.response_timeout

        if wait_for is None:
            wait_for = command.strip()
            logger.debug("wait_for is '{}'".format(wait_for))
        if self.is_connected():
            self.crt_send(command)
            result = self.current_tab.Screen.WaitForString(wait_for, timeout)
            if not result:
                if self.skip_exceptions is False:
                    raise Exception("Timed out waiting for sent command to be echoed back to us.")
            else:
                return result
        else:
            if self.skip_exceptions is False:
                raise Exception("Session is not connected.  Cannot send command.")

    def send_wait_for_strings(self, command, wait_for_strings, timeout=None):
        """
        Pretty much the same as send() but you can wait until you see one of several strings instead of just one.
        :param command: the command to send to self.current_tab
        :param wait_for_strings: a list containing the strings to wait for
        :param timeout: the time in seconds to wait for the wait_for_strings
        :return: the index of the string found from of wait_for_strings, counting from 1. 0 means no strings were found.
        """
        result = 0

        if timeout is None:
            timeout = self.response_timeout

        if self.is_connected():
            self.crt_send(command)
            logger.debug("wait_for_strings are '{}'".format(','.join(wait_for_strings)))
            result = self.current_tab.Screen.WaitForStrings(wait_for_strings, timeout)
            if not result:
                if self.skip_exceptions is False:
                    raise Exception("Timed out waiting for sent command to be echoed back to us.")
            else:
                return result
        else:
            if self.skip_exceptions is False:
                raise Exception("Session is not connected.  Cannot send command.")

        return result

    def get_command_output(self, command):
        """
        Send a command to self.current_tab and wait for output. Return the output after seeing self.prompt shows.
        Sending commands with no output like "no shut" will cause this function to go into a timeout exception.
        Use send(command + "\r") instead for commands with no output. Consider changing self.response_timeout
        for commands that take a long time to output.
        :param command: the command to send to self.current_tab
        :param skip_exceptions: skips exceptions so that common_tasks are not paused until you close the message box
        :type skip_exceptions: bool
        :param timeout: time in seconds to wait for command output
        :return: the shell output of the command sent to self.current_tab
        """

        timeout = self.response_timeout
        skip_exceptions = self.skip_exceptions

        # RegEx to match the whitespace and backspace commands after --More-- prompt
        exp_more = r' [\b]+[ ]+[\b]+(?P<line>.*)'
        re_more = re.compile(exp_more)

        self.set_prompt()
        line_matches = [self.prompt] + self.line_matches

        output = []
        # Write the output to the specified file
        try:
            # Need the 'b' in mode 'wb', or else Windows systems add extra blank lines.
            self.send(command + "\r")
            logger.info("Command '{}' sent to device/tab.".format(command))

            # Loop to capture every line of the command.  If we get CRLF (first entry in our "endings" list), then
            # write that line to the file.  If we get our prompt back (which won't have CRLF), break the loop b/c we
            # found the end of the output.
            while True:
                nextline = self.current_tab.Screen.ReadString(line_matches, timeout)
                # If the match was the 1st index in the endings list -> \r\n
                if self.current_tab.Screen.MatchIndex == 0:
                    logger.debug("MatchIndex is 0. Timeout trying to capture input.")
                    # TODO: debugging/logging if this scope is reached
                    # TODO: gets stuck here on commands that show the next prompt with no output
                    if self.skip_exceptions is False:
                        raise Exception("Timeout trying to capture output")
                elif self.current_tab.Screen.MatchIndex == 1:
                    logger.debug("MatchIndex is 1. Successfully found prompt!")
                    # We got our prompt, so break the loop
                    break
                elif self.current_tab.Screen.MatchIndex <= 4:
                    # Strip newlines from front and back of line.
                    nextline = nextline.strip('\r\n')
                    # If there is something left, write it.
                    if nextline != "":
                        # Check for backspace and spaces after --More-- prompt and strip them out if needed.
                        regex = re_more.match(nextline)
                        if regex:
                            nextline = regex.group('line')
                        # Strip line endings from line.  Also re-encode line as ASCII
                        # and ignore the character if it can't be done (rare error on
                        # Nexus)
                        output.append(nextline.strip('\r\n'))
                    logger.debug("MatchIndex is less than or equal to 4. Append newline to output list.")
                elif self.current_tab.Screen.MatchIndex > 4:
                    # If we get a --More-- send a space character
                    self.crt_send(" ")
                    logger.debug("MatchIndex is greater than 4. Usually this means we encountered a 'More' prompt.")
                else:
                    if self.skip_exceptions is False:
                        raise Exception("Timeout trying to capture output")
        except Exception as e:
            if self.skip_exceptions is False:
                self.crt.Dialog.MessageBox(str(e))
            logger.debug(e)
        return output

    def send_spacebar(self):
        """
        Send a spacebar to SecureCRT. Useful for --More-- prompts.
        :return: empty
        """
        self.crt.Screen.Send(" ")
