import shutil  # Used to copy files on the file system
import json  # Used to retrieve the JSON template file
import os  # Used to create directories on the file system
import winreg  # Used to restore registry keys
'''This function accesses the template file for the program selected by the user, retrieves all created file paths 
from it, and returns them to the calling function
template_file_name: the name of the template file input by the user'''
def retrieve_created_files(template_file_name):
    created_files = []  # Return list
    fileName = template_file_name + ".txt"
    with open(fileName) as f:
        data = json.load(f)  # Creates a dictionary of the template data
        paths_cre = (data["files_created"])  # Retrieves the list of file paths of files created during installation
    for path in paths_cre:
        created_files.append(path)
    return created_files


'''This function accesses the template file for the program selected by the user, retrieves all created registry key 
paths from it for a given registry key, and returns them to the calling function
template_file_name: the name of the template file input by the user
reg_name: name of the hive that we want to know the changes of'''
def retrieve_created_keys(template_file_name, reg_name):
    created_keys = {}  # Return list
    fileName = template_file_name + ".txt"
    reg_name = reg_name + "_created"
    with open(fileName) as f:
        data = json.load(f)  # Creates a dictionary of the template data
        created_keys = (data[reg_name])  # Retrieves the list of file paths of keys created during installation
    return created_keys


'''This function takes the list of files created by installation, and backs them up to a folder, so that the program
can be restored later'''
def backup_program_files():
    try:
        file_name = input("Give the file name of the template")
        files_to_backup = retrieve_created_files(file_name)
    except FileNotFoundError:
        print("No template with that name exists")
        return None
    backup_folder = os.path.join(r"C:\Users\Ben\Documents", file_name)  # Creates the path of the folder we will use to back up the program
    os.mkdir(backup_folder)  # Creates the backup folder
    for file in files_to_backup:  # For each program file that we need to backup
        try:
            backup_file_name = str(file).strip().replace("\\", "")  # The file name of the backup file is the path of the original file without backslashes
            backup_file_name = str(backup_file_name).strip().replace("//", "")
            file = file.replace("\\\\", "\\")  # Replaces double backslashes in the original file to single backslashes
            new_file_path = os.path.join(backup_folder, backup_file_name)  # Creates the path for the backup file
            shutil.copy2(file, new_file_path)  # Copies the original file to the backup file path
        except PermissionError:  # A PermissionError is raised when we attempt to copy a folder
            folders_to_save = os.path.join(backup_folder, 'folders_for_backup_restoration.txt')  # Creates a path to a file we will use to store program folders
            with open(folders_to_save, 'a') as f:  # Opens in append, ensuring that no information is overwritten if a file already exists
                write_to_file = file + "\r\n"  # \r\n is the windows NewLine character
                f.write(write_to_file)  # Adds the path to the folder to the txt file of folder paths
        except FileNotFoundError:  # If the file has been deleted since the installation occured
            continue


'''This function takes the backup files and restores them to their initial locations, restoring the program'''
def restore_backup_program_files():
    backup_folder_name = input("Give the file name of the template")
    backup_folder = os.path.join(r"C:\Users\Ben\Documents", backup_folder_name)  # Creates the path to the backup folder
    try:
        file_of_folders_to_create = os.path.join(backup_folder, 'folders_for_backup_restoration.txt')  # Creates the path to the file containing the list of folders that need created
        '''In order to successfully restore all of the files in the program, the folders that they are placed in must
               already exist. This section creates the folder structure of the program, so that the files can be correctly placed'''
        with open(file_of_folders_to_create, 'r') as f:
            folders_to_create = f.readlines()  # Retrieves folder paths from the file
            for folder in folders_to_create:
                create_folder(folder)
    except FileNotFoundError:
        pass  # If the file doesn't exist, then the program installation created no folders and we can continue
    try:
        files_to_restore = retrieve_created_files(backup_folder_name)  # Retrieves the list of file paths to restore
        for file in files_to_restore:
            try:
                backup_file_name = str(file).strip().replace("\\", "")  # Removes backslashes from the file to allow the backup file to be found
                backup_file_name = str(backup_file_name).strip().replace("//", "")
                backup_file_path = os.path.join(backup_folder, backup_file_name)
                shutil.copy2(backup_file_path, file)  # Copies the backup file into its original location
            except FileNotFoundError:  # If the file has been deleted
                continue
        restore_backup_keys(backup_folder_name)  # Restores registry keys from template file
    except FileNotFoundError:  # If the user inputs an incorrect template name
        print("Sorry, no backup file with that name exists")


