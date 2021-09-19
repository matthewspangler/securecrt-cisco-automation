#   Secure CRT Cisco Automation

```

      ||        ||
      ||        ||                     
     ||||      ||||
 ..:||||||:..:||||||:..                 
------------------------
C i s c o  S y s t e m s
```

### About

This is a set of libraries and scripts for automating Cisco devices (and to a lesser extent, bash prompts)
via SecureCRT. 

SecureCRT's built-in python functions are very basic, making it difficult to automate complex tasks.
This library makes it easier to write scripts for Cisco devices by adding a little abstraction.

Main goals of this project:
* Abstract automating SecureCRT so writing scripts requires less work
* Make it easier to do OS agnostic scripting (IOS XE, XR, NXOS, ASA, etc.)
* Make it easier to parse Cisco configurations and shell output

Currently I have tested this library mostly on IOS, IOS XE, ASA, and NXOS. 
While I have prototyped a class for XR, I am not familiar enough with XR to finish it.

This entire project is under the GPLv3 license. I would love to see others contribute to it!


### Help

For help with scripting, please check the [wiki](https://github.com/matthewspangler/securecrt-cisco-automation/wiki).

As of writing this README, SecureCRT only works with Python 3.8, 
so make sure you DON'T install a later version unless they update
SecureCRT for newer versions of python.

To setup dependencies, navigate to the project's root directory and run ```pip install -r requirements.txt```.

#### Included Scripts

Multi-tab:
- m_template.py - example script showing off features of this library
- m_run_script_all_tabs.py - Runs a selected script on all tabs with an active connection
- m_cdp_map.py - Enables CDP and parses the output of #sh cdp neigh detail

Single-tab:
- s_imaging.py - automates imaging Cisco devices over FTP
- s_gotorommon.py - reloads and sends break sequence until ROMMON is reached
- s_set_tabs_to_prompts.py - sets the tab name to match the cisco hostname
- s_start_to_file.py - saves startup-config to a .txt file
- s_run_to_file.py - saves running-config to a .txt file
- s_set_intf_cidr.py - Finds an unused IP from a CIDR and sets on an interface.
- s_upload_config.py - uploads a cisco configuration text file to a cisco device's startup-config
- s_noshut_all.py - run 'no shutdown' on a specified range of interfaces
- s_password_crack.py - attempts to login by following a password list

If you have any suggestions for scripts you'd like to see included, feel free to submit them through github!

### Credits
This project was made possible by referencing solutions from two other projects on Github:
- jamiecaesar/securecrt-tools 
- btr1975/secure-crt-python-public

Both are Python 2, rather than Python 3, and thus did not meet my needs.
Nonetheless, I am indebted to both. Thank you!


#### Useful Links

Useful links with SecureCRT python scripting examples:
- https://www.vandyke.com/support/securecrt/python_examples.html
- https://forums.vandyke.com/showthread.php?t=12857
- https://forums.vandyke.com/showthread.php?t=14434
- https://forums.vandyke.com/showthread.php?t=14295
