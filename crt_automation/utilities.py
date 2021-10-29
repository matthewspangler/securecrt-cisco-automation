# $language = "Python3"
# $interface = "1.0"

import re
import socket
import struct
import logging
import textfsm

logger = logging.getLogger()

# Enter one of the most convoluted regular expressions I've ever worked with:
interface_regex = r"\w+(-\w+)?\d+(([\/:]\d+)+(\.\d+)?)?"

replace_pairs = [
    ("Ce", "Cellular"),
    ("Eth", "Ethernet"),
    ("Et", "FastEthernet"),
    ("Gi", "GigabitEthernet"),
    ("GE", "GigabitEthernet"),
    ("Te", "TenGigabit"),
    ("Se", "Serial"),
    ("AT", "ATM"),
    ("Po", "Port-channel"),
    ("PortCh", "Port-channel"),
    ("Tu", "Tunnel"),
    ("Lo", "Loopback"),
    ("NV", "NVI"),
    ("FD", "Fddi"),
    ("Vl", "Vlan"),
    ("EO", "EOBC"),
    ("Vi", "Virtual-Access"),
    ("Vt", "Virtual-Template"),
    ("In", "Internal-Data"),
    ("Async", "Async"),
    ("Group-Async", "Group-Async"),
    ("mgmt", "mgmt"),
    ("Ma", "Management")
]


def intf_regex(any_string):
    """
    Uses Regular Expression to determine if string contains a Cisco interface name
    :param any_string: Multiline string to perform regular expression search on
    :return: list of interface names if any were found
    """
    matches = re.finditer(interface_regex, any_string, re.MULTILINE)
    results = []
    for match in matches:
        results.append(match.group())
    return results


def long_int_from_int_list(short_name, int_list):
    """
    Returns the canonical interface name for an abbreviated form.
    Requires a list of all interfaces as a parameter.
    :param short_name: the full interface name, like "GigabitEthernet1/1"
    :param int_list: a list of interface names from the disco device
    :return:
    """
    num_regex = r'[\d\/]{1,}'
    short_intf_nums = re.search(num_regex, short_name).group()
    short_intf_word = re.split(num_regex, short_name)[0]
    for interface in int_list:
        # make it case insensitive:
        if short_intf_word.lower() in interface.lower():
            long_intf_nums = re.search(num_regex, interface).group()
            if short_intf_nums in long_intf_nums:
                return interface
    return None


def short_int_name(long_name):
    """
    This function shortens the interface name for easier reading
    :param long_name:  The input string (long interface name)
    :return:  The shortened interface name
    """
    lower_str = long_name.lower()
    for pair in replace_pairs:
        if pair[1] in lower_str:
            return lower_str.replace(pair[1], pair[0])
    else:
        return long_name


def long_int_name(short_name):
    """
    This function expands a short interface name to the full name
    :param short_name:  The input string (short interface name)
    :return:  The shortened interface name
    """
    for pair in replace_pairs:
        if re.match("{0}\d".format(pair[0]), short_name, re.IGNORECASE):
            return short_name.replace(pair[0], pair[1])
    else:
        return short_name


def expand_number_range(num_string):
    """
    A function that will accept a text number range (such as 1,3,5-7) and convert it into a list of integers such as
    [1, 3, 5, 6, 7]
    :param num_string: <str> A string that is in the format of a number range (e.g. 1,3,5-7)
    :return: <list> A list of all integers in that range (e.g. [1,3,5,6,7])
    """
    num_string = num_string.strip()
    temp = [(lambda sub: range(sub[0], sub[-1] + 1))(list(map(int, ele.split('-')))) for ele in num_string.split(',')]
    output_list = [b for a in temp for b in a]
    return output_list