'''This function is used to create the folder structure for the program being restored. It works by taking each
folder path in turn. It checks if the folder has already been created, and if it hasn't, it breaks down the path into
its subpaths e.g. C://Users/User/Documents/Test/LastFolder would become [C://Users, User, Documents, Test,LastFolder]. The first part of the
path is then checked, and if it exists, it joins it with the next part of the path and checks if that exists,
until it finds a path that doesn't exist. It then creates that folder, and then joins the next part and creates that folder.
For example, in the above example, the program checks if C://Users is an existing path. It is, so it checks if
C://Users/User is valid, which it is. This continues until it finds that C://Users/User/Documents/Test does not
exist, and so it creates that folder, adds LastFolder to the path, and creates C://Users/User/Documents/Test/LastFolder.
This method means that all folders in the project can be created without problems caused by trying to create a subfolder
before its superfolder.
folder_name: The name of the folder to be created'''
def create_folder(folder_name):
    does_folder_exist = os.path.exists(folder_name)  # Checks if the folder exists
    if does_folder_exist:
        return True
    else:  # If the folder does not exist
        folder_split_path = folder_name.split("\\")  # Creates a list of the parts of the file path
        iterator = len(folder_split_path)
        current_folder_to_check = ""  # Used to store the path being checked
        i = 0
        while i < iterator:
            current_folder_to_check = os.path.join(current_folder_to_check, folder_split_path[i])  # Adds the next part of the path
            does_folder_exist = os.path.exists(current_folder_to_check)
            if does_folder_exist:  # If the folder exists, nothing needs to be done
                i = i + 1
            else:  # If the folder does not exist, we need to create it and subsequent subfolders
                while i < (iterator-1):
                    os.mkdir(current_folder_to_check)  # Creates the current folder
                    i = i + 1
                    current_folder_to_check = os.path.join(current_folder_to_check, folder_split_path[i])  # Adds the next part of the path
                break


