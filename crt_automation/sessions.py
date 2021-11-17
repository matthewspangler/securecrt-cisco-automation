# Anything for working with multiple tabs or SecureCRT in general goes in this class.

import runners
import logging
import os
import toml
import time
from runners.common_runner import CommonRunner
from runners.cisco.cisco_runner import CiscoRunner
from runners.nix import LinuxRunner
import runners.cisco
import crt_automation.utilities


class CrtSession:
    def __init__(self, crt):
        self.crt = crt
        self.sessions = self.get_all_sessions()
        # Sessions loosely represent tabs, although a device can be reassigned to a different tab.
        self.active_session = self.get_active_sessions()
        self.initial_tab = self.crt.GetScriptTab()

    def cleanup(self):
        pass

    def get_active_sessions(self):
        # TODO: if sessions list is empty...
        active_tab_index = self.__get_focused_tab_index()
        for session in self.sessions:
            if session.tab_index is active_tab_index:
                return session
        return None

    def __get_focused_tab_index(self):
        return self.crt.GetScriptTab().Index

    def __get_tab_count(self):
        return self.crt.GetTabCount()

    def set_active_session(self, session=None):
        if not session:
            self.active_session = self.get_active_sessions()
        else:
            self.active_session = session
            self.active_session.focus_tab()

    def get_script_tab(self):
        return self.crt.GetScriptTab()

    def get_all_sessions(self):
        session_list = []
        initial_tab = self.crt.GetScriptTab()
        for i in range(1, self.crt.GetTabCount() + 1):
            tab = self.crt.GetTab(i)
            tab.Activate()
            tab_session = Session(self.crt, tab)
            tab_session.tab_index = i
            session_list.append(tab_session)
        initial_tab.Activate()
        return session_list

    def open_new_tab(self):
        pass

    def close_session(self, session):
        active_tab_index = self.__get_focused_tab_index()
        i = 0
        for session in self.sessions:
            i += 1
            if session.tab_index is active_tab_index:
                session.tab.Close()
                self.sessions.pop(i)

    def focus_session(self, session):
        session.tab.Activate()
        self.active_session = session

    def focus_next_session(self):
        focus_index = self.__get_focused_tab_index() + 1
        for session in self.sessions:
            if session.tab_index is focus_index:
                self.focus_session(session)

    def focus_previous_session(self):
        focus_index = self.__get_focused_tab_index() + 1
        for session in self.sessions:
            if session.tab_index is focus_index:
                self.focus_session(session)

    def focus_session_by_index(self, index):
        session = self.sessions[index + 1]  # assuming count starts from 0
        self.focus_session(session)

    def focus_session_by_tab_label(self, name):
        for n_tab_index in range(1, self.crt.GetTabCount() + 1):
            tab = self.crt.GetTab(n_tab_index)
            if tab.Caption == name:
                return self.get_session_by_index(n_tab_index + 1)  # assuming count starts from 0
        return None

    def get_session_by_index(self, index):
        for session in self.sessions:
            if session.tab_index == index:
                return session
        return None

    def message_box(self, message):
        """
        Wrapper for crt.Dialog.MessageBox()
        :param message:
        :return:
        """
        self.crt.Dialog.MessageBox(message)

    def prompt(self, message):
        """
        Wrapper for crt.Dialog.Prompt()
        :param message:
        :return:
        """
        return self.crt.Dialog.Prompt(message)

    def file_open_dialog(self, title, extension_filter=None, button_label=None, default_filename=None):
        """
        Wrapper for crt.Dialog.FileOpenDialog()
        :param title:
        :param extension_filter:
        :param button_label:
        :param default_filename:
        :return:
        """
        return self.crt.Dialog.FileOpenDialog(title=title,
                                              filter=extension_filter,
                                              button_label=button_label,
                                              default_filename=default_filename)


