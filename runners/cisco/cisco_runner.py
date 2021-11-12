# $language = "Python3"
# $interface = "1.0"

from runners.common_runner import CommonRunner
import crt_automation.utilities
import socket
import struct
import re
import logging
from ciscoconfparse import CiscoConfParse
import time

# Logging configuration defined in common_runner.py
logger = logging.getLogger()


class CiscoRunner(CommonRunner):
    """
    Class containing common methods and functions used for interacting with Cisco OS's

    :var self.prompt:
            Contains the entire prompt. On Cisco devices, this is used to discover the configuration mode.
            It might be something like "Router(config)#" or "Switch>"
    :var self.prompt_regex: Regex for discovering the prompt
    :var self.mode: The canonical name of the configuration mode. Example: "Privileged EXEC"
    :var self.mode_prompt: The name of the mode as seen in the prompt. Example: "(config-if)"
    :var self.interfaces:
        set_interfaces() sets this variable to be a list of all interface names on the runners device
    :var self.line_matches:
        this variable is used for parsing shell output to determine if a command was successfully entered
    """

    def __init__(self, crt, current_tab=None):
        CommonRunner.__init__(self, crt, current_tab)
        self.crt.Screen.Synchronous = True
        self.crt.Screen.IgnoreEscape = True
        self.mode = None
        self.mode_prompt = None
        self.response_timeout = 5
        # Discovers prompts with '#' or '>' on Cisco devices.
        self.prompt_regex = re.compile(r'^.*#|^.*>')
        self.rommon_prompts = ['loader >', 'loader>', 'switch:', '>', '?']
        self.prompt = None
        self.set_prompt()
        self.line_matches = ["\r\n", '\r', '\n', '--More--']
        self.image_version = None
        self.model = None
        self.interfaces = None
        self.model_number = None
        self.config_register = None
        self.hostname = None
        # These variables save us from running '#sh run' and '#sh ver' multiple times:
        self.running_config = None
        self.startup_config = None
        self.show_version = None

    def __str__(self):
        return '<Class: CiscoRunner>'

    def set_running_config(self):
        self.running_config = self.get_command_output("show running-config")

    def get_model(self):
        self.model = self.get_output_as_str(
            "sh inv | i hassis").split(":")[2]

    def get_boot_vars(self):
        pass

    def check_model(self):
        pass

    def get_image_version(self):
        self.image_version = self.get_output_as_str(
            "sh ver | i Version").split("ersion ")[1].split(",")[0].split("\n")[0]
        return self.image_version

    def check_image_version(self):
        pass

    def set_prompt(self):
        """
        Method to set the self.prompt variable, which contains the entire prompt.
        It might be something like "Router(config)#" or "Switch>".
        On Cisco devices, this is used to discover the configuration mode.
        Keeping track of the prompt is important, it allows us to distinguish input from output.
        """

        result = ''
        attempts = 0
        while result == '' and attempts < 10:
            test_string = "\n!&%\b\b\b"
            self.current_tab.Screen.Send(test_string)
            result = self.current_tab.Screen.ReadString("!&%", self.response_timeout)
            attempts += 1
            logger.debug("<CONNECT> Attempt {0}: Prompt result = {1}".format(attempts, result))
            #time.sleep(0.1)

        prompt = result.strip(u"\r\n\b ")
        if prompt == '':
            try:
                screen_row = self.current_tab.Screen.CurrentRow + 0
                logger.debug("set_prompt(): screenrow = {}".format(screen_row))
                read_line = self.current_tab.Screen.Get(screen_row, 1, screen_row, 120)
                logger.debug("set_prompt(): read_line = {}".format(read_line))
                prompt = re.search(self.prompt_regex, read_line).group(0)
            except AttributeError:
                prompt = 'UNKNOWN'
                logger.debug("<GET PROMPT> Prompt discovery failed.  Raising exception.")
                raise Exception("Unable to discover device prompt")

        logger.debug("<GET PROMPT> Discovered prompt as '{0}'.".format(prompt))

        self.prompt = prompt
        logger.debug("self.prompt set to '{}'".format(self.prompt))
        return prompt

    def get_output_as_str(self, command):
        return '\n'.join(self.get_command_output(command))

    def write_output_to_file(self, command, file):
        self.set_prompt()
        full_output = self.prompt + command + '\r' + self.get_output_as_str(command)
        self.str_to_file(full_output, file)
        return full_output

    def str_to_file(self, multiline_string, file):
        with open(file, "a") as output:
            output.write(multiline_string + '\n')
            output.write('\n')

    def get_command_output(self, command):
        """
        Send a command to self.current_tab and wait for output. Return the output after seeing self.prompt shows.
        Sending commands with no output like "no shut" will cause this function to go into a timeout exception.
        Use send(command + "\r") instead for commands with no output. Consider changing self.response_timeout
        for commands that take a long time to output.
        :param command: the command to send to self.current_tab
        :return: the shell output of the command sent to self.current_tab
        """

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
                nextline = self.current_tab.Screen.ReadString(line_matches, self.response_timeout)
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
                    # TODO: make crt API wrapper and replace this send command:
                    self.current_tab.Screen.Send(" ")
                    logger.debug("MatchIndex is greater than 4. Usually this means we encountered a 'More' prompt.")
                else:
                    if self.skip_exceptions is False:
                        raise Exception("Timeout trying to capture output")
        except Exception as e:
            if self.skip_exceptions is False:
                self.crt.Dialog.MessageBox(str(e))
            logger.debug(e)
        return output

    # TODO: functions for moving between modes don't seem to always work. Sometimes we get stuck in user exec.
    def set_mode(self):
        """
        Method to discover the configuration mode of a Cisco device. Sets the variables self.mode and self.mode_prompt.
        :return:
            No return
        """
        mode = None
        mode_prompt = None
        if not self.prompt:
            self.set_prompt()
        if "(config)" in self.prompt:
            mode = "Global Configuration"
            mode_prompt = "(config)"
        elif "config-if" in self.prompt:
            mode = "Interface"
            mode_prompt = "(config-if)"
        elif "config-router" in self.prompt:
            mode = "Routing Engine"
            mode_prompt = "(config-router)"
        elif "config-line" in self.prompt:
            mode = "Line"
            mode_prompt = "(config-line)"
        elif ">" in self.prompt:
            mode = "User EXEC"
            mode_prompt = ">"
        else:
            if not "#" in self.prompt:
                if self.skip_exceptions is False:
                    raise Exception("Could not determine the current mode of this Cisco device!")
            else:
                mode = "Privileged EXEC"
                mode_prompt = "#"
        self.mode = mode
        logger.debug("self.mode set to {}".format(mode))
        self.mode_prompt = mode_prompt
        logger.debug("self.mode_prompt set to {}".format(mode_prompt))

    def user_exec(self):
        """
        Can enter user exec from any other mode.
        :return:
        """
        # TODO: make more efficient
        # TODO: current state of function gets stuck on enable passwords
        self.set_prompt()
        self.priv_exec()
        self.current_tab.Screen.Send("end \r")
        self.current_tab.Screen.WaitForString("end")
        self.current_tab.Screen.Send("exit \r")
        self.current_tab.Screen.WaitForString("RETURN")
        self.current_tab.Screen.Send("\r")
        self.current_tab.Screen.WaitForString(">")
        self.set_prompt()
        self.set_mode()
        if "User EXEC" in self.mode:
            logger.info("Entered User EXEC mode.")

    def global_config(self):
        """
        Can enter global config from any other mode.
        :return:
        """
        self.set_prompt()
        self.set_mode()
        if "#" in self.prompt:
            if "(config)" in self.mode_prompt:
                pass
            elif "(config-" in self.mode_prompt:
                self.send("exit \r")
            else:
                self.send("conf t \r")
        else:
            self.send("en \r")
            self.send("conf t \r")
        self.set_prompt()
        self.set_mode()
        if "Global Config" in self.mode:
            logger.info("Entered Global Configuration mode.")

    def priv_exec(self):
        """
        Can enter privileged exec from any other mode.
        :return:
        """
        self.set_prompt()
        self.set_mode()
        if self.mode_prompt == "(config)":
            self.send("exit \r")
        elif "(config-" in self.mode_prompt:
            self.send("exit \r")
            self.send("exit \r")
        elif self.mode_prompt == ">":
            self.send("en \r")
        else:
            if self.mode_prompt == "#":
                pass
            else:
                if self.skip_exceptions is False:
                    raise Exception("Could not enter Privileged EXEC!")
        self.set_prompt()
        self.set_mode()
        if "Privileged EXEC" in self.mode:
            logger.info("Entered Privilege EXEC mode.")

    def goto_intf_config(self, interface):
        """
        Can enter interface config mode from any other mode.
        :return:
        """
        self.set_prompt()
        self.set_mode()
        self.global_config()
        if "(config)" in self.mode_prompt:
            self.send("int {0} \r".format(interface))
        elif "#" in self.mode_prompt:
            self.send("int {0} \r".format(interface))
        else:
            self.send("en \r")
            self.send("int {0} \r".format(interface))
        self.set_prompt()
        self.set_mode()

    def show_intf_brief(self):
        """
        Returns a brief summary of all interfaces. Equivalent of "sh int br" or "sh ip int br"
        :return:
        """
        self.priv_exec()
        return self.get_command_output("sh ip int br")

    def get_intf_names(self):
        # TODO: gets wrong info if an interface has an IP, which seems to match the regex.
        """
        Returns a list of interfaces on the Cisco device -- just the names.
        :return: interface names in a list
        """
        intf_names = []
        if not self.running_config:
            self.set_running_config()
        parse = CiscoConfParse(self.running_config)
        for intf_obj in parse.find_objects('^interface'):
            # Remove the word "interface" from the names:
            intf_names.append(intf_obj.text.split("interface ")[1])
        logging.debug("Interface list: {}.".format(str(", ".join(intf_names))))
        return intf_names

    def set_interfaces(self):
        """
        Sets the self.interfaces variable to a list of all active interfaces on the Cisco device
        :return:
        """
        self.interfaces = self.get_intf_names()

    def set_intf_addr(self, ip_address, netmask=None, interface=None):
        """
        Sets an address on an interface.
        :param ip_address: can be an IP, hostname, or CIDR
        :param netmask: The netmask, not required if CIDR was passed to ip_address
        :param interface: The interface to set the address on
        """
        if interface:
            self.goto_intf_config(interface)
        if netmask is None:
            CIDR = ip_address
            ip, netmask = crt_automation.utilities.CIDR_to_IP_netmask(CIDR)
            self.send("ip addr {} {}".format(ip, netmask))
        else:
            self.send("ip addr {} {}".format(ip_address, netmask))

    def save_changes(self):
        """
        Sends "copy run start" or equivalents with boilerplate code for different OS's like XE, XR, etc.
        :return:
        """
        # TODO - write a version of this function for the XR class
        self.send("copy run start \r", "startup-config")
        self.send("\r")
        self.send("\r", "[OK]")
        # TODO - for some reason everything get stuck after saving, unless the prompt is set again:
        self.set_prompt()

    def enable_cdp_global(self):
        self.global_config()
        self.send("cdp run \r")

    def enable_cdp_intf(self, interface):
        self.goto_intf_config(interface)
        self.send("cdp enable \r")
        self.send("no shut \r")

    def get_copy_directory(self):
        dir_output = '\n'.join(self.get_command_output("dir | i :/"))
        # This regex matches stuff like: bootflash:/ flash:/ and harddisk:/
        matches = re.finditer(r"(\S+)\s*:/(?!\/)", dir_output, re.MULTILINE)
        results = []
        for match in matches:
            results.append(match.group())
        return results[0].split("/")[0]  # I decided to remove the '/' because it isn't necessary.

    def get_mgmt_vrf(self):
        """
        Returns the management vrf for the management interface
        :return:
        """
        # TODO - better parsing of the management vrf. Check what interface the vrf corresponds to using regex.
        mgmt_vrf_list = ["management",
                         "Mgmt-vrf",
                         "Mgmt-intf",
                         "mgmt",
                         "mgmtVrf"]
        sh_vrf = '\n'.join(self.get_command_output("sh vrf"))
        if sh_vrf is None:
            return None
        else:
            for vrf in mgmt_vrf_list:
                if vrf in sh_vrf:
                    return vrf
        return None
