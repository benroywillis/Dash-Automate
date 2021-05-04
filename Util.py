import argparse
import os
import time
import subprocess as sp
import json
import logging
import re
import collections
import ctypes

globLog = logging.getLogger("Util")

### Global Definitions
SourceScript = "export " +\
    "CC='clang-9 -flto -DENABLE_TRACING' " +\
    "CXX='clang++-9 -flto -DENABLE_TRACING' " +\
    "DASH_DATA='/mnt/nobackup-09/Dash/Data/' " +\
    "DASH_ROOT='/mnt/nobackup-09/Dash/Sources/' " +\
    "LDFLAGS='-fuse-ld=lld-9 -Wl,-plugin-opt=emit-llvm' " +\
    "LIBRARY_PATH='/mnt/nobackup-09/Dash/Sources/lib/' " +\
    "LD_LIBRARY_PATH='/mnt/nobackup-09/Dash/Sources/lib/' " +\
    "AR='llvm-ar-9' " +\
    "NM='llvm-nm-9' " +\
    "RANLIB='/bin/true' " +\
    "READELF='llvm-readelf-9' ; "
    
### General Utilities
def flatten(input):
    if isinstance(input, collections.Iterable):
        for entry in input:
            if isinstance(entry, collections.Iterable) and not isinstance(entry, (str, bytes)):
                yield from flatten(entry)
            else:
                yield entry
    else:
        yield input

def getLocalFiles(path, suffix="", prefix=""):
    """
    @function 	listJsons
    @author 	Ben Willis
    @brief 	This function searches the directory specified by path for all files ending in 
                suffix and returns a list.
    @param[in] 	path 		Specifies the path from root to the local directory.
    @param[in]  prefix          File prefix used to search for files. Can be a string or list.
    @param[in]  suffix          File suffix used to search for files. Can be a string or list.
    @retval 	localFiles      List of all files in the <path> directory ending in .<suffix>
    """
    localList = os.listdir(path)
    localFiles = []
    if isinstance(suffix, list):
        for suff in suffix:
            if isinstance(prefix, list):
                for pre in prefix:
                    for localfile in localList:
                        if localfile.endswith(suff) and localfile.startswith(pre):
                            localFiles.append(localfile)
                    
            elif isinstance(prefix, str):
                for localfile in localList:
                    if localfile.endswith(suff) and localfile.startswith(prefix):
                        localFiles.append(localfile)
    elif isinstance(suffix, str):
        if isinstance(prefix, list):
            for pre in prefix:
                    for localfile in localList:
                        if localfile.endswith(suffix) and localfile.startswith(pre):
                            localFiles.append(localfile)
        elif isinstance(prefix, str):
            for localfile in localList:
                if localfile.endswith(suffix) and localfile.startswith(prefix):
                    localFiles.append(localfile)
            
    return localFiles

def getPathDiff(source, sink, build=True):
    """
    @function   getPushPath
    @brief      Creates a project path for this project to be used in the root table entry.
    @param[in]  source      Head of the path that is the source node in the file tree.
    @param[in]  sink        Path to the sink node, which should be the current project.
    @param[in]  build       Include a build folder name at the end of the sink path.
    @retval     returnPath  Difference between sink path and source path. Includes both the source and sink-1 (because sink is build folder).
    """
    returnPath = ""
    sourceList = source.split("/")
    sinkList = sink.split("/")
    for i in range(len(sourceList)-1, 0, -1):
        if sourceList[i] is "":
            del sourceList[i]
    sourceHead = sourceList[-1]

    for i in range(len(sinkList)-1, 0, -1):
        if sinkList[i] is "":
            del sinkList[i]

    for i in range(len(sinkList)):
        if sinkList[i] == sourceHead:
            # we've found the root, make the path start one above the head plus all on top except build_compile
            for k in range(i+1, len(sinkList)):
                if sinkList[k].startswith("build"):
                    return returnPath
                returnPath += sinkList[k]
                if k is not len(sinkList):
                    returnPath += "/"
            if not build:
                cleanPath = returnPath.split("/")
                while "" in cleanPath:
                    cleanPath.remove("")
                if cleanPath.__len__() > 1:
                    if cleanPath[-1].startswith("build"):
                        cleanPath.remove(cleanPath[-1])
                    returnPath = "/".join(x for x in cleanPath)+"/"
            return returnPath  # return this rendered path
    # if there is no intersection between the two, just return the sink absolute path
    return sink