class Session:
    def __init__(self, crt, tab):
        self.crt = crt
        self.tab = tab
        self.screen = tab.Screen
        self.session = tab.Session
        self.script = None
        self.os = None
        self.host = tab.Caption
        # TODO - don't set this to a Cisco runner, in case we are working with bash.
        self.runner = CiscoRunner(self.crt, tab)
        self.remote_ip = "0.0.0.0"
        self.enable_pass = ''
        self.username = ''
        self.password = ''
        self.hostname = None
        self.tab_name = None
        self.tab_index = None
        self.term_len = None
        self.term_width = None
        self.logger = logging.getLogger()

    def set_os(self):
        pass

    def set_name(self):
        pass

    def set_tab_by_focused(self):
        self.tab = self.crt.GetScriptTab()

    def set_tab_by_index(self, index):
        self.tab = self.crt.GetTab(index)

    def set_tab_by_label(self):
        # TODO - implement
        pass

    def focus_tab(self):
        if self.tab is None:
            raise Exception("Please set the tab before trying to focus it.")
        self.tab.Activate()

    def end_session(self):
        pass

    def close_tab(self):
        pass

    def connect(self, host=None):
        if self.is_connected():
            return

    def disconnect(self):
        self.screen.Synchronous = False
        self.screen.IgnoreEscape = False
        try:
            self.session.Unlock()
        except Exception:
            pass

    def is_connected(self):
        """
        Determines if the current tab has an active connection to a device.
        :return: a boolean representing whether the connection in the current tab is active or not
        """
        if self.tab.Session.Connected:
            return True
        else:
            return False

    def validate_os(self, os_list, raise_exception=True):
        """
        Check this device's OS against a list of OS's to verify a script's compatibility.
        :param os_list: A list of compatible OS's. Valid options: Linux, IOS, XE, NXOS, XR, ASA, WAAS. Case insensitive.
        :param raise_exception: If this flag is True, an exception is raised.
        :return: True bool if OS was found in list, otherwise False
        """
        if not self.runner:
            if raise_exception:
                raise Exception("You need to run start_session() or "
                                "start_cisco_session() before running validate_os().")
            return False
        if not self.os:
            if raise_exception:
                raise Exception("Could not find self.device_type")
            return False
        if self.os.lower() in [os.lower() for os in os_list]:  # converts os_list to lowercase
            return True
        else:
            if raise_exception:
                raise Exception("Incompatible operating system. "
                                "This script is not designed to run on {}!".format(self.os))
            return False

    def cisco_login(self):
        pass

    def cisco_enable_pass(self):
        # TODO
        pass

    def start_linux_session(self):
        """
        Sets self.runner to an instance of the bash class
        :return:
        """
        self.os = "Linux"
        self.runner = LinuxRunner(self.crt, self.tab)
        self.runner.set_prompt()

    def attempt_login(self, runner):
        login_waitfors = ["ogin",
                          "sername",
                          "assword",
                          "incorrect",
                          "#",
                          ">"]
        login_timeout = 5
        runner.current_tab.Screen.Send("\r")
        result = runner.current_tab.Screen.WaitForStrings(login_waitfors, login_timeout)
        max_attempts = 5
        count = 1
        while result < 4:
            if count > max_attempts:
                break
            result = runner.current_tab.Screen.WaitForStrings(login_waitfors, login_timeout)
            time.sleep(1)
            if result <= 2:
                runner.current_tab.Screen.Send("{}\r".format(self.username))
                runner.current_tab.Screen.WaitForString(":", 20)
                time.sleep(1)
                runner.current_tab.Screen.Send("{}\r".format(self.password))
                time.sleep(1)
            elif result == 3:
                runner.current_tab.Screen.Send("\r")
                runner.current_tab.Screen.Send("{}\r".format(self.password))
                time.sleep(1)
            elif result >= 5:
                break
            elif result == 0:
                break
            count += 1

        if result == 4:  # If password is still incorrect after max attempts reached:
            raise Exception("Failed to login!")

    def start_cisco_session(self, attempt_login=True, enable_pass=None, timeout=5):
        """
        Discovers the Cisco OS, sets self.runner to an instance of a runner class, and sets the prompt.
        :return:
        """
        if not self.is_connected():
            raise Exception("Session is not connected.  Cannot start Cisco device.")

        # Lock tab to prevent keystrokes sending data
        try:
            self.session.Lock()
        except Exception:
            pass

        if not self.screen.Synchronous:
            self.screen.Synchronous = True
            # TODO: next line seemed to break scripts on Nexus devices:
            # self.screen.IgnoreEscape = True

        if enable_pass:
            self.enable_pass = enable_pass

        # TODO - code for enable passwords, usernames and passwords

        # Use this runner until we discover the network OS type
        temp_runner = runners.CiscoRunner(self.crt, self.tab)

        if attempt_login:
            self.attempt_login(temp_runner)

        # Discover the prompt so we can parse output
        temp_runner.set_prompt()

        if ">" in temp_runner.prompt:  # enter priv exec from user exec
            temp_runner.send("en \r")
            temp_runner.current_tab.Screen.WaitForString("en", timeout)
            temp_runner.set_prompt()
        while ")#" in temp_runner.prompt:  # exit configuration modes
            temp_runner.send("exit \r")
            temp_runner.current_tab.Screen.WaitForString("exit", timeout)
            temp_runner.set_prompt()

        # Check for ROMMON:
        if temp_runner.prompt in temp_runner.rommon_prompts:
            temp_runner.send("help\r")
            result = temp_runner.send_wait_for_strings("help\r", ["boot", "Invalid"])
            if result == 0:
                pass
            if result == 1:
                self.runner = runners.cisco.ROMMON(self.crt, self.tab)
                self.os = "ROMMON"
            if result == 2:
                pass
        else:  # Not ROMMON
            os_waitfors = [
                "IOS",
                "NX-OS",
                "XR",
                "ASA",
                "WAAS"
            ]
            result = temp_runner.send_wait_for_strings("sh ver | i Cisco \r", os_waitfors)

            if result == 0:
                self.runner = CiscoRunner(self.crt, self.tab)
                self.os = "UNKNOWN"
            if result == 1:
                self.runner = runners.cisco.XE(self.crt, self.tab)
                self.os = "XE"
            if result == 2:
                self.runner = runners.cisco.NXOS(self.crt, self.tab)
                self.os = "NXOS"
            if result == 3:
                self.runner = runners.cisco.XR(self.crt, self.tab)
                self.os = "XR"
            if result == 4:
                self.runner = runners.cisco.ASA(self.crt, self.tab)
                self.os = "ASA"
            if result == 5:
                self.runner = runners.cisco.WAAS(self.crt, self.tab)
                self.os = "WAAS"

        logging.info("OS class is {}".format(self.runner.__str__()))

