import registryScanner  # Contains our registry scanner code
import sys  # Used to ensure that the program has administrator access
from watchdog.observers import Observer  # File scanner
from watchdog.events import PatternMatchingEventHandler  # File scanner type that allows us to ignore certain files
import refactorPassiveFiles  # Used to retrieve list of files that watchdog should ignore
import datetime  # Used to create a timestamp for the registry scanner
import eel  # Used to reveal functions to the web application
import ctypes  # Used to ensure that the program is running with administrator permissions
import threading  # Used to move the file scanner to a thread
import json  # Used to store data from the scanners
import re  # Used to locate the timestamp and registry path from registry keys

'''The following global variables are used to store the paths of files that have changed, so that we can
track changes to the file system during installation. They are global because the functions that change them are
called by the Watchdog library, rather than our code, and so this is the easiest way to track the changes to the 
file system'''
files_created = []
files_deleted = []
files_modified = []
files_moved = {}  # Files moved have a source and destination, a dictionary is used so that we can store both
observer = None  # Observer is a global variable to allow it to be controlled by the registry scanner function
current_time = None  # Current time is a global variable to allow it to be accessed by the file and registry scanners
ignore_patterns = refactorPassiveFiles.returnListOfPathsToIgnore()  # This function returns a list of file paths that we want to ignore
template_name = ""  # This global variable stores the name input by the user, which is used to name the template file
'''This function is used to create the dictionary that is to be stored in the JSON file. It does this by
retrieving the outputs of both scanners, and labelling them appropriately
hkcc_match: tuple containing the output of the registry scanner for the HKCC hive
hardware_match: tuple containing the output of the registry scanner for the HARDWARE sub-hive
hkcu_match: tuple containing the output of the registry scanner for the HKCU hive
sam_match: tuple containing the output of the registry scanner for the SAM sub-hive
security_match: tuple containing the output of the registry scanner for the SECUIRTY sub-hive
software_match: tuple containing the output of the registry scanner for the SOFTWARE sub-hive'''
def create_dict_for_json(hkcc_match, hardware_match, hkcu_match, sam_match, security_match, software_match):
    dict_to_convert = {}  # This is the return dictionary for the function, containing the labelled scanner outputs
    global files_created
    global files_deleted
    global files_modified
    '''The final_files_created list is used to store a list of file creations that we want to store in the 
    template file. We are only interested in files that still exist at the end of the installation, because if
    a file is created and deleted, then it was a temporary file that we can ignore. Therefore, we remove any file
    paths that appear in both the files_created and files_deleted list, and store the remaining paths in this 
    list'''
    final_files_created = []
    for i in files_created:
        if i not in files_deleted:  # If the file has been created and has not been deleted
            final_files_created.append(i)
    final_files_deleted = []  # Stores deleted file paths that were not temp files
    for i in files_deleted:
        if i not in files_created:
            final_files_deleted.append(i)
    global files_moved
    files_modified = list(set(files_modified))  # By converting the list to a set, we remove duplicate entries
    dict_to_convert["files_created"] = final_files_created
    dict_to_convert["files_deleted"] = final_files_deleted
    dict_to_convert["files_modified"] = files_modified
    dict_to_convert["files_moved"] = files_moved
    '''Each return from the registry scanner is a tuple consisting of three lists, one of modified keys, one
    of deleted keys and one of created keys. Here, we split them back into these lists, and label them, to aid 
    readability and make it easier to access them from the JSON file'''
    dict_to_convert["hkcc_modified"] = hkcc_match[0]
    dict_to_convert["hkcc_deleted"] = hkcc_match[1]
    dict_to_convert["hkcc_created"] = hkcc_match[2]
    dict_to_convert["hardware_modified"] = hardware_match[0]
    dict_to_convert["hardware_deleted"] = hardware_match[1]
    dict_to_convert["hardware_created"] = hardware_match[2]
    dict_to_convert["hkcu_modified"] = hkcu_match[0]
    dict_to_convert["hkcu_deleted"] = hkcu_match[1]
    dict_to_convert["hkcu_created"] = hkcu_match[2]
    dict_to_convert["sam_modified"] = sam_match[0]
    dict_to_convert["sam_deleted"] = sam_match[1]
    dict_to_convert["sam_created"] = sam_match[2]
    dict_to_convert["security_modified"] = security_match[0]
    dict_to_convert["security_deleted"] = security_match[1]
    dict_to_convert["security_created"] = security_match[2]
    dict_to_convert["software_modified"] = software_match[0]
    dict_to_convert["software_deleted"] = software_match[1]
    dict_to_convert["software_created"] = software_match[2]
    return dict_to_convert