### DashAutomate helpers
def argumentParse():
    """
    @function   argumentParse
    @brief      Parses all runtime arguments of the tool. Passed to the rest of the program as a dictionary.
    """
    arg_parser = argparse.ArgumentParser()
    # build flow configuration options and flags
    arg_parser.add_argument("-i", "--input-file", default="compile.json", help="Input JSON file name.")
    arg_parser.add_argument("-b", "--build", default="build", help="Specifiy build folder name.")
    #arg_parser.add_argument("-bo", "--bash-only", action="store_true", help="Use bash for the build flow.")
    arg_parser.add_argument("-ns", "--no-subdirectories", action="store_true", help="Ignore subdirectories specified in the .json.")
    arg_parser.add_argument("-nl", "--no-labeling", action="store_true", help="Turn off kernel labeling in the Cartographer.")
    #arg_parser.add_argument("-np", "--no-papi", action="store_true", help="Disable the PAPI step of the tool.")
    arg_parser.add_argument("-kt", "--keep-trace", action="store_true", help="Don't delete the trace during build flow.")
    arg_parser.add_argument("-P", "--project-prefix", default=os.getcwd(), help="Set path prefix to the project root folder.")
    # toolchain configuration
    arg_parser.add_argument("-cs", "--compiler-suffix", default="-9", help="Set suffix for binaries in system LLVM install.")
    arg_parser.add_argument("-tp", "--toolchain-prefix", default="/mnt/nobackup-09/Dash/Sources/", help="Specify path to the TraceAtlas toolchain installation.")
    # tracing configuration
    arg_parser.add_argument("-tc", "--trace-compression", default=9, help="Specify zlib compression level when tracing.")
    arg_parser.add_argument("-O", "--opt-level", nargs='+', default=[None,None], help="Specify string following the '-O' optimizer flag in project build flow. Enter as a whitespace-separated list: opt command flag first, clang command flag second.")
    arg_parser.add_argument("-tt", "--trace-type", default="EncodedTrace", help="Specify the type of compression a trace has. Default is EncodedTrace.")
    # cartographer configuration
    arg_parser.add_argument("-ci", "--cartographer-intermediate", action="store_true", help="Enable the intermediate csv in Cartographer.")
    # SLURM flag
    arg_parser.add_argument("-p", "--partition", nargs='+', default=['Dash'], help="Specify SLURM partition to use. Can be a whitespace-separated list of multiple partitions. Options: Spade (should only be used for cad tools), Dash (default value).")
    # database flags
    arg_parser.add_argument("-c", "--commit", action="store_true", help="Commit all results of this run to the database.")
    arg_parser.add_argument("-rid", "--run-id", default="0", help="Specify RunId to be used when pushing to SQL.")
    arg_parser.add_argument("-pid", "--previous-id", default="0", help="Specify the RunID use when calculating build diffs or project list for nightly builds.")
    arg_parser.add_argument("-nb", "--nightly-build", action="store_true", help="Enable nightly build, designed to run only the projects necessary to fully test the TraceAtlas toolchain.")
    arg_parser.add_argument("-on", "--only-new", action="store_true", help="Only build projects not present in the SQL database under RunID --previous-id.")
    arg_parser.add_argument("-dbf", "--database-file", default="/mnt/nobackup-09/Dash/Sources/tools/database/.login", help="Specify absolute path to database login file.")
    # logging
    arg_parser.add_argument("-ll", "--log-level", default="20", help="Set log level. Valid settings are 0 (Everything), 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERROR), and 50 (CRITICAL).")
    arg_parser.add_argument("-lf", "--log-file", default=os.getcwd()+"/DashAutomate.log", help="Set output log file name.")

    args = arg_parser.parse_args()
    args.log_level = int(args.log_level)
    if not args.project_prefix.endswith("/"):
        args.project_prefix+= "/"

    # a nightly build AND only new build is not possible in one run
    if args.nightly_build and args.only_new:
        exit("A nightly build and only new build is not possible in a single run!")
    return args

def readJson(path, args, name=None, subD=False):
    """
    @brief      Reads in the input json file and returns its dictionary.
    @param[in]  path        Absolute path to the relative directory of the project
    @param[in]  args        Dictionary of the input arguments
    @param[in]  name        Name of the .json file to be read.
    @retval     jsonDict    Dictionary of the input .json
    """
    localJsons = getLocalFiles(path, suffix=".json")
    if(name == None):
        jsonFile = args.input_file
        for jsonName in localJsons:
            if(jsonName == jsonFile):
                try:
                    jsonDict = json.load(open(path+'/'+jsonFile))
                except:
                    continue
                return jsonDict

        if subD:
            globLog.error("Error: No compile.json file could be found in " + path)
            return None
        else:
            exit("Error: No compile.json file could be found in " + path)
            return None
    else:
        jsonFile = name
        for jsonName in localJsons:
            if(jsonName == jsonFile):
                try:
                    jsonDict = json.load(open(path+"/"+jsonFile))
                except:
                    continue
                return jsonDict
        if subD:
            globLog.error("Error: No .json file named %s found." % jsonFile)
            return None
        else:
            exit("Error: No .json file named %s found." % jsonFile)
            return None

