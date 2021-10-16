# Anything for working with multiple tabs or SecureCRT in general goes in this class.

import runners
import logging
import os
from runners.common_runner import CommonRunner
from runners.cisco.cisco_runner import CiscoRunner
from runners.nix import LinuxRunner
import runners.cisco
import crt_automation.utilities


class CrtSession:
    def __init__(self, crt):
        self.crt = crt
        self.sessions = self.get_all_sessions()
        # Sessions loosely represent tabs, although a session can be reassigned to a different tab.
        self.active_session = self.get_active_session()
        self.initial_tab = self.crt.GetScriptTab()

    def cleanup(self):
        """
        Run this at the end of your scripts, to return everything back to how it was before you ran the script.
        """
        for session in self.sessions:
            session.tab.Caption = session.host
        self.initial_tab.Activate()

    def get_active_session(self):
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
            self.active_session = self.get_active_session()
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
        Check this session's OS against a list of OS's to verify a script's compatibility.
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
                raise Exception("Could not find self.os")
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
        pass

    def start_linux_session(self):
        """
        Sets self.runner to an instance of the bash class
        :return:
        """
        self.os = "Linux"
        self.runner = LinuxRunner(self.crt, self.tab)
        self.runner.set_prompt()

    def start_cisco_session(self, enable_pass=None, username=None, password=None, timeout=5):
        """
        Discovers the Cisco OS, sets self.runner to an instance of a runner class, and sets the prompt.
        :return:
        """
        self.crt.Screen.Synchronous = True

        if not self.is_connected():
            raise Exception("Session is not connected.  Cannot start Cisco session.")

        if enable_pass:
            self.enable_pass = enable_pass
        if username:
            self.username = username
        if password:
            self.password = password

        # Use this runner until we discover the network OS type
        temp_runner = runners.CiscoRunner(self.crt, self.tab)

        # Discover the prompt so we can parse output
        temp_runner.set_prompt()

        if ">" in temp_runner.prompt:  # enter priv exec from user exec
            temp_runner.send("en \r")
            temp_runner.current_tab.Screen.WaitForString("en", timeout)
            temp_runner.set_prompt()
        while ")#" in temp_runner.prompt:  # exit configuration modes
            temp_runner.send("exit\r")
            temp_runner.current_tab.Screen.WaitForString("exit", timeout)
            temp_runner.set_prompt()

        sh_ver_out = temp_runner.get_command_output("sh ver | i Cisco")
        result = crt_automation.utilities.os_regex(sh_ver_out)
        if not result:
            if "IOS" in '\n'.join(sh_ver_out):
                self.runner = runners.cisco.XE(self.crt, self.tab)
                self.os = "IOS"
            else:
                # TODO - handle ROMMON properly.
                self.runner = runners.cisco.ROMMON(self.crt, self.tab)
                self.os = "ROMMON"
        else:
            if "XE" in result:
                self.runner = runners.cisco.XE(self.crt, self.tab)
                self.os = "XE"
            elif "XR" in result:
                self.runner = runners.cisco.XR(self.crt, self.tab)
                self.os = "XR"
            elif "WAAS" in result:
                self.runner = runners.cisco.WAAS(self.crt, self.tab)
                self.os = "WAAS"
            elif "NX-OS" in result:
                self.runner = runners.cisco.NXOS(self.crt, self.tab)
                self.os = "NXOS"
            elif "ASA" in result:
                self.runner = runners.cisco.ASA(self.crt, self.tab)
                self.os = "ASA"
            else:
                # if all else fails:
                self.runner = CommonRunner(self.crt, self.tab)
                self.os = "Unknown"
                # TODO: add Linux detection.

        logging.debug("OS class is {}".format(self.runner.__str__()))