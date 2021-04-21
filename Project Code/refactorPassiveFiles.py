import json

'''This function opens a file containing file paths that we want to ignore, retrieves these file paths and returns them'''
def returnListOfPathsToIgnore():
    listOfPathsToIgnore = []  # Return list
    with open('newPassive.txt') as file:  # This file contains a list of file paths that we want to ignore
        unformatedListOfPathsToIgnore = file.readlines()  # Pulls the filepaths from the file
        for path in unformatedListOfPathsToIgnore:
            try:
                indexToStartOn = path.index(('/'))-2  # This represents the start of the file path
            except ValueError:  # Some lines in the passive files could be empty
                continue
            formattedPath = path[indexToStartOn:]  # Pulls the path from the line
            if formattedPath in listOfPathsToIgnore:  # Ensures that paths aren't duplicated
                continue
            else:
                listOfPathsToIgnore.append(formattedPath)  # Adds the path to the return list
    return listOfPathsToIgnore
