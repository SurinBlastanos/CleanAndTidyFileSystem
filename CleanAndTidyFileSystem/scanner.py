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

files_created = []
files_deleted = []
files_modified = []
files_moved = {}  # Files moved have a source and destination, a dictionary is used so that we can store both
observer = None  # Observer is a global variable to allow it to be controlled by the registry scanner function
current_time = None  # Current time is a global variable to allow it to be accessed by the file and registry scanners

'''This function is used to create the dictionary that is to be stored in the JSON file. It does this by
retrieving the information about created, modified and deleted information from both scanner types'''
def create_dict_for_json(hkcc_match, hardware_match, hkcu_match, sam_match, security_match):
    dict_to_convert = {}
    dict_to_convert["files_created"] = files_created
    dict_to_convert["files_deleted"] = files_deleted
    dict_to_convert["files_modified"] = files_modified
    dict_to_convert["files_moved"] = files_moved
    dict_to_convert["hkcc_modified"] = hkcc_match[0]
    dict_to_convert["hkcc_created"] = hkcc_match[1]
    dict_to_convert["hkcc_deleted"] = hkcc_match[2]
    dict_to_convert["hardware_modified"] = hardware_match[0]
    dict_to_convert["hardware_created"] = hardware_match[1]
    dict_to_convert["hardware_deleted"] = hardware_match[2]
    dict_to_convert["hkcu_modified"] = hkcu_match[0]
    dict_to_convert["hkcu_created"] = hkcu_match[1]
    dict_to_convert["hkcu_deleted"] = hkcu_match[2]
    dict_to_convert["sam_modified"] = sam_match[0]
    dict_to_convert["sam_created"] = sam_match[1]
    dict_to_convert["sam_deleted"] = sam_match[2]
    dict_to_convert["security_modified"] = security_match[0]
    dict_to_convert["security_created"] = security_match[1]
    dict_to_convert["security_deleted"] = security_match[2]
    print("-------------------------------------------------")
    # Add the other registry hives
    return dict_to_convert


'''This function is used to store the information returned by the scanners for later use. It stores the 
information as a JSON dictionary, for ease of access and manipulation'''
def save_json(json_dict, template_name):
    file_name = template_name + ".txt"  # Template name will be the name of the program the information refers to
    with open(file_name, 'w') as outfile:
        json.dump(json_dict, outfile)


'''This function is used to handle file creation events. It stores the path of the file creation to the 
files_created list'''
def on_created(event):  # Runs when a file is created
    print("Created")  # Debugging information
    sequence = 'User Data'  # The scanner was picking up dozens of events from microsoft edge's "User Data" ...
    ignore_this = re.search(sequence, event.src_path)  # ...folder, these lines ignore files from this location...
    ignore_that = re.search("edge", event.src_path)  # ...to prevent false positives
    if not ignore_this and not ignore_that:
        print(event.src_path)  # Debugging information
        files_created.append(event.src_path)


'''This function is used to handle file deletion events. Commenting as above'''
def on_deleted(event):
    print("Deleted")
    sequence = 'User Data'
    ignore_this = re.search(sequence, event.src_path)
    ignore_that = re.search("edge", event.src_path)
    if not ignore_this and not ignore_that:
        print(event.src_path)
        files_deleted.append(event.src_path)


'''This function is used to handle file modification events. Commenting as above'''
def on_modified(event):
    print("Modified")
    sequence = 'User Data'
    ignore_this = re.search(sequence, event.src_path)
    ignore_that = re.search("edge", event.src_path)
    if not ignore_this and not ignore_that:
        print(event.src_path)
        files_modified.append(event.src_path)


'''This function is used to handle file moving events. Commenting as above'''
def on_moved(event):
    print("HELLO")
    print(event.src_path)
    sequence = 'User Data'
    ignore_this = re.search(sequence, event.src_path)
    ignore_that = re.search("edge", event.src_path)
    if not ignore_this and not ignore_that:
        files_moved[event.src_path] = event.dest_path


'''This function is used to ensure that the program has the administrator access required to access the registry'''
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # Returns true if the program has administrator access
    except:
        return False


'''This function is used to start the file system scanner'''
def startFileSystemScan():
    global observer
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:  # Allows the file scanner to be stopped by a keyboard interrupt(Ctrl-C)
        observer.stop()
    # observer.join()


'''This function handles the execution of the registry scanner functions from registryScanner.py and returns
each scanner's results to the calling function. Each scan is executed by passing the registry hive's names to
the detect_registry_changes function, along with the start time o the installation'''
def beginRegistryScan():
    global current_time  # Retrieves the start time of the installation to allow the registry scanner to make comparisons
    print(current_time)
    registryScanner.getCopyOfRegistry()  # Creates the "after" snapshot of the registry
    print("Starting Comparisons")
    hkcc_matches = registryScanner.detect_registry_changes(current_time, "HKCC", "HKCCInitial.dat")
    print(hkcc_matches)
    print("First comparisons complete")
    hardware_matches = registryScanner.detect_registry_changes(current_time, "Hardware", "HARDWAREInitial.dat")
    print(hardware_matches)
    print("2 comparisons complete")
    # hkcr_matches = registryScanner.detect_registry_changes(current_time, "HKCR", "HKCRInitial.dat")
    # print("3 comparisons complete")
    hkcu_matches = registryScanner.detect_registry_changes(current_time, "HKCU", "HKCUInitial.dat")
    print(hkcu_matches)
    print("4 comparisons complete")
    sam_matches = registryScanner.detect_registry_changes(current_time, "SAM", "SAMInitial.dat")
    print(sam_matches)
    print("5 comparisons complete")
    security_matches = registryScanner.detect_registry_changes(current_time, "SECURITY", "SECURITYInitial.dat")
    print(security_matches)
    print("6 comparisons complete")
    # software_matches = registryScanner.detect_registry_changes(current_time, "software", "SOFTWAREInitial.dat")
    # print("7 comparisons complete")
    # system_matches = registryScanner.detect_registry_changes(current_time, "SYSTEM", "SYSTEMInitial.dat")
    # print("complete")
    return hkcc_matches, hardware_matches, hkcu_matches, sam_matches, security_matches  # hkcr_matches, software_software, system_matches

# This function points the Eel webserver that is used as the controller for the scanner functions at the web folder
eel.init('web')

'''This function is used to create and set up the file system scanner object and create the "before" snapshot
of the registry. It is triggered directly by the user through the web application'''
@eel.expose  # This line allows the javascript for the webserver to trigger this function
def triggerFileScan():
    x = threading.Thread(target=registryScanner.getInitialCopyOfRegistry, args=())  # Creates a copy of the registry
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


'''This function stops the file scanner and begins the registry scanner function. It uses the information 
returned by the registry scanners and file scanners to create a JSON dictionary, and calls the function that
stores the JSON dictionary in a file'''
@eel.expose
def terminate_file_scan_and_start_registry_scan():
    global observer
    observer.stop()
    hkcc, hardware, hkcu, sam, security = beginRegistryScan()  # Add the other registry keys
    json_dictionary = create_dict_for_json(hkcc, hardware, hkcu, sam, security)
    save_json(json_dictionary, "test")  # Creates the template file
    return "This function executes"  # Debugging information


'''# This function starts the Eel webserver. For testing purposes, it is set to "edge", but it could be set to
a browser of the user's choice'''
eel.start('main.html', mode=None)


if is_admin():
    print("hello")
else:
    ' This function asks the user to give the program administrator access'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