def parseValidSubDs(jsonDict, args):
    """
    """
    subdirectories = []
    if jsonDict.get("Subdirectories", None) is not None:
        for path in jsonDict["Subdirectories"]:
            if path.startswith("/") or path.startswith("$"):
                absPath = path if path.endswith("/") else path+"/"
            else:
                absPath = args.project_prefix+path if path.endswith("/") else args.project_prefix+path+"/"
            # if this subdirectory is a valid path
            if os.path.isdir(absPath):
                # if this subdirectory is not the path we're currently in
                if absPath.strip("/") != args.project_prefix.strip("/"):
                    subdirectories.append(absPath)
                else:
                    globLog.error("The subdirectories path '{}' is not valid. If you do not need the subdirectories functionality for this project, please remove it from your .json file.".format(absPath))
            else:
                globLog.error("The subdirectory path {} is not valid.".format(absPath))
    return subdirectories

def getSubDs(absolutePath, args):
    """
    Description
    In order to find the subprojects below us, we have to recurse into the directories specified by the compile.jsons
    This function finds and validates the subdirectories described in absolutePath/compile.json
    It also indicates whether or not there is a project to build in this current directory
    """
    jsonDict = readJson(absolutePath, args, subD=True)
    if jsonDict == None:
        subdirectories = []
        project = False
        return subdirectories, project

    if jsonDict.get("Subdirectories", None) is not None:
        subdirectories = []
        for path in jsonDict["Subdirectories"]:
            if path.startswith("/") or path.startswith("$"):
                newPath = path if path.endswith("/") else path+"/"
            else:
                newPath = absolutePath if absolutePath.endswith("/") else absolutePath+"/"
                newPath += path.strip(".") if path.strip(".").endswith("/") else path.strip(".")+"/"

            # if this subdirectory is a valid path
            if os.path.isdir(newPath):
                # if this subdirectory is not the path we're currently in
                if newPath.strip("/") != absolutePath.strip("/"):
                    subdirectories.append(newPath)
                else:
                    globLog.error("The subdirectories path '{}' is not valid. If you do not need the subdirectories functionality for this project, please remove it from your .json file.".format(newPath))
            else:
                globLog.error("The subdirectory path {} is not valid.".format(newPath))

    else:
        subdirectories = []
    if jsonDict.get("Build", None) is not None:
        project = True
    else:
        project = False
    return subdirectories, project

def recurseThroughSubDs(path, args, repPaths):
    """
    @brief      Takes this directories subdirectories and recurses into them until it reaches the bottom of the subdirectory tree.
    @param[in]  path        Absolute path to a subdirectory defined in this directory's compile.json
    @param[in]  args        Dictionary containing arguments passed to this tool
    @param[in]  repPaths    Set containing all subdirectory paths.
    @retval     repPaths    A set containing all subdirectory paths in the tree.
    """
    # we already have this compile.json subdirectories in self.subdirectories, now we have to recurse into lower ones
    reportPathList, project = getSubDs(path, args)
    if project:
        repPaths.add(path)

    # if we find some new subdirectories, recurse to them and find their subdirectories
    if len(reportPathList) > 0:
        for item in reportPathList:
            repPaths = recurseThroughSubDs(item, args, repPaths)

    return repPaths

### Project helpers
def replaceVariables(command, variableDict):
    """
    @brief Maintains backward compatibility of old compile.json format by replacing variables.

    Using variables in a command is deprecated.
    @param[in] command          Raw string to be parsed.
    @param[in] variableDict     Dictionary containing all variables from the Build field in the input JSON file
    @retval    commandString    String containing expanded variables
    """
    commandString = ""
    commandList = command.split(" ")
    for comm in commandList:
        if "%" in comm:
            if variableDict is None:
                globLog.warning("A variable was found in the build command but there wasn't a variables section in the input JSON file. This variable will be skipped.")
                commandString += ""
                continue

            var = comm.strip("%")
            varVal = ""
            test = variableDict.get(var, None)
            if test == None:
                globLog.warning("Variable "+var+" could not be found in the input JSON file. This variable will be ignored.")
            else:
                varVal = variableDict[var].get("Value", "")

            if isinstance(varVal, str):
                commandString += var+"="+varVal
            elif isinstance(varVal, int):
                commandString += var+"="+str(varVal)
            elif isinstance(varVal, list):
                # not going to implement this, just do the first entry and forget about the others
                commandString += var+"="+str(varVal[0])
            commandString += " "

        else:
            commandString += comm+" "
    return commandString

def getLFLAGSDict(jsonDict):
    """
    @brief  Gets all LFLAG information for a each bitcode name in a project
    @retval     LFLAGS          Dictionary mapping LFLAGS lists to a bitcode name
    """
    # list of commands defined in the Build field of the input JSON
    Commands = []
    # dictionary mapping bitcode to LFLAGS
    LFLAGS = dict()
    for field in jsonDict:
        if field == "Build":
            for key in jsonDict[field]:
                if key == "LFLAGS":
                    # LFLAGS can be a dictionary, list or string
                    if isinstance(jsonDict[field][key], dict):
                        # Look for a "default" or (deprecated) "general" field
                        trykey = jsonDict[field][key].get("default", None)
                        if trykey is not None:
                            LFLAGS["default"] = jsonDict[field][key]["default"]
                        else:
                            # look for deprecated "general" field
                            trykey = jsonDict[field][key].get("default", None)
                            if trykey is not None:
                                LFLAGS["default"] = jsonDict[field][key]["general"]

                        # grab all other entries in the LFLAGS dictionary
                        for name in jsonDict[field][key]:
                            if isinstance(jsonDict[field][key][name], str):
                                LFLAGS[name] = list(jsonDict[field][key][name])
                            else:
                                LFLAGS[name] = jsonDict[field][key][name]
                                
                    elif isinstance(jsonDict[field][key], list):
                        for name in jsonDict[field][key]:
                            LFLAGS["default"] = []
                            LFLAGS["default"].append(name)
                    elif isinstance(jsonDict[field][key], str):
                        LFLAGS["default"] = []
                        LFLAGS["default"].append( jsonDict[field][key] )

                elif key == "Variables":
                    continue
                elif key == "Commands":
                    continue
                else:
                    globLog.error("{} within ( Build: LFLAGS: ) is an invalid key. Please check your input JSON file's LFLAGS field.".format(key))

    return LFLAGS

def getRARGSDict(jsonDict):
    """
    @brief  Gets all information defined in the Run field of input JSON
    """
    # dictionary mapping bitcode to RARGS
    RARGS = dict()
    for field in jsonDict:
        if field == "Run":
            # Run dictionary needs to have at least 1 key, the Commands list
            if jsonDict[field].get("Commands", None) is not None:
                if isinstance(jsonDict[field]["Commands"], dict):
                    for key in jsonDict[field]["Commands"]:
                        if isinstance(jsonDict[field]["Commands"][key], dict):
                            for bitcode in jsonDict[field]["Commands"][key]:
                                RARGS[bitcode] = getRARGS(jsonDict[field]["Commands"][key][bitcode], jsonDict)
                                if RARGS[bitcode] == None:
                                    return None
                        elif isinstance(jsonDict[field]["Commands"][key], list):
                            RARGS[key] = getRARGS(jsonDict[field]["Commands"][key], jsonDict)
                            if RARGS[key] == None:
                                return None
                        elif isinstance(jsonDict[field]["Commands"][key], str):
                            RARGS[key] = getRARGS(jsonDict[field]["Commands"][key], jsonDict)
                            if RARGS[key] == None:
                                return None
                else:
                    globLog.critical("The \"Commands\" field in the input JSON file needs to be a dictionary, with a bitcode file name as key (no suffix) and run command as value.\n\tDash-Automate is now done. Please interrupt the process with Ctrl+C")
                    EXIT_TOOL()
            else:
                globLog.critical("Your input JSON Run field needs at least a \"Commands\" field.")
                return None
    return RARGS