'''This function is used to store the information returned by the scanners for later use. It stores the 
information as a JSON dictionary, for ease of access and manipulation
json_dict: The dictionary created by the create_dict_for_json() function, containing the output from both scanners'''
def save_json(json_dict):
    global template_name  # Retrieves the template name that the user has input
    file_name = template_name + ".txt"  # Template name will be the name of the program the information refers to
    with open(file_name, 'w') as outfile:
        json.dump(json_dict, outfile)  # Stores the dictionary as a JSON object in a text file


'''This function is used to handle file creation events. It stores the path of the file creation to the 
files_created list
event: The watchdog event object containing the path of the event'''
def on_created(event):  # Runs when a file is created
    global files_created  # Retrieves the list of file paths of files created during the program installation
    global ignore_patterns  # Retrieves the list of paths that are to be ignored because they are updated by sources other than the installation that we are tracking
    matchFound = False  # Control variable for the filter process
    '''To avoid the problems caused by backslash being an escape character, we remove all backslashes from both the
    filepath we are checking, and the filepaths that we want to ignore, allowing us to compare them without issue'''
    filePath = re.escape(str(event.src_path).strip().replace("\\", ""))
    for pattern in ignore_patterns:  # Iterates through each path that we want to ignore
        pattern = re.escape(str(pattern).strip().replace("\\", ""))
        if re.search(pattern, filePath):  # If the filepath we are checking is the same as a filepath that we want to ignore, or a subpath of a path we want to ignore
            matchFound = True
            break
    if not matchFound:  # If the path is related to the installation we are tracking
        files_created.append(event.src_path)


'''This function is used to handle file deletion events. Commenting as above'''
def on_deleted(event):
    global files_deleted
    global ignore_patterns
    matchFound = False
    filePath = re.escape(str(event.src_path).strip().replace("\\", ""))
    for pattern in ignore_patterns:
        pattern = re.escape(str(pattern).strip().replace("\\", ""))
        if re.search(pattern, filePath):
            matchFound = True
            break
    if not matchFound:
        files_deleted.append(event.src_path)


'''This function is used to handle file modification events. Commenting as above'''
def on_modified(event):
    global files_modified
    global ignore_patterns
    matchFound = False
    filePath = re.escape(str(event.src_path).strip().replace("\\", ""))
    for pattern in ignore_patterns:
        pattern = re.escape(str(pattern).strip().replace("\\", ""))
        if re.search(pattern, filePath):
            matchFound = True
            break
    if not matchFound:
        files_modified.append(event.src_path)


'''This function is used to handle file moving events. Commenting as above'''
def on_moved(event):
    global files_moved
    global ignore_patterns
    matchFound = False
    filePath = re.escape(str(event.src_path).strip().replace("\\", ""))
    for pattern in ignore_patterns:
        pattern = re.escape(str(pattern).strip().replace("\\", ""))
        if re.search(pattern, filePath):
            matchFound = True
            break
    if not matchFound:
        files_moved[event.src_path] = event.dest_path  # Store the source and destination paths as a key and value in the dictionary


'''This function is used to ensure that the program has the administrator access required to access the registry'''
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # Returns true if the program has administrator access
    except:
        return False


