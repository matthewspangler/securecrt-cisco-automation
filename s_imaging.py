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

def ftp_push_image(hostname, username, password):
    # Get image to upload
    image_full_path = crt.Dialog.FileOpenDialog(title="Please select an image file",
                                                filter="Image files (*.bin)|*.bin||")

    # Connect FTP Server
    ftp_server = FTP(hostname, username, password)

    # force UTF-8 encoding
    ftp_server.encoding = "utf-8"

    # Get filename from full path:
    filename = os.path.basename(image_full_path)

    # Login so we can check what files are already on the ftp server:
    ftp_server.login(username, password)

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
        crt.Dialog.MessageBox("Exception message: {}".format(e))

    success = False
    if filename in ftp_server.nlst():
        # crt.Dialog.MessageBox("File {} successfully uploaded to FTP server.".format(filename))
        success = True

    if success is False:
        raise Exception("Could not find file on FTP server!")

    ftp_server.quit()

    return filename


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

    # Enter privileged exec mode
    runner.priv_exec()

    # Enter in the FTP server info:
    hostname = crt.Dialog.Prompt("Please enter the FTP server hostname/IP: ")
    username = crt.Dialog.Prompt("Please enter the FTP server username: ")
    password = crt.Dialog.Prompt("Please enter the FTP server password: ")

    do_ftp_upload = crt.Dialog.Prompt("Would you like to upload the file to the ftp server? [no]").lower()
    is_mgmt_intf = crt.Dialog.Prompt("Is the connection to the FTP server over a management interface? [no]").lower()

    filename = None
    if do_ftp_upload == "y" or "yes":
        filename = ftp_push_image(hostname, username, password)
    if is_mgmt_intf == "y" or "yes":
        mgmt_vrf = runner.get_mgmt_vrf()
        CiscoScripts(runner).copy_ftp(hostname, filename, username, password, mgmt_vrf)
    else:
        CiscoScripts(runner).copy_ftp(hostname, filename, username, password)

    if filename is None:
        filename = crt.Dialog.Prompt("Please enter the image filename: ")

    CiscoScripts(runner).image_device(filename)

    return runner  # return OS class so we can run commands on it from other scripts, and see gathered information.


main()