def getRARGS(commandList, jsonDict):
    """
    @brief  Interprets args in a run command and inputs them into a complete bash string
            This function ignores all words that are not encoded in variables because we want to know what they are explicitly
            Moved to the Project class to maintain backward compatibility
    @param[in]  commandList     List of defined commands for a bitcode name or the default (or deprecated general) category
    @parampin]  jsonDict        Complete json dictionary for looking up variables
    @retval     Rcommands       List of strings that when appended to a binary name will create a bash-ready run command. 
                                Each entry corresponds to each index in commandList 
    """
    Rcommands = []
    if isinstance(commandList, list):
        for entry in commandList:
            runString = ""
            for word in entry.split(" "):
                if word.startswith("%"):
                    globLog.warning("Defining variables in the compile.json is deprecated. Please change the JSON to explicitly write out the run command.")
                    if jsonDict["Run"].get("Variables", None) is None:
                        globLog.critical("In input JSON file:\n\tVariables were used in Commands but no variables were defined.")
                        return None

                    # find our variable and replace it with its value
                    found = False
                    for key in jsonDict["Run"]["Variables"]:
                        if str(key) == str(word[1:]):
                            # variables don't have to have a Value key, so check first
                            if jsonDict["Run"]["Variables"][word[1:]].get("Value", None) is not None:
                                runString += str(jsonDict["Run"]["Variables"][word[1:]]["Value"])+" "
                                found = True
                                break
                    if not found:
                        globLog.critical("In input JSON file:\n\tThe variable {} was not defined.".format(word[1:]))
                        return None
                elif word.startswith("./"):
                    # this is a fake binary name, ignore it
                    continue
                # this is not a variable so add the raw word to the list
                else:
                    runString += " "+word
            Rcommands.append(runString)

    elif isinstance(commandList, str):
        runString = ""
        for word in commandList.split(" "):
            if word.startswith("%"):
                globLog.warning("Defining variables in the compile.json is deprecated. Please change the JSON to explicitly write out the run command.")
                if jsonDict["Run"].get("Variables", None) is None:
                    globLog.critical("In input JSON file:\n\tVariables were used in Commands but no variables were defined.")
                    return None

                # find our variable and replace it with its value
                found = False
                for key in jsonDict["Run"]["Variables"]:
                    if str(key) == str(word[1:]):
                        # variables don't have to have a Value key, so check first
                        if jsonDict["Run"]["Variables"][word[1:]].get("Value", None) is not None:
                            runString += str(jsonDict["Run"]["Variables"][word[1:]]["Value"])+" "
                            found = True
                            break
                if not found:
                    globLog.critical("In input JSON file:\n\tThe variable {} was not defined.".format(word[1:]))
                    return None
            elif word.startswith("./"):
                # this is a fake binary name, ignore it
                continue
            # this is not a variable so add the raw word to the list
            else:
                runString += word

        Rcommands.append(runString)

    return Rcommands

### Bitcode helpers
def waitOnFile(file, path, appear=True, directory=True, N=3, message=None, level=0):
    """
    @brief Creates a bash script command that will wait for a file or directory to be created
    @param[in] appear       Wait for a file to appear. If set to false, the logic will wait for the file to disappear
    @param[in] directory    Type of file to look at. If set to false, will look for a file.
    @param[in] N            Integer exponent to count up to. Base 2
    @param[in] message      Message to echo if the intial if condition evaluates to true
    @param[in] level        Basic logic level. If this condition will be wrapped in another condition, the level should be set to 1 for indents to line up
    """
    l0 = "\n"
    for i in range(level):
        l0 += "\t"
    l1 = l0+"\t"
    l2 = l1+"\t"
    l3 = l2+"\t"
    if directory:
        obj = "-d"
    else:
        obj = "-f"
    if appear:
        condition = " ! "
        failmessage = "\"Failed to generate target "+file+". Exiting.\""
    else:
        condition = " "
        failmessage = "\"Failed to remove target "+file+". Exiting.\""
    if message is not None:
        message = l1+"echo \""+message+"\""
    else:
        message = ""
    # create initial condition
    command = l0+"if ["+condition+obj+" \""+file+"\" ]; then"+message+l1
    # for loop for waiting
    command += "for i in 1:"+str(N)+l1+"do"+l2+"if ["+condition+obj+" \""+file+"\" ]; then"+l3+"break"+l2+"fi"+l2+"sleep 2**i"+l1+"done"+l1
    # exit command if the target did not turn up during wait period
    command += "if ["+condition+obj+" \""+file+"\" ]; then"+l2+"echo "+failmessage+l2+"rm -rf "+path+l2+"exit"+l1+"fi"+l0+"fi\n ; "

    return command

def getAuthor( JD ):
    """
    """
    if isinstance(JD, dict):
        if JD.get("User", None) is not None:
            if JD["User"].get("Author", None) is not None:
                authorList = JD["User"]["Author"]
                if isinstance(authorList, list):
                    return ",".join(x for x in authorList)
                elif isinstance(authorList, str):
                    return authorList
                else:
                    globLog.critical("Author definition must be a string or list of strings!")
                    return ""
            else:
                return ""
        else:
            return ""
    else:
        return ""

def getLibraries( JD ):
    """
    """
    if isinstance(JD, dict):
        if JD.get("User", None) is not None:
            if JD["User"].get("Libraries", None) is not None:
                if isinstance(JD["User"]["Libraries"], list):
                    return ",".join(str(x) for x in JD["User"]["Libraries"])
                elif isinstance(JD["User"]["Libraries"], str):
                    return JD["User"]["Libraries"]
                else:
                    globLog.critical("Library definition in User field of compile.json must be a string or list of strings!")
                    return ""
            else:
                return ""
        else:
            return ""
    else:
        return ""
        