'''This function is used to start the file system scanner'''
def startFileSystemScan():
    global observer  # Retrieves the observer object created by the triggerFileScan() function
    observer.start()  # Begins monitoring of the file system
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:  # Allows the file scanner to be stopped by a keyboard interrupt(Ctrl-C)
        observer.stop()


'''This function handles the execution of the registry scanner functions from registryScanner.py and returns
each scanner's results to the calling function. Each scan is executed by passing the registry hive's names to
the detect_registry_changes function, along with the start time of the installation'''
def beginRegistryScan():
    global current_time  # Retrieves the start time of the installation to allow the registry scanner to make comparisons
    registryScanner.getCopyOfRegistry()  # Creates the "after" snapshot of the registry
    hkcc_matches = registryScanner.detect_registry_changes(current_time, "HKCC", "HKCCInitial.dat")
    hardware_matches = registryScanner.detect_registry_changes(current_time, "Hardware", "HARDWAREInitial.dat")
    hkcu_matches = registryScanner.detect_registry_changes(current_time, "HKCU", "HKCUInitial.dat")
    sam_matches = registryScanner.detect_registry_changes(current_time, "SAM", "SAMInitial.dat")
    security_matches = registryScanner.detect_registry_changes(current_time, "SECURITY", "SECURITYInitial.dat")
    software_matches = registryScanner.detect_registry_changes(current_time, "software", "SOFTWAREInitial.dat")
    return hkcc_matches, hardware_matches, hkcu_matches, sam_matches, security_matches, software_matches


eel.init('web')  # This function points the Eel webserver at the web folder


'''This function is used to create and set up the file system scanner object and create the "before" snapshot
of the registry. It is triggered directly by the user through the web application
program_name: The name that the user inputs for the template file'''
@eel.expose  # This line allows the javascript for the webserver to trigger this function
def triggerFileScan(program_name):
    global template_name
    template_name = program_name
    registryScanner.getInitialCopyOfRegistry()  # Creates a copy of the registry
    global current_time
    current_time = datetime.datetime.now(datetime.timezone.utc)  # Sets the start time of the installation
    patterns = "*"  # Specifies that the scanner should scan for all file changes on the system
    ignore_patterns = refactorPassiveFiles.returnListOfPathsToIgnore()  # Gives the list of files for the scanner to ignore
    ignore_directories = False  # Allows the scanner to detect when folders have been created/changed/deleted/moved
    case_sensitive = True
    # This event handler type allows us to ignore files in the list we have passed to it
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created  # Binds file creation events to our on_created function
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved
    path = "C://"  # Scan the entire filesystem
    global observer  # Makes the observer handler global, to allow it to be terminated by the registry scanner
    observer = Observer()
    observer.schedule(my_event_handler, path, recursive=True)  # Recursive allows the scanner to check subfolders
    # This line calls the function that starts the file scanner, it is threaded to allow the main execution to continue
    x = threading.Thread(target=startFileSystemScan, args=())
    x.start()
    return "Scanning File System"  # This is returned to the user via an alert box on the webpage


'''This function stops the file scanner and begins the registry scanner function. It uses the information 
returned by the registry scanners and file scanners to create a JSON dictionary, and calls the function that
stores the JSON dictionary in a file'''
@eel.expose
def terminate_file_scan_and_start_registry_scan():
    global observer
    observer.stop()  # Stops the file scanner
    hkcc, hardware, hkcu, sam, security, software = beginRegistryScan()  # Add the other registry keys
    json_dictionary = create_dict_for_json(hkcc, hardware, hkcu, sam, security, software)
    save_json(json_dictionary)  # Creates the template file
    return "Template Successfully Created"


''' This function starts the Eel webserver. The mode parameter tells Eel which browser to open, we set this to
None because we create the browser window for the Eel server in the WXTray program'''
eel.start('main.html', mode=None)


if is_admin():
    print("System Scanner Ready")
else:
    ' This function asks the user to give the program administrator access'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
