from regipy.registry import RegistryHive
import re
import datetime
import ctypes,sys,os
import json
import regipy
import regipy.regdiff
import testregpi
import dateutil.parser
''' Iterates through the pre-installation registry and saves any key values that get deleted by installation
both_name_list: a list containing the names of key values that have been modified during installation
pre_key: The initial key being checked
post_key: The modified key being checked'''
def create_modified_key_dictionary(both_name_list, pre_key, post_key):
    modified_keys = {}  # Return dictionary
    for name in both_name_list:  # Iterates through names common to both registries, to check if keys have been updated
        for key_value in pre_key:  # Iterates through names within the key to find name that matches the name being searched for
            if key_value.name == name:  # Finds the matching key name in the  initial key
                initial_key_value = key_value.value  # Retrieves the value from the initial key
                break
        for key_value_modified in post_key:
            if key_value_modified.name == name:  # Finds the matching key name in the modified key
                modified_key_value = key_value_modified.value
                modified_key_value_type = key_value_modified.value_type
                break
        if initial_key_value != modified_key_value:  # If the value of the key value has changed
            modified_keys[
                name] = [initial_key_value, modified_key_value_type]  # We only need to save the value as it was before the installation occurred
    return modified_keys


''' Iterates through the pre-installation registry and saves any key values that get deleted by installation. 
Documentation as above
deleted_name_list: List containing the names of key values that have been deleted during installation
deleted_from_key: The initial key containing the deleted value'''
def create_deleted_key_dictionary(deleted_name_list, deleted_from_key):
    deleted_keys = {}
    for name in deleted_name_list:
        for key_value in deleted_from_key:
            if key_value.name == name:
                selected_key_value = key_value.value
                selected_key_value_type = key_value.value_type
                break
        deleted_keys[name] = [selected_key_value, selected_key_value_type]
    return deleted_keys


''' Iterates through the post-installation registry and saves any key values that get create by installation.
Documentation as above
created_name_list: List containing the names of key values that have been created during installation
created_from_key: The modified key containing the created value'''
def create_created_key_dictionary(created_name_list, created_from_key):
    created_keys = {}
    for name in created_name_list:
        for key_value in created_from_key:
            if key_value.name == name:
                selected_key_value = key_value.value
                selected_key_value_type = key_value.value_type
                break
        created_keys[name] = [selected_key_value, selected_key_value_type]
    return created_keys


''' This function iterates through the key objects to check for changes, and then returns the changes
modified: A list of the modified key's values
initial: A list of the initial key's values'''
def check_for_value_creation_and_deletion(modified, initial):
    names_only_in_modified = []  # Installation has  created these key values
    names_only_in_initial = []  # Installation has deleted these key values
    names_in_both = []  # Installation has modified these values
    checked_names = 0
    names_in_initial = []
    names_in_modified = []
    for key_value in modified:  # Gets a list of all the names in the key
        names_in_modified.append(key_value.name)
    for key_value in initial:
        names_in_initial.append(key_value.name)
    for name in names_in_modified:  # Iterates through the modified list to check if all of the names match
        if name in names_in_initial:  # If the value appears in both keys
            checked_names += 1  # If this is equal to the length of the initial list, then it has been fully checked
            names_in_both.append(name)
        else:  # If the value only appears in the modified key
            names_only_in_modified.append(name)
    if len(names_in_initial) != checked_names:  # If these are different, then there are keys in the initial key that aren't in the modified hive
        for name in names_in_initial:
            if name not in names_in_modified:  # If the value only appears in the initial key
                names_only_in_initial.append(name)
    return names_in_both, names_only_in_initial, names_only_in_modified


''' This function is used to retrieve a list of registry keys that we want to ignore, because they are changes 
by the operating system rather than by a program installation
registry_name: the name of the registry hive being scanned'''
def registry_filter(registry_name):
    mod = (registry_name + "_modified").lower()  # Uses the registry name and "modified" to select a specific key in the dictionary
    delete = (registry_name + "_deleted").lower()
    cre = (registry_name + "_created").lower()
    paths = []  # Return dictionary
    with open('passive_reg.txt') as f:
        data = json.load(f)  # Retrieves the dictionary stored in the JSON file
        paths_mod = (data[mod].keys())  # Pulls the key paths from the relevant key in the dictionary
        paths_del = (data[delete].keys())
        paths_cre = (data[cre].keys())
        for path in paths_mod:
            paths.append(path)
        for path in paths_del:
            paths.append(path)
        for path in paths_cre:
            paths.append(path)
    return paths

