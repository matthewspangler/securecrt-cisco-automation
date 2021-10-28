# $language = "Python3"
# $interface = "1.0"

import re
import os
from ftplib import FTP

class CiscoScripts:
    def __init__(self, runner_class_instance):
        self.session = runner_class_instance

    def no_shut(self, interface):
        """
        No shut a runners interface
        :param interface:
        :return:
        """

        pass  # TODO - OS agnostic function

    def cdp_enable(self, intf_list=None):
        if not intf_list:
            pass  # just enable in conf t
        else:
            pass  # enable in conf t AND in interfaces

    def save_configuration(self):
        """
        Runs: #copy run start; #wr; #wr me; (XR) #commit
        :return:
        """
        pass  # TODO - os agnostic function

    def get_mgmt_vrf(self):
        """
        Returns the management vrf for the management interface
        :return:
        """
        return self.session.get_mgmt_vrf()

    def show_interface_brief(self):
        """
        Returns a brief summary of all interfaces. Equivalent of "sh int br" or "sh ip int br"
        :return:
        """
        return self.session.show_intf_brief()

    def ping(self):
        pass

    def image_device(self, image_name):
        self.session.priv_exec()

        # Gets the directory on the router/switch to copy to, such as flash:, bootflash:, etc.
        copy_dir = self.session.get_copy_directory()

        sh_run_boot = '\n'.join(self.session.get_command_output("sh run | i boot"))
        sh_boot = '\n'.join(self.session.get_command_output("sh boot"))

        # Check for kickstart.
        kickstart = False
        if "kickstart" in sh_boot:
            kickstart = True
            raise Exception("Not implemented for kickstart images. Please image manually!")
            # TODO - implement kickstart imaging

        # TODO - We need a better way to distinguish NXOS than this. If the boot variable is erased, this doesn't work.
        boot_var = None
        if "nxos" in sh_run_boot:
            boot_var = "nxos"
        if "system" in sh_run_boot:
            boot_var = "system"
        if boot_var is None:
            raise Exception("Could not find boot variable name. Please image manually!")

        self.session.global_config()

        self.session.send("no boot {} \r".format(boot_var))
        self.session.send("boot {} {}{} \r".format(boot_var, copy_dir, image_name))

        self.session.priv_exec()
        self.session.save_changes()

        self.session.crt.Dialog.MessageBox("Please MANUALLY double check boot variable, and then reload.")

    def get_copy_directory(self, runner):
        dir_output = '\n'.join(self.session.get_command_output("dir | i :/"))
        # This regex matches stuff like: bootflash:/ flash:/ and harddisk:/
        matches = re.finditer(r"(\S+)\s*:/(?!\/)", dir_output, re.MULTILINE)
        results = []
        for match in matches:
            results.append(match.group())
        return results[0].split("/")[0]  # I decided to remove the '/' because it isn't necessary.

    def copy_from_ftp_server(self, session, hostname, username, password, title="Please select an image file", filter="Image files (*.bin)|*.bin||"):
        runner = session.runner
        image_full_path = self.session.crt.Dialog.FileOpenDialog(title, filter)

        HOSTNAME = hostname
        USERNAME = username
        PASSWORD = password

        # Connect FTP Server
        ftp_server = FTP(HOSTNAME, USERNAME, PASSWORD)

        # force UTF-8 encoding
        ftp_server.encoding = "utf-8"

        # Get filename from full path:
        filename = os.path.basename(image_full_path)

        # Login so we can check what files are already on the ftp server:
        ftp_server.login(USERNAME, PASSWORD)

        # If file is already on server, delete it:
        if filename in ftp_server.nlst():
            ftp_server.delete(filename)

        try:
            # Read file in binary mode
            with open(image_full_path, "rb") as file:
                # Command for Uploading the file "STOR filename"
                ftp_server.storbinary(f"STOR {filename}", file)
        except Exception as e:
            # Print out errors in a message box:
            self.session.crt.Dialog.MessageBox("Exception message: {}".format(e))

        success = False
        if filename in ftp_server.nlst():
            # crt.Dialog.MessageBox("File {} successfully uploaded to FTP server.".format(filename))
            success = True

        if success is False:
            raise Exception("Could not find file on FTP server!")

        ftp_server.quit()
        mgmt_vrf = runner.get_mgmt_vrf()

        if mgmt_vrf is None:
            self.copy_ftp(HOSTNAME, filename, USERNAME, PASSWORD)
        else:
            self.copy_ftp(HOSTNAME, filename, USERNAME, PASSWORD, mgmt_vrf)

        return filename

    def copy_ftp(self, runner, hostname, source_filename, username="", password="", vrf=None, destination_dir=None,
                 copy_timeout=1800):
        if destination_dir is None:
            destination_dir = self.get_copy_directory(runner)

        self.session.priv_exec()

        if vrf is None:
            self.session.current_tab.Screen.Send("copy ftp://{}:{}@{} {} \r".format(username,
                                                                                    password,
                                                                                    hostname,
                                                                                    destination_dir))

        else:
            self.session.current_tab.Screen.Send("copy ftp://{}:{}@{} {} vrf {} \r".format(username,
                                                                                           password,
                                                                                           hostname,
                                                                                           destination_dir,
                                                                                           vrf))

        while True:
            result = self.session.current_tab.Screen.WaitForStrings(["Address",
                                                                     "filename",
                                                                     "Destination",
                                                                     "write",
                                                                     "OK",
                                                                     "!"
                                                                     ], 10)
            if result == 1:
                self.session.send("\r")
            if result == 2:
                self.session.current_tab.Screen.Send(source_filename + "\r")
            if result == 3:
                self.session.send("\r")
            if result == 4:
                self.session.send("\r")
            if result == 5:
                break
            if result == 6:
                # Currently copying, could take a while. Wait 30 minutes for it to finish.
                self.session.current_tab.Screen.WaitForString("OK", copy_timeout)
            if result == 0:
                # TODO - timeout error
                break