### Reporting
def getTraceSize(filepath):
    try:
        size = os.path.getsize(filepath)
        return size
    except Exception as e:
        globLog.error(str(e))
        return -1

def getLogTime(filepath):
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse log "+filepath)
        return -1

    timeValues = []
    # if utf cant decode the text it will throw an exception
    try:
        for line in logfile:
            timeValues = re.findall("real\s\d+.\d+", line)
            if len(timeValues) > 0:
                list1 = re.findall("\d+\w", line)+re.findall("\d+.", line)
                totalseconds = 0
                days = []
                hours = []
                minutes = []
                seconds = []
                for entry in list1:  # should contain days, hours, minutes, whole seconds
                    if len(re.findall("\d+d", entry)) != 0:
                        if len(days) == 0:
                            days = re.findall("\d+d", entry)
                    if len(re.findall("\d+h", entry)) != 0:
                        if len(hours) == 0:
                            hours = re.findall("\d+h", entry)
                    if len(re.findall("\d+m", entry)) != 0:
                        if len(minutes) == 0:
                            minutes = re.findall("\d+m", entry)
                    if len(re.findall("\d+\.", entry)) != 0:
                        if len(seconds) == 0:
                            seconds = re.findall("\d+\.", entry)

                if len(days) != 0:
                    totalseconds += totalseconds+86400*int(days[0][:-1])
                if len(hours) != 0:
                    totalseconds += totalseconds+3600*int(hours[0][:-1])
                if len(minutes) != 0:
                    totalseconds += totalseconds+60*int(minutes[0][:-1])
                if len(seconds) != 0:
                    totalseconds += totalseconds+int(seconds[0][:-1])

                return totalseconds

    except Exception as e:
        globLog.error("Could not parse log file for time: "+filepath)
        return 0

    return 0

def getCartographerKernels(filepath):
    try:
        dic = json.load( open(filepath, "r") )
    except:
        return 0
    kernels = 0
    for key in dic:
        if key == "Kernels":
            for id in dic[key]:
                kernels+=1
    return kernels

def getTikKernels(filepath):
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse tik log "+filepath)
        return 0

    count = 0
    errors = 0
    try:
    	for line in logfile:
            errors += len(re.findall(".*DAStepERROR:\stik\scommand\sfailed.*", line))
            count += len(re.findall(".*Successfully\sconverted\skernel.*", line))
    except Exception as e:
        globLog.error("Could not parse line in tik log file "+filepath)
        return 0
    if errors > 0:
        return 0
    return count

def parseTikSwapResults(filepath):
    # tikswap results
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse tikSwap log "+filepath)
        return ((0,0), (0,0), (0,0))

    count = 0
    swapSuccess = 0
    compilationSuccess = 0
    binarySuccess = 0
    try:
    	for line in logfile:
            swapSuccess += len( re.findall(".*DAStepSuccess:\sTikSwap\scommand\ssucceeded.*", line))
            count += len(re.findall(".*Successfully\sswapped\sentrance\s0.*", line))
            compilationSuccess += len( re.findall(".*DAStepSuccess:\sTik\sCompilation\scommand\ssucceeded.*", line))
            binarySuccess += len( re.findall(".*DAStepSuccess:\sTik\sBinary\scommand\ssucceeded.*", line))
    except Exception as e:
        globLog.error("Could not parse line in tik log file: "+str(e))

    # swap results
    tikSwapKernels = count
    tikSwapBinaries = swapSuccess

    # tik compilation results
    tikCompilationBinaries = compilationSuccess
    tikCompilationKernels = tikSwapKernels if tikCompilationBinaries > 0 else 0

    # tik success results
    tikBinarySuccess = binarySuccess
    tikBinarySuccessKernels = tikCompilationKernels if tikBinarySuccess > 0 else 0

    return ( (tikSwapKernels, tikSwapBinaries), (tikCompilationKernels, tikCompilationBinaries), (tikBinarySuccessKernels, tikBinarySuccess) )

def getAvgKSize(kernelPath, Nodes=False, Blocks=False):
    """
    Returns the average kernel size, either in GraphNodes or basic blocks (from the original source bitcode), of the kernels in kernelPath
    """
    # read in kernel file
    # parse average kernel size number (in either nodes or blocks)
    # return the float
    avg = 0.0
    try:
        dic = json.load( open(kernelPath, "r") )
    except:
        return avg

    if Nodes:
        if dic.get("Average Kernel Size (Nodes)") is not None:
            return dic["Average Kernel Size (Nodes)"]
    else:
        if dic.get("Average Kernel Size (Blocks)") is not None:
            return dic["Average Kernel Size (Blocks)"]