'''This function retrieves the path of any keys in the SOFTWARE hive that have been modified during the installation
install_time: the time that the installation began
reg_modified: The modified SOFTWARE hive'''
def getMatchingSoftwareKeys(install_time, reg_modified):
    listOfSoftwareKeys = []  # Return list
    '''Here, we use a modified version of a Regipy function. It functions the same, except that it doesn't 
    retrieve the values of every key that it checks. We do this because using the original function would cause
    this process to take approximately 50 hours to complete, and this modified version takes approximately 2 minutes'''
    for subkey in testregpi.recurse_subkeys(reg_modified):
        subkey_path = subkey.path  # Retrieves the path of the current key
        ts = subkey.timestamp  # Retrieves the timestamp of the current key
        if ts > install_time:  # If the timestamp is greater than install_time, then it was created during installation
            ignore_policies = re.search("Policies", subkey_path)
            ignore_classes = re.search("Classes", subkey_path)
            if not ignore_policies and not ignore_classes:  # If the key is not one that we want to ignore
                listOfSoftwareKeys.append(subkey_path)
    return listOfSoftwareKeys


'''Because the software hive is so large, we use a different method of scanning it, using a modified regipy method
to cut down on the amount of processing required to scan the hive. This method returns 3 dictionaries, containing
keys that have changed, been created, or been deleted during the installation
registry_name: used to retrieve the keys to ignore from the registry filter file
install_time: the timestamp of the start of the installation, used to determine which keys were changed during installation
reg_initial: The initial registry hive
reg_modified: The modified registry hive'''
def softwareScan(registry_name, install_time, reg_initial, reg_modified):
    listOfSoftwareKeys = getMatchingSoftwareKeys(install_time, reg_modified)  # Retrieves the keys that have changed in the software hive
    modified_registry_keys = {}  # Dictionary that stores information on keys that have been modified during installation
    deleted_registry_keys = {}
    created_registry_keys = {}
    paths_to_ignore = registry_filter(registry_name)  # Retrieves keys to be ignored
    for software_key_path in listOfSoftwareKeys:  # Cycles through each key that has changed during installation
        key_path = software_key_path.replace(r"\\", "\\")  # Replaces any double backslashes with single ones

        if key_path not in paths_to_ignore:  # If the path isn't a path edited by the OS
            # Find the keys by their path
            modified_key = reg_modified.get_key(key_path).get_values(as_json=True)
            try:
                initial_key = reg_initial.get_key(key_path).get_values(as_json=True)

                # Get which values were added, removed or modified in the key
                both_names, deleted_names, created_names = check_for_value_creation_and_deletion(
                    modified_key, initial_key)
                mod_keys = create_modified_key_dictionary(both_names, initial_key, modified_key)  # Retrieve information about the key values, such as their value and its type
                del_keys = create_deleted_key_dictionary(deleted_names, initial_key)
                cre_keys = create_created_key_dictionary(created_names, modified_key)
                if len(mod_keys) > 0:  # If at least one value has been modified within the current key
                    modified_registry_keys[key_path] = mod_keys  # Stored the key value information against the key path
                if len(del_keys) > 0:  # If at least one value has been deleted within the current key
                    deleted_registry_keys[key_path] = del_keys
                if len(cre_keys) > 0:
                    created_registry_keys[key_path] = cre_keys

            except regipy.RegistryKeyNotFoundException:  # This error is raised when a key is not found, which for our purposes means that a full key has been created
                all_keys = {}
                for key_value in modified_key:  # This iterates through each value in the key
                    current_name = key_value.name  # Retrieves the key value name
                    current_key_value = key_value.value  # Retrieves the key value value
                    current_key_value_type = key_value.value_type  # Retrieves the key value type
                    all_keys[current_name] = [current_key_value, current_key_value_type]  # Stores the value information against its name
                created_registry_keys[key_path] = all_keys  # Adds the key information to the return list
    return modified_registry_keys, deleted_registry_keys, created_registry_keys


