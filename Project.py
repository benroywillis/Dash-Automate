import Util
from Command import Command as cm
import SQL
import json
import logging
import time
import re

"""
@brief Represents a project to be build by Dash-Automate

Each project has a build flow (either GNU Makefile or CMake) and produces bitcodes.
Special flags and commands are specified in the project's input JSON file.
"""
class Project:
    def __init__(self, rootPath, path, buildFolder, jsonName):
        """
        @brief Configures command object
        @param[in] rootPath     Absolute path to the root directory of the corpus build
        @param[in] path         Absolute path to the project folder (the folder where the buildflow file exists)
        @param[in] buildFolder  Name of the build folder for the project. 
        """
        # Flag indicating that this project is a valid project for the Dash-Automate build flow
        self.Valid = True
        # Absolute path to the project directory
        self.projectPath = path if path.endswith("/") else path+"/"
        # relative path to the project from the root build folder
        self.relPath = Util.getPathDiff(rootPath, path, build=False)
        # Absolute path to the project build folder
        self.buildPath = self.projectPath+buildFolder+"/"
        self.logger = logging.getLogger("Project: "+Util.getPathDiff(rootPath, self.projectPath))
        # Name of the input JSON file
        self.jsonName = jsonName
        # Dictionary of the projects input JSON file
        self.compileJSON =  self.getJSONDict()
        if self.compileJSON == None:
            # Can't find the input JSON. Quit
            self.Valid = False
            return
        # Command to build the project
        self.buildCommand = self.getBuildCommand()
        # Dictionary that has resulting bitcode filenames as key and LFLAGS and RARGS for that bitcode as values
        self.Bitcodes = dict()
        # Name of the script to pass to the Command class
        self.scriptName = "BuildFlow.sh"
        # Name of the log file for the bash script
        self.logFile = "BuildFlow.log"
        # Command object to use for building 
        self.Command = cm(self.projectPath, scriptPath=self.buildPath+"scripts/", logFilePath=self.buildPath+"logs/", partition=["Dash"], environment=Util.SourceScript)
        # JobID this project will have when building
        self.jobID = -1
        # Flag indicating whether or not this project is currently building
        self.building = False
        # SQL pushing object
        self.PSQL = SQL.ProjectSQL(self.relPath, self.compileJSON)
        # SQL ID assigned to entry
        self.ID = -1
        # Flag indicating errors in the build flow
        self.errors = False

    def __hash__(self):
        return hash(self.projectPath)

    def __eq__(self, other):
        if isinstance(other, Project):
            return self.projectPath == other.projectPath
        return NotImplemented

    def __neq__(self, other):
        if isinstance(other, Project):
            return self.projectPath != other.projectPath
        return NotImplemented

    def getJSONDict(self):
        """
        @brief      Reads in the input json file and returns its dictionary.
        @param[in]  path        Path to the relative directory of the project
        @param[in]  args        Dictionary of the input arguments
        @param[in]  name        Name of the .json file to be read.
        @retval     jsonDict    Dictionary of the input .json
        """
        localJsons = Util.getLocalFiles(self.projectPath, suffix=".json")
        for fjson in localJsons:
            if(self.jsonName == fjson):
                try:
                    jsonDict = json.load(open(self.projectPath+self.jsonName))
                except:
                    continue
                return jsonDict
        self.logger.critical("Could not find input JSON file for project {}".format(self.projectPath))
        return None

    def getBuildCommand(self):
        """
        @brief  Parses the input compileD dictionary for a make command
        @info   This is written specifically for GNU Makefiles. More work will need to be done for CMake compatibility.
        @retval compileCommands     Value retrieved from the Build: { Commands : } field
                                    This value is a string, where multiple build commands will be separated by &, the parallel operator in bash.
        """
        compileCommands = None
        returnString = ""
        # parse the compile.json build field
        if self.compileJSON.get("Build", None) is not None:
            # grab the command data specified, if any (can be string or list)
            if self.compileJSON["Build"].get("Commands", None) is not None:
                compileCommands = self.compileJSON["Build"]["Commands"]

        if compileCommands == None:
            return "make -k"
        if isinstance(compileCommands, str):
            comm = Util.replaceVariables(compileCommands, self.compileJSON["Build"].get("Variables", None))
            # process the given command for emptiness  -k flag
            kFlag = comm.find(" -k ")
            if kFlag < 0:
                comm += " -k "
            returnString = comm
        elif isinstance(compileCommands, list):
            commandStrings = []
            for comm in compileCommands:
                commandStrings.append( Util.replaceVariables(comm, self.compileJSON["Build"].get("Variables", None)) )
            returnString = " && ".join(x for x in commandStrings)
        else:
            logging.critical("Compile commands must be a string or list.")
            self.Valid = False

        return returnString

    def run(self):
        """
        @brief Runs the build flow.

        If the appropriate flag telling the build flow to keep progressing after errors is not set, it will be added by Dash-Automate.
        """
        # generate a build folder with logs and scripts folder embedded in it
        self.Command.generateFolder(Name=self.buildPath, subfolders=["scripts","logs"])
        # create appropriate bash script prefix
        prefix = "cd "+self.projectPath+" ; "
        self.buildCommand = prefix+self.buildCommand
        # generate script that will build our project and put it in th,e build/scripts folder
        bashfile = self.Command.constructBashFile(self.scriptName, self.buildCommand)
        # run the script and return the process ID or SLURM ID
        self.jobID = self.Command.run(bashfile)
        if self.Command.poll(self.jobID):
            self.building = True

    def done(self):
        """
        @brief Monitors the project's active build job. If the job has completed, a bitcode map for the project, specifying the LFLAGS and RARGS for each one is generated.
        @retval Returns False if an active job is still active, True if there are no active jobs and all housekeeping has been taken care of
        """
        if self.Command.poll(self.jobID, checkDependencies=False):
            return False
        else:
            time.sleep(0.1)        
            bitcodes = Util.getLocalFiles(self.projectPath, suffix=[".bc",".o"])
            if len(bitcodes) > 0:
                self.parseBitcodes( bitcodes )
                self.Command.moveFiles(bitcodes, self.projectPath, self.buildPath)
                self.parseErrors()
                self.PSQL.push()
                self.ID = self.PSQL.ID
            else:
                self.parseErrors()
                
            return True

    def parseBitcodes(self, bitcodes):
        """
        @brief Maps bitcodes to their respective RARGS and LFLAGS
        @param[in] bitcodes List of bitcode file names only
        """
        LFLAGsDict = Util.getLFLAGSDict(self.compileJSON)
        if LFLAGsDict == None:
            self.Valid = False
        RARGSDict = Util.getRARGSDict(self.compileJSON)
        if RARGSDict == None:
            self.Valid = False
        if not self.Valid:
            self.errors = True
            self.Bitcodes = []
            return

        for name in bitcodes:
            BCname = name.split(".")[0]
            self.Bitcodes[name] = dict()
            self.Bitcodes[name]["LFLAGS"] = []
            self.Bitcodes[name]["RARGS"] = []
            found = False
            for key in LFLAGsDict:
                if BCname == key:
                    self.Bitcodes[name]["LFLAGS"] = LFLAGsDict[key]
                    found = True
            if not found:
                # maintain backward compatibility with old "general" key
                if LFLAGsDict.get("general", None) is not None:
                    self.Bitcodes[name]["LFLAGS"] = LFLAGsDict["general"]
                elif LFLAGsDict.get("default", None) is not None:
                    self.Bitcodes[name]["LFLAGS"] = LFLAGsDict["default"]

            found = False
            for key in RARGSDict:
                if BCname == key:
                    self.Bitcodes[name]["RARGS"] = RARGSDict[BCname]
                    found = True
            if not found:
                # maintain backward compatibility with old "general" key
                if RARGSDict.get("general", None) is not None:
                    self.Bitcodes[name]["RARGS"] = RARGSDict["general"]
                elif RARGSDict.get("default", None) is not None:
                    self.Bitcodes[name]["RARGS"] = RARGSDict["default"]

            if len(self.Bitcodes[name]["LFLAGS"]) == 0:
                self.Bitcodes[name]["LFLAGS"] = [""]
            if len(self.Bitcodes[name]["RARGS"]) == 0:
                self.Bitcodes[name]["RARGS"] = [""]

    def parseErrors(self):
        """
        @brief Looks through build flow log for keywords to indicate problems with the build flow
        """
        try:
            log = open(self.buildPath+"logs/"+self.logFile,"r")
        except:
            self.logger.warn("Could not find build flow log file.")
            return
        errors = []
        for line in log:
            errors += re.findall(".*error.*", line)
        if len(errors) > 0:
            self.errors = True