def getCartographerErrors(filepath):
    reportDict = dict()
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse tik log "+filepath)
        return reportDict

    errorList = []
    try:
    	for line in logfile:
            reasons = re.findall(".*\[error\].*", line)
            reasons += re.findall(".*\[critical\].*", line)
            segFaults = re.findall("Segmentation.*", line)
            errorList += segFaults + reasons  # + errors
    except Exception as e:
        globLog.error("Could not parse line in tik log file "+filepath)
        return reportDict

    for entry in errorList:
        entry = entry.lower()
        segs = re.findall(".*segmentation.*", entry)
        if len(segs) == 0:
            lineNumber = re.findall("\.cpp\:\d+\:", entry)
            critical = re.findall(".*\[critical\].*", entry)
            if len(lineNumber) > 0:
                if reportDict.get(str(lineNumber[0]), None) is not None:
                    reportDict[str(lineNumber[0])] = reportDict[str(lineNumber[0])] + 1
                else:
                    reportDict[str(lineNumber[0])] = 1
            if len(critical) > 0:
                if reportDict.get("ModuleErrors", None) is not None:
                    reportDict["ModuleErrors"] = reportDict["ModuleErrors"] + 1
                else:
                    reportDict["ModuleErrors"] = 1

        else:
            if reportDict.get("Segmentation Faults", None) is not None:
                reportDict["Segmentation Faults"] = reportDict["Segmentation Faults"] + 1
            else:
                reportDict["Segmentation Faults"] = 1
    return reportDict

def getTikErrors(filepath):
    reportDict = dict()
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse tik log "+filepath)
        return reportDict

    errorList = []
    try:
    	for line in logfile:
            reasons = re.findall(".*\[error\].*", line)
            reasons += re.findall(".*\[critical\].*", line)
            segFaults = re.findall("Segmentation.*", line)
            errorList += segFaults + reasons  # + errors
    except Exception as e:
        globLog.error("Could not parse line in tik log file "+filepath)
        return reportDict

    for entry in errorList:
        entry = entry.lower()
        segs = re.findall(".*segmentation.*", entry)
        if len(segs) == 0:
            lineNumber = re.findall("\.cpp\:\d+\:", entry)
            critical = re.findall(".*\[critical\].*", entry)
            if len(lineNumber) > 0:
                if reportDict.get(str(lineNumber[0]), None) is not None:
                    reportDict[str(lineNumber[0])] = reportDict[str(lineNumber[0])] + 1
                else:
                    reportDict[str(lineNumber[0])] = 1
            if len(critical) > 0:
                if reportDict.get("ModuleErrors", None) is not None:
                    reportDict["ModuleErrors"] = reportDict["ModuleErrors"] + 1
                else:
                    reportDict["ModuleErrors"] = 1

        else:
            # check if its a pig segfault or tik segfault
            pig = re.findall(".*\/sources\/bin\/pig.*", entry)
            if len(pig) == 0:
                if reportDict.get("Segmentation Faults", None) is not None:
                    reportDict["Segmentation Faults"] = reportDict["Segmentation Faults"] + 1
                else:
                    reportDict["Segmentation Faults"] = 1
    return reportDict

def getTikSwapErrors(filepath):
    reportDict = dict()
    try:
        logfile = open(filepath, "r")
    except:
        globLog.error("Could not parse tikSwap log "+filepath)
        return reportDict

    errorList = []
    try:
    	for line in logfile:
            reasons = re.findall(".*\[error\].*", line)
            reasons += re.findall(".*\[critical\].*", line)
            segFaults = re.findall("Segmentation.*", line)
            errorList += segFaults + reasons  # + errors
    except Exception as e:
        globLog.error("Could not parse line in tikSwap log file "+filepath)
        return reportDict

    for entry in errorList:
        entry = entry.lower()
        segs = re.findall(".*segmentation.*", entry)
        if len(segs) == 0:
            lineNumber = re.findall("\.cpp\:\d+\:", entry)
            critical = re.findall(".*\[critical\].*", entry)
            if len(lineNumber) > 0:
                if reportDict.get(str(lineNumber[0]), None) is not None:
                    reportDict[str(lineNumber[0])] = reportDict[str(lineNumber[0])] + 1
                else:
                    reportDict[str(lineNumber[0])] = 1
            if len(critical) > 0:
                if reportDict.get("ModuleErrors", None) is not None:
                    reportDict["ModuleErrors"] = reportDict["ModuleErrors"] + 1
                else:
                    reportDict["ModuleErrors"] = 1

    return reportDict