''' This function is used to scan a given registry hive for changes that occurred during the installation period
install_time: the start time of the installation
registry_name: the name of the registry, used to find the modified registry snapshot
initial_registry_name: the name of the registry, used to find the initial registry snapshot'''
def detect_registry_changes(install_time, registry_name, initial_registry_name):
    registry_file_name = registry_name + ".dat"  # On the file system, the registry snapshot is a .dat file
    reg_modified = RegistryHive(registry_file_name)  # Handler object for the modified registry snapshot
    reg_initial = RegistryHive(initial_registry_name)  # Handler object for the initial registry snapshot
    modified_registry_keys = {}  # Dictionary that stores information on keys that have been modified during installation
    deleted_registry_keys = {}
    created_registry_keys = {}
    if registry_name == "software":  # The software registry has to be handled differently, because of its size
        modified_registry_keys, deleted_registry_keys, created_registry_keys = softwareScan(registry_name, install_time, reg_initial, reg_modified)
    else:
        for entry in reg_modified.recurse_subkeys(as_json=True):  # Iterates through each key in the registry hive
            date_modified = entry.timestamp  # Retrieves the timestamp for the last time that the key was modified
            key_path = entry.path  # Retrieves the key path of the key
            datetime_object = datetime.datetime.strptime(date_modified, '%Y-%m-%dT%H:%M:%S.%f%z')  # Formats the timestamp to a format where we can compare it to another timestamp
            paths_to_ignore = registry_filter(registry_name)  # Retrives the registry keys that we want to ignore
            if datetime_object > install_time:  # If the key has been modified during installation
                key_path = key_path.replace(r"\\", "\\")  # Replace double backslashes with single backslash
                if key_path not in paths_to_ignore:  # If the path isn't a path edited by the OS
                    # Find the keys by their path
                    modified_key = reg_modified.get_key(key_path).get_values(as_json=True)
                    try:
                        initial_key = reg_initial.get_key(key_path).get_values(as_json=True)

                        # Get which values were added, removed or modified in the key
                        both_names, deleted_names, created_names = check_for_value_creation_and_deletion(modified_key, initial_key)
                        mod_keys = create_modified_key_dictionary(both_names, initial_key, modified_key)  # Retrieve information about the key value, such as its value and its type
                        del_keys = create_deleted_key_dictionary(deleted_names, initial_key)
                        cre_keys = create_created_key_dictionary(created_names, modified_key)
                        if len(mod_keys) > 0: # If at least one value has been modified within the current key
                            modified_registry_keys[key_path] = mod_keys
                        if len(del_keys) > 0:
                            deleted_registry_keys[key_path] = del_keys
                        if len(cre_keys) > 0:
                            created_registry_keys[key_path] = cre_keys
                    except regipy.RegistryKeyNotFoundException:  # This error is raised when a key is not found, which for our purposes means that a full key has been created
                        all_keys = {}
                        for key_value in modified_key:  # This iterates through each value in the key
                            current_name = key_value.name  # Retrieves the key value name
                            current_key_value = key_value.value  # Retrieves the key value value
                            current_key_value_type = key_value.value_type  # Retrieves the key value type
                            all_keys[current_name] = [current_key_value,
                                                      current_key_value_type]  # Stores the value information against its name
                        created_registry_keys[key_path] = all_keys  # Adds the key information to the return list
    return modified_registry_keys, deleted_registry_keys, created_registry_keys


''' This function issues commands to the operating system to create files to represent the initial state of 
the registry'''
def getInitialCopyOfRegistry():
    os.system('REG SAVE HKCC "HKCCInitial.dat" /y')
    os.system('REG SAVE HKCR "HKCRInitial.dat" /y')
    os.system('REG SAVE HKCU "HKCUInitial.dat" /y')
    os.system('REG SAVE HKLM\SAM "SAMInitial.dat" /y')
    os.system('REG SAVE HKLM\SECURITY "SECURITYInitial.dat" /y')
    os.system('REG SAVE HKLM\SOFTWARE "SOFTWAREInitial.dat" /y')
    os.system('REG SAVE HKLM\SYSTEM "SYSTEMInitial.dat" /y')
    os.system('REG SAVE HKLM\HARDWARE "HARDWAREInitial.dat" /y')
    print("Registry Backup Complete")

''' This function issues commands to the operating system to create files to represent the current state of 
the registry'''
def getCopyOfRegistry():
    os.system('REG SAVE HKCC "HKCC.dat" /y')  # Creates a copy of the HKCC hive using the REG SAVE command
    os.system('REG SAVE HKCR "HKCR.dat" /y')
    os.system('REG SAVE HKCU "HKCU.dat" /y')
    os.system('REG SAVE HKLM\SAM "SAM.dat" /y')
    os.system('REG SAVE HKLM\SECURITY "SECURITY.dat" /y')
    os.system('REG SAVE HKLM\SOFTWARE "SOFTWARE.dat" /y')
    os.system('REG SAVE HKLM\SYSTEM "SYSTEM.dat" /y')
    os.system('REG SAVE HKLM\HARDWARE "HARDWARE.dat" /y')


