from regipy.registry import RegistryHive
import re
import datetime
import ctypes, sys, os
import json

''' Iterates through the pre-installation registry and saves any key values that get deleted by installation'''
def create_modified_key_dictionary(both_name_list, pre_key, post_key):
    modified_keys = {}
    for name in both_name_list:  # Iterates through names common to both registries, to check if keys have been updated
        for key_value in pre_key:  # Iterates through names within the key to find name that matches the name being searched for
            if key_value.name == name:
                initial_key_value = key_value.value
                break
        for key_value_modified in post_key:
            if key_value_modified.name == name:
                modified_key_value = key_value_modified.value
                break
        if initial_key_value != modified_key_value:  # If the value of the key value has changed
            modified_keys[
                name] = initial_key_value  # We only need to save the value as it was before the installation occured
    return modified_keys


''' Iterates through the pre-installation registry and saves any key values that get deleted by installation'''
def create_deleted_key_dictionary(deleted_name_list, deleted_from_key):
    deleted_keys = {}
    for name in deleted_name_list:
        for key_value in deleted_from_key:
            if key_value.name == name:
                selected_key_value = key_value.value
                break
        deleted_keys[name] = selected_key_value
    return deleted_keys


''' Iterates through the post-installation registry and saves any key values that get create by installation'''
def create_created_key_dictionary(created_name_list, created_from_key):
    created_keys = {}
    for name in created_name_list:
        for key_value in created_from_key:
            if key_value.name == name:
                selected_key_value = key_value.value
                break
        created_keys[name] = selected_key_value
    return created_keys


''' This function iterates through the key objects to check for changes, and then returns the changes'''
def check_for_value_creation_and_deletion(modified, initial):
    names_only_in_modified = []  # Installation has  created these keys
    names_only_in_initial = []  # Installation has deleted these keys
    names_in_both = []
    checked_names = 0
    names_in_initial = []
    names_in_modified = []
    for key_value in modified:  # Gets a list of all the names in the key
        names_in_modified.append(key_value.name)
    for key_value in initial:
        names_in_initial.append(key_value.name)
    for name in names_in_modified:  # Iterates through the modified list to check if all of the names match
        if name in names_in_initial:
            checked_names += 1  # If this is equal to the length of the initial list, then it has been fully checked
            names_in_both.append(name)
        else:
            names_only_in_modified.append(name)
    if len(initial) != checked_names:  # If these are different, then there are keys in the initial key that aren't in the modified hive
        for name in names_in_initial:
            if name not in names_in_modified:
                names_only_in_initial.append(name)
    return names_in_both, names_only_in_initial, names_only_in_modified


''' This function is used to retrieve a list of registry keys that we want to ignore, because they are changes 
by the operating system rather than by a program installation'''
def registry_filter(registry_name):
    mod = (registry_name + "_modified").lower()
    delete = (registry_name + "_deleted").lower()
    cre = (registry_name + "_created").lower()
    paths = []
    with open('passive_reg.txt') as f:
        data = json.load(f)
        paths_mod = (data[mod].keys())
        paths_del = (data[delete].keys())
        paths_cre = (data[cre].keys())
        for path in paths_mod:
            paths.append(path)
        for path in paths_del:
            paths.append(path)
        for path in paths_cre:
            paths.append(path)
    return paths


''' This function is used to scan a given registry hive for changes that occurred during the installation period'''
def detect_registry_changes(install_time, registry_name, initial_registry_name):
    registry_file_name = registry_name + ".dat"
    reg_modified = RegistryHive(registry_file_name)
    reg_initial = RegistryHive(initial_registry_name)  # The registry before installation
    modified_registry_keys = {}
    deleted_registry_keys = {}
    created_registry_keys = {}
    for entry in reg_modified.recurse_subkeys(as_json=True):
        string_to_match = entry
        search_object = re.search('timestamp=', str(string_to_match))
        index_to_start = search_object.span()[1]
        index_to_end_path = index_to_start - 13  # The end of the path variable we need later is 13 spaces back from the date modified
        date_modified = str(string_to_match)[(index_to_start + 1):(index_to_start + 33)]
        datetime_object = datetime.datetime.strptime(date_modified, '%Y-%m-%dT%H:%M:%S.%f%z')
        paths_to_ignore = registry_filter(registry_name)
        if (datetime_object > install_time):
            # Get the path of the key if there have been changes in it
            search_object = re.search('path=', str(string_to_match))
            index_to_start_path = search_object.span()[1]
            key_path = str(string_to_match)[(index_to_start_path + 1):index_to_end_path]
            key_path = key_path.replace(r"\\", "\\")
            if key_path not in paths_to_ignore:  # If the path isn't a path edited by the OS
                # Find the keys by their path
                modified_key = reg_modified.get_key(key_path).get_values(as_json=True)
                initial_key = reg_initial.get_key(key_path).get_values(as_json=True)

                # Get which values were added, removed or modified in the key
                both_names, deleted_names, created_names = check_for_value_creation_and_deletion(modified_key, initial_key)
                mod_keys = create_modified_key_dictionary(both_names, initial_key, modified_key)
                del_keys = create_deleted_key_dictionary(deleted_names, initial_key)
                cre_keys = create_created_key_dictionary(created_names, modified_key)
                if len(mod_keys) > 0:
                    modified_registry_keys[key_path] = mod_keys
                if len(del_keys) > 0:
                    deleted_registry_keys[key_path] = del_keys
                if len(cre_keys) > 0:
                    created_registry_keys[key_path] = cre_keys

    return modified_registry_keys, deleted_registry_keys, created_registry_keys


''' This function is used to ensure that this program is being executed with administrator privileges'''
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


''' This function issues commands to the operating system to create files to represent the current state of 
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


''' This function issues commands to the operating system to create files to represent the current state of 
the registry'''
def getCopyOfRegistry():
    os.system('REG SAVE HKCC "HKCC.dat" /y')
    os.system('REG SAVE HKCR "HKCR.dat" /y')
    os.system('REG SAVE HKCU "HKCU.dat" /y')
    os.system('REG SAVE HKLM\SAM "SAM.dat" /y')
    os.system('REG SAVE HKLM\SECURITY "SECURITY.dat" /y')
    os.system('REG SAVE HKLM\SOFTWARE "SOFTWARE.dat" /y')
    os.system('REG SAVE HKLM\SYSTEM "SYSTEM.dat" /y')
    os.system('REG SAVE HKLM\HARDWARE "HARDWARE.dat" /y')


'''Debugging information'''
if is_admin():
    '''matches_from_hkcc()
    matches_from_hardware()
    matches_from_hkcr()
    matches_from_hkcu()
    matches_from_sam()
    matches_from_security()
    matches_from_software()
    matches_from_system()'''

else:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

