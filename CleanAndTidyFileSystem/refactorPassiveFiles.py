import json

'''This function takes the files of passively changed files that the scanner has found, and converts them
 to a list of files to ignore'''
def returnListOfPathsToIgnore():
    listOfPathsToIgnore = []
    with open('passive_files.txt') as file:
        unformatedListOfPathsToIgnore = file.readlines()
        for path in unformatedListOfPathsToIgnore:
            try:
                indexToStartOn = path.index(('/'))-2  # This represents the start of the file path
            except ValueError:  # Some lines in the passive files are empty
                continue
            formattedPath = path[indexToStartOn:]  # Pulls the path from the line
            if formattedPath in listOfPathsToIgnore:  # Ensures that paths aren't duplicated
                continue
            else:
                listOfPathsToIgnore.append(formattedPath)
    with open('passive.txt') as f:
        data = json.load(f)
        paths_mod = (data["files_modified"])
        paths_del = (data["files_deleted"])
        paths_cre = (data["files_created"])
        for path in paths_mod:
            listOfPathsToIgnore.append(path)
        for path in paths_del:
            listOfPathsToIgnore.append(path)
        for path in paths_cre:
            listOfPathsToIgnore.append(path)
    print("help")
    return listOfPathsToIgnore