### Command helpers
def RunJob(command, SLURM=True):
    """
    @brief  Class helper function to bash a command and get its ID back
    """
    if SLURM:
        failure = False
        while True:
            proc = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
            # the file object attached to this process is not guaranteed
            try:
                standardout = proc.communicate()
            except Exception as e:
                globLog.error("Lost the file object when trying to communicate: "+str(e))
                failure = True
                time.sleep(1)
                continue
            for entry in flatten(standardout):
                ID = re.findall("(\d+)", entry.decode("utf-8"))
                if len(ID) > 0:
                    return ID[0]
            time.sleep(0.05)
    else: # bash
        time.sleep(1)
        return proc.pid

### SQL
def getDBParameters(path):
    """
    @brief Reads the DB connection parameters
    """
    with open(path, "r") as f:
        params = list()
        for line in f:
            answer = line.strip("\n").split("=")
            params.append( answer[1] )
    return params

def getGitRepoIDs(path):
    """
    @brief Retrieves the most recent hash of the git repository for Dash-Corpus and its submodules at tool runtime
    @param[in] path     Absolute path to the directory of the tool call
    @retval             List of IDs in string form [Corpus, RadioCorpus, SDH, Kestrel_Spectrum_Sensing, Kestrel_Comms]
    """
    IDs = ["-1","-1","-1","-1","-1"]
    paths = []
    paths.append( path ) # corpus path
    paths.append( path+"Dash-RadioCorpus/" ) # radiocorpus path
    paths.append( path+"SDH_Workloads/" ) # SDH path
    paths.append( path+"Kestrel_Spectrum_Sensing/" ) # Kestrel_Spectrum_Sensing path
    paths.append( path+"Kestrel_Comms/" ) # Kestrel_Comms path
    for i in range( len(paths) ):
        proc = sp.Popen("cd "+paths[i]+" ; git rev-parse HEAD", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        output = ""
        while proc.poll() is None:
            output += proc.stdout.read().decode("utf-8")
        fatal = re.findall(".*fatal.*", output)
        if len(fatal) == 0:
            IDs[i] = output.strip("\n")
    return IDs

def getKernelLibraries(FD, index):
    """
    @param[in] FD    Dictionary of function annotation data per trace
    @param[in] index Kernel index to be retrieved. Needs to be in string form
    """
    if isinstance(FD, dict):
        if FD.get(index, None) is not None:
            return ",".join(x for x in FD[index])
        else:
            return ""
    else:
        return ""

def getKernelHash(KHD, index):
    """
    @param[in] KHD    Dictionary of kernel and basic block hash data per trace
    @param[in] index  Kernel index to be retrieved. Needs to be in string form
    @retval           Kernel hash as a 64 bit integer
    """
    if isinstance(KHD, dict):
        if KHD.get(index, None) is not None:
            if KHD[index].get("Kernel", None) is not None:
                return ctypes.c_long(KHD[index]["Kernel"]).value
            else:
                return -1
        else:
            return -1
    else:
        return -1

def getBBHList(KHD, index):
    """
    @brief Retrieves the list of basic block hashes for the given kernel index from the given dictionary
    @param[in] KHD   Dictionary of kernel and basic block hash info per trace
    @param[in] index Kernel index to be retrieved. Must be a string
    @retval          CSV string of each BB hash
    """
    if isinstance(KHD, dict):
        if KHD.get(index, None) is not None:
            if KHD[index].get("Blocks", None) is not None:
                hashList = []
                for entry in KHD[index]["Blocks"]:
                    hashList.append( ctypes.c_long(entry).value )
                return hashList
            else:
                return None
        else:
            return None
    else:
        return None

def getKernelLabels(KD, index):
    """
    @param[in] KD    Dictionary of kernel data per trace
    @param[in] index Kernel index to be retrieved. Needs to be in string form
    """
    if isinstance(KD, dict):
        if KD.get("Kernels", None) is not None:
            if KD["Kernels"].get(index, None) is not None:
                if KD["Kernels"][index].get("Label", None) is not None:
                    label = KD["Kernels"][index]["Label"]
                    if len(label) > 256:
                        # truncate, database only allows 256 characters or less
                        label = label[0:255]
                    return label
                else:
                    return ""
            else:
                return ""
        else:
            return ""
    else:
        return ""

### Errors
def findErrors(logpath):
    """
    @brief  Finds a key phrase in log files when a step fails. 
    @retval Returns True if an error is found or if the given logfile path is not present, False otherwise
    """
    try:
        f = open(logpath, "r")
    except:
        globLog.error("Could not find log file "+logpath)
        return True

    try:
        for line in f:
            errors = re.findall(".*DAStepERROR\:.*", line)
            if len(errors) > 0:
                return True
    except UnicodeDecodeError:
        globLog.error("Could not decode file {}. Skipping error processing.".format(logpath))

    return False

def EXIT_TOOL():
    """
    @brief Cleans up before the tool exits.
    """
    # close both threads somehow...
    # nothing special for now
    exit()