'''This function checks whether the registry keys created during installation have changed, and updates them to 
match the originals'''
def restore_backup_keys(template):
    hkcc_dict = retrieve_created_keys(template, "hkcc")  # This function opens the template file and retrieves created hkcc keys from it
    hkcc_keys = hkcc_dict.keys()  # Retrieves the keys from the dictionary, these keys are the paths of keys in the registry hive
    hardware_dict = retrieve_created_keys(template, "hardware")
    hardware_keys = hardware_dict.keys()
    hkcu_dict = retrieve_created_keys(template, "hkcu")
    hkcu_keys = hkcu_dict.keys()
    sam_dict = retrieve_created_keys(template, "sam")
    sam_keys = sam_dict.keys()
    security_dict = retrieve_created_keys(template, "security")
    security_keys = security_dict.keys()
    software_dict = retrieve_created_keys(template, "software")
    software_keys = software_dict.keys()
    regStringTypes = ["REG_NONE", "REG_SZ", "REG_EXPAND_SZ", "REG_BINARY", "REG_DWORD", "REG_DWORD_BIG_ENDIAN",
                      "REG_LINK", "REG_MULTI_SZ",
                "REG_RESOURCE_LIST", "REG_FULL_RESOURCE_DESCRIPTOR", "REG_RESOURCE_REQUIREMENTS_LIST",
                "REG_QWORD"]  # This list contains the names of key values types. Their index is the integer value of the type returned by winreg
    '''By way of explaination, the registry contains hives that contain keys. Each key contains values,
    and confusingly, each value consists of a value name and a value value(which is the information stored in the value)'''
    for key_path in hkcu_keys:  # Cycles through each key in the hkcu hive that was modified during installation
        key_value_dict = hkcu_dict[key_path]  # Retrieves the value names and their values from the dictionary
        value_names = key_value_dict.keys()  # This retrieves the names of the key values
        key_path = key_path.split("\\")  # To prevent problems with python handling "\" characters, we split the string on "\", and then rebuild it with the os.path.join method, which prevents python treating "\" as an escape character
        final_key_path = ""
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:  # We attempt to open the key in a try statement. If that fails, we know that the key doesn't exist, so we create a new key in the except clause
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, final_key_path)
        for value_name in value_names:  # This cycles through each value in the key to see if it has changed
            stored_value_info = key_value_dict[value_name]  # This pulls the information about the key value from the dictionary
            try:  # We attempt to read the key value in a try. If it fails, we know that the key value doesn't exist
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]  # This returns the integer that denotes the data type of the value
                key_value_exists = False  # This boolean denotes whether we need to create the key value
                if regType == stored_value_info[1]:  # If the value type is the same as it was during installation
                    if regType == "REG_BINARY":  # If the value type is binary, we need to encode our data before we check against it
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:  # Here, we convert the stored data to the encoding used by winreg, to allow comparison
                            key_value_exists = True  # If the value is the same as the value we recorded during installation, we don't need to change it
                    else:
                        if stored_value_info[0] == value_info[0]:  # If the value is the same as the value we recorded during installation, we don't need to change it
                            key_value_exists = True
            except:  # If the key value doesn't exist(likely because it was deleted by an uninstall)
                key_value_exists = False
            if not key_value_exists:  # If the key value
                try:
                    value_type = int(regStringTypes.index(stored_value_info[1]))  # This retrieves the integer that denotes the value type
                    if str(stored_value_info[0]) == "0" and value_type == 1:
                        stored_value_info[0] = ""
                    if value_type == 1:
                        stored_value_info[0] = str(stored_value_info[0])
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass
    # HKCC Restore - Commenting as above
    for key_path in hkcc_keys:
        key_value_dict = hkcc_dict[key_path]
        value_names = key_value_dict.keys()
        key_path = key_path.split("\\")
        final_key_path = ""
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_CONFIG, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_CONFIG, final_key_path)
        for value_name in value_names:
            stored_value_info = key_value_dict[value_name]
            try:
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]
                key_value_exists = False
                if regType == stored_value_info[1]:
                    if regType == "REG_BINARY":
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:
                            key_value_exists = True
                    else:
                        if stored_value_info[0] == value_info[0]:
                            key_value_exists = True
            except Exception as e:
                key_value_exists = False
            if not key_value_exists:
                try:
                    value_type = int(regStringTypes.index(
                        stored_value_info[1]))  # This retrieves the integer that denotes the value type
                    if str(stored_value_info[0]) == "0" and value_type == 1:
                        stored_value_info[0] = ""
                    if value_type == 1:
                        stored_value_info[0] = str(stored_value_info[0])
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass

    #HKLM SOFTWARE - Commenting as above
    for key_path in software_keys:
        key_value_dict = software_dict[key_path]
        value_names = key_value_dict.keys()
        key_path = key_path.split("\\")
        final_key_path = "SOFTWARE"  # Because we have seperated the subhives of HKLM, we need to specify the subhive here
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, final_key_path)
        for value_name in value_names:
            stored_value_info = key_value_dict[value_name]
            try:
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]
                key_value_exists = False
                if regType == stored_value_info[1]:
                    if regType == "REG_BINARY":
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:
                            key_value_exists = True
                    else:
                        if stored_value_info[0] == value_info[0]:
                            key_value_exists = True
            except Exception as e:
                print(e)
                key_value_exists = False
            if not key_value_exists:
                try:
                    value_type = int(regStringTypes.index(
                        stored_value_info[1]))  # This retrieves the integer that denotes the value type
                    if str(stored_value_info[0]) == "0" and value_type == 1:
                        stored_value_info[0] = ""
                    if value_type == 1:
                        stored_value_info[0] = str(stored_value_info[0])
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass
    for key_path in hardware_keys:
        key_value_dict = hardware_dict[key_path]
        value_names = key_value_dict.keys()
        key_path = key_path.split("\\")
        final_key_path = "HARDWARE"
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, final_key_path)
        for value_name in value_names:
            stored_value_info = key_value_dict[value_name]
            try:
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]
                key_value_exists = False
                if regType == stored_value_info[1]:
                    if regType == "REG_BINARY":
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:
                            key_value_exists = True
                    else:
                        if stored_value_info[0] == value_info[0]:
                            key_value_exists = True
            except Exception as e:
                pass
                key_value_exists = False
            if not key_value_exists:
                try:
                    value_type = int(regStringTypes.index(
                        stored_value_info[1]))  # This retrieves the integer that denotes the value type
                    if str(stored_value_info[0]) == "0" and value_type == 1:
                        stored_value_info[0] = ""
                    if value_type == 1:
                        stored_value_info[0] = str(stored_value_info[0])
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass
    for key_path in sam_keys:
        key_value_dict = sam_dict[key_path]
        value_names = key_value_dict.keys()
        key_path = key_path.split("\\")
        final_key_path = "SAM"
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, final_key_path)
        for value_name in value_names:
            stored_value_info = key_value_dict[value_name]
            try:
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]
                key_value_exists = False
                if regType == stored_value_info[1]:
                    if regType == "REG_BINARY":
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:
                            key_value_exists = True
                    else:
                        if stored_value_info[0] == value_info[0]:
                            key_value_exists = True
            except Exception as e:
                pass
                key_value_exists = False
            if not key_value_exists:
                try:
                    value_type = int(regStringTypes.index(
                        stored_value_info[1]))  # This retrieves the integer that denotes the value type
                    if str(stored_value_info[0]) == "0" and value_type == 1:
                        stored_value_info[0] = ""
                    if value_type == 1:
                        stored_value_info[0] = str(stored_value_info[0])
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass
    for key_path in security_keys:
        key_value_dict = security_dict[key_path]
        value_names = key_value_dict.keys()
        key_path = key_path.split("\\")
        final_key_path = "SECURITY"
        for path_segment in key_path:
            final_key_path = os.path.join(final_key_path, path_segment)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, final_key_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, final_key_path)
        for value_name in value_names:
            stored_value_info = key_value_dict[value_name]
            try:
                value_info = winreg.QueryValueEx(key, value_name)
                regType = regStringTypes[value_info[1]]
                key_value_exists = False
                if regType == stored_value_info[1]:
                    if regType == "REG_BINARY":
                        if bytes.fromhex(stored_value_info[0]) == value_info[0]:
                            key_value_exists = True
                    else:
                        if stored_value_info[0] == value_info[0]:
                            key_value_exists = True
            except Exception as e:
                key_value_exists = False
            if not key_value_exists:
                try:
                    value_type = int(regStringTypes.index(stored_value_info[1]))
                    winreg.SetValueEx(key, value_name, 0, value_type, stored_value_info[0])
                    print("Key: " + final_key_path + ", Value Name: " + value_name + " created")
                except Exception as e:
                    print("*********")
                    print("Value Creation Failed: " + str(e))
                    print(value_name)
                    print("value: " + str(stored_value_info[0]))
                    print("Type: " + stored_value_info[1])
                    print("***********")
            else:
                pass


user_selection = int(input("Do you wish to backup a program using its template file(1), or restore it(2):  "))
if user_selection == 1:
    backup_program_files()
elif user_selection == 2:
    restore_backup_program_files()
else:
    print("Invalid Selection Made")