def expand_int_range(int_range):
    """
    Returns a list of individual interfaces from an interface range
    :param int_range:
    :return:
    """
    int_range = int_range.strip()
    int_name = re.split('[^a-zA-Z]', int_range.strip())[0]
    num_range = int_range.split(int_name)[1]
    linecard_nums = ''
    if '/' in num_range:
        # rsplit delimits by last '/' in string:
        linecard_nums = num_range.rsplit('/', 1)[0] + '/'
        print(linecard_nums)
        num_range = num_range.rsplit('/', 1)[1]
    print(num_range)
    nums = expand_number_range(num_range)
    output_list = []
    for num in nums:
        interface = int_name + linecard_nums + str(num)
        output_list.append(long_int_name(interface))
    return output_list


def os_regex(show_ver_output):
    """
    Gets the OS type from #show version
    :param show_ver_output: list containing lines returned from #sh ver
    :return: OS type, like 'XR', 'XE', etc.
    """
    sh_ver_str = '\n'.join(show_ver_output)
    result = re.search(r"XE|XR|NX-OS|ASA|AIR|WAAS", sh_ver_str, re.IGNORECASE)
    if not result:
        result = None
    else:
        result = result.group()
    return result


def textfsm_parse_to_list(input_data, template_name, add_header=False):
    """
    Use TextFSM to parse the input text (from a command output) against the specified TextFSM template.   Use the
    default TextFSM output which is a list, with each entry of the list being a list with the values parsed.  Use
    add_header=True if the header row with value names should be prepended to the start of the list.
    :param input_data:  Path to the input file that TextFSM will parse.
    :param template_name:  Path to the template file that will be used to parse the above data.
    :param add_header:  When True, will return a header row in the list.  This is useful for directly outputting to CSV.
    :return: The TextFSM output (A list with each entry being a list of values parsed from the input)
    """

    logger.debug("Preparing to process with TextFSM and return a list of lists")
    # Create file object to the TextFSM template and create TextFSM object.
    logger.debug("Using template at: {0}".format(template_name))
    with open(template_name, 'r') as template:
        fsm_table = textfsm.TextFSM(template)

    # Process our raw data vs the template with TextFSM
    output = fsm_table.ParseText(input_data)
    logger.debug("TextFSM returned a list of size: '{0}'".format(len(output)))

    # Insert a header row into the list, so that when output to a CSV there is a header row.
    if add_header:
        logger.debug("'Adding header '{0}' to start of output list.".format(fsm_table.header))
        output.insert(0, fsm_table.header)

    return output


def textfsm_parse_to_dict(input_data, template_filename):
    """
    Use TextFSM to parse the input text (from a command output) against the specified TextFSM template.   Convert each
    list from the output to a dictionary, where each key in the TextFSM Value name from the template file.
    :param input_data:  Path to the input file that TextFSM will parse.
    :param template_filename:  Path to the template file that will be used to parse the above data.
    :return: A list, with each entry being a dictionary that maps TextFSM variable name to corresponding value.
    """

    logger.debug("Preparing to process with TextFSM and return a list of dictionaries.")
    # Create file object to the TextFSM template and create TextFSM object.
    logger.debug("Using template at: {0}".format(template_filename))
    with open(template_filename, 'r') as template:
        fsm_table = textfsm.TextFSM(template)

    # Process our raw data vs the template with TextFSM
    fsm_list = fsm_table.ParseText(input_data)
    logger.debug("TextFSM returned a list of size: '{0}'".format(len(fsm_list)))

    # Insert a header row into the list, so that when output to a CSV there is a header row.
    header_list = fsm_table.header

    # Combine the header row with each entry in fsm_list to create a dictionary representation.  Add to output list.
    output = []
    for entry in fsm_list:
        dict_entry = dict(zip(header_list, entry))
        output.append(dict_entry)

    logger.debug("Converted all sub-lists to dicts.  Size is {0}".format(len(output)))
    return output


def CIDR_to_IP_netmask(CIDR):
    ip, net_bits = CIDR.split('/')
    host_bits = 32 - int(net_bits)
    netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
    return ip, netmask