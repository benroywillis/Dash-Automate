from BitCode import BitCode as Bc
from Project import Project as pj
import Util
import SQL
import os
import threading
import time
import logging
import json
import sys
import subprocess as sp
import statistics as st
import re

class tupleHash(tuple):
    def __new__(self, str1, str2):
        return tuple.__new__(tupleHash, (str1, str2))

    def __key(self):
        return (self[0])

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, tupleHash):
            return self.__key() == other.__key()
        return NotImplemented        

# name of output data file
TimeMapFile = "TimeMap.json"

# maximum number of bitcode buildflows that are allowed to run at once
MAX_PROCESSES=20

# Environment of each bash script
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

def parseLogFileInfo(log, args):
    # 14 metrics
    natives = []
    profiles = []
    printTimes = []
    kernels = []
    transforms = []
    segs = []
    nodeCount = []
    endNodeCount = []
    edgeCount = []
    endEdgeCount = []
    startEntropies = []
    endEntropies = []
    startTotalEntropies = []
    endTotalEntropies = []

    i = 0
    while i in range(3):
        try:
            f =  open(log,"r")
            break
        except:
            time.sleep(2**i)
            i += 1
            if i > 3:
                print("Could not open file "+str(log)+" for reading")
                return [], [], [], [], [], [], [], [], [], [], [], [], [], []
    try:
        for line in f:
            newNative = re.findall("NATIVE_TIME:\s\d+\.\d+",line)
            newProfile = re.findall("PROFILETIME:\s\d+\.\d+",line)
            newFilePrint = re.findall("HASHTABLEPRINTTIME:\s\d+\.\d+",line)
            newKernel = re.findall("CARTOGRAPHERKERNELS:\s\d+",line)
            newTransform = re.findall("CARTOGRAPHERTRANSFORMTIME:\s\d+\.\d+",line)
            newSeg = re.findall("CARTOGRAPHERSEGMENTATIONTIME:\s\d+\.\d+",line)
            newNode = re.findall("HASHTABLENODES:\s\d+",line)
            newEndNode = re.findall("TRANSFORMEDNODES:\s\d+",line)
            newEdge = re.findall("HASHTABLEEDGES:\s\d+",line)
            newEndEdge = re.findall("TRANSFORMEDEDGES:\s\d+",line)
            newStartEntropy = re.findall("STARTENTROPY:\s\d+.\d+",line)
            newEndEntropy = re.findall("ENDENTROPY:\s\d+.\d+",line)
            newStartTotalEntropy = re.findall("STARTTOTALENTROPY:\s\d+.\d+",line)
            newEndTotalEntropy = re.findall("ENDTOTALENTROPY:\s\d+.\d+",line)
            if len(newNative) == 1:
                numberString = newNative[0].replace("NATIVE_TIME: ","")
                runTime = float(numberString)
                natives.append( runTime )
            elif len(newProfile) == 1:
                numberString = newProfile[0].replace("PROFILETIME: ","")
                runTime = float(numberString)
                profiles.append( runTime )
            elif len(newFilePrint) == 1:
                numberString = newFilePrint[0].replace("HASHTABLEPRINTTIME: ","")
                runTime = float(numberString)
                printTimes.append( runTime )
            elif len(newKernel) == 1:
                numberString = newKernel[0].replace("CARTOGRAPHERKERNELS: ","")
                count = int(numberString)
                kernels.append( count )
            elif len(newTransform) == 1:
                numberString = newTransform[0].replace("CARTOGRAPHERTRANSFORMTIME: ","")
                runTime = float(numberString)
                transforms.append( runTime )
            elif len(newSeg) == 1:
                numberString = newSeg[0].replace("CARTOGRAPHERSEGMENTATIONTIME: ","")
                runTime = float(numberString)
                segs.append( runTime )
            elif len(newNode) == 1:
                numberString = newNode[0].replace("HASHTABLENODES: ","")
                number = int(numberString)
                nodeCount.append( number )
            elif len(newEndNode) == 1:
                numberString = newEndNode[0].replace("TRANSFORMEDNODES: ","")
                number = int(numberString)
                endNodeCount.append( number )
            elif len(newEdge) == 1:
                numberString = newEdge[0].replace("HASHTABLEEDGES: ","")
                number = int(numberString)
                edgeCount.append(number)
            elif len(newEndEdge) == 1:
                numberString = newEndEdge[0].replace("TRANSFORMEDEDGES: ","")
                number = int(numberString)
                endEdgeCount.append( number )            
            elif len(newStartEntropy) == 1:
                numberString = newStartEntropy[0].replace("STARTENTROPY: ","")
                number = float(numberString)
                startEntropies.append( number )
            elif len(newEndEntropy) == 1:
                numberString = newEndEntropy[0].replace("ENDENTROPY: ","")
                number = float(numberString)
                endEntropies.append( number )
            elif len(newStartTotalEntropy) == 1:
                numberString = newStartTotalEntropy[0].replace("STARTTOTALENTROPY: ","")
                number = float(numberString)
                startTotalEntropies.append( number )
            elif len(newEndTotalEntropy) == 1:
                numberString = newEndTotalEntropy[0].replace("ENDTOTALENTROPY: ","")
                number = float(numberString)
                endTotalEntropies.append( number )
        totalTimes = len(natives) + len(profiles) + len(printTimes) + len(segs)
        if totalTimes != args.samples * 4:
            print("Did not find the correct number of samples for all four categories! Sample lengths were: natives "+str(len(natives))+", profiles: "+str(len(profiles))+", filePrints: "+str(len(printTimes))+", segmentations: "+str(len(segs)))
            return [], [], [], [], [], [], [], [], [], [], [], [], [], []
        return natives, profiles, printTimes, kernels, transforms, segs, nodeCount, endNodeCount, edgeCount, endEdgeCount, startEntropies, endEntropies, startTotalEntropies, endTotalEntropies
    except Exception as e:
        print("Exception while reading through logFile "+log+": "+str(e))
        return [], [], [], [], [], [], [], [], [], [], [], [], [], []

def buildBashCommand(command, buildFilePath, logFile, scriptFile):
    # if not set, set environment to init parameter
    logFile = buildFilePath+"logs/"+logFile

    bashString = "#!/bin/bash\n"
    bashString += "export "+SourceScript+"\n"
    bashString += "touch "+logFile + "\n"
    bashString += command.replace(" ; ","\n")+"\n"

    bashFile = buildFilePath+"scripts/"+scriptFile
    with open(bashFile, "w") as f:
        f.write(bashString)
    #return "cd "+buildFilePath+"/scripts/ ; chmod +x "+bashFile+" ; "+bashFile+ " | tee -ia " + logFile
    return "cd "+buildFilePath+"/scripts/ ; chmod +x "+bashFile+" ; "+bashFile

def runBashCommand( scriptCommand ):
    return sp.Popen(scriptCommand, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)    

class DashAutomate:
    """
    """
    def __init__(self, rtargs):
        """
        @brief Facilitates builds on the Dash-Ontology database
        @param[in]  rtargs  Runtime arguments to the tool
        """
        # path where the tool was called
        self.rootPath = rtargs.project_prefix
        # set of projects included in the build tree
        self.projects = set()
        # set of projects that are currently active
        self.buildingProjects = set()
        # set of bitcodes created from projects
        self.bitcodes = set()
        # set of bitcodes that are currently active
        self.buildingBitcodes = set()
        # runtime args
        self.args = rtargs
        # logging object
        self.log = logging.getLogger("DashAutomate")
        # DB connection object for run-related SQL pushes
        self.DASQL = SQL.DashAutomateSQL(self.rootPath, self.args.previous_id)
        # tree holds all existing traces in the specified previous runID
        self.existingMap = None
        # set to hold project paths that have already had a project built
        self.builtProjects = set()
        # thread one generates the project directory tree, builds each valid project, and starts each respective project's bitcode once the project is done
        self.thread1 = threading.Thread(target=self.run)
        # report file path
        self.reportFile = os.getcwd()+"/FULLREPORT_"+str(self.DASQL.ID)+"_"+self.args.build+".json"
        # full report dictionary
        self.FULLREPORT = dict()
        self.FULLREPORT["Full Report"] = dict()
        self.FULLREPORT["Full Report"]["Traces"] = 0
        self.FULLREPORT["Full Report"]["Tik Traces"] = 0
        self.FULLREPORT["Full Report"]["Tik Swaps"] = 0
        self.FULLREPORT["Full Report"]["Tik Compilations"] = 0
        self.FULLREPORT["Full Report"]["Tik Successes"] = 0
        self.FULLREPORT["Full Report"]["Cartographer Kernels"] = 0
        self.FULLREPORT["Full Report"]["Tik Kernels"] = 0
        self.FULLREPORT["Full Report"]["TikSwap Kernels"] = 0
        self.FULLREPORT["Full Report"]["Tik Compilation Kernels"] = 0
        self.FULLREPORT["Full Report"]["Tik Success Kernels"] = 0
        self.FULLREPORT["Full Report"]["Average Kernel Size (Nodes)"] = 0
        self.FULLREPORT["Full Report"]["Average Kernel Size (Blocks)"] = 0
        self.FULLREPORT["Full Report"]["Cartographer Errors"] = dict()
        self.FULLREPORT["Full Report"]["Tik Errors"] = dict()
        self.FULLREPORT["Full Report"]["TikSwap Errors"] = dict()
        self.FULLREPORT["Full Report"]["Bad Projects"] = list()
        self.FULLREPORT["Full Report"]["Bitcodes with Errors"] = dict()

    def getProjects(self):
        """
        @brief Acquires all project directories from subdirectory tree
        """
        compileD = Util.readJson(self.args.project_prefix, self.args)
        subdirectories = Util.parseValidSubDs(compileD, self.args)
        # set of relative paths from the current directory to all subdirectories
        projectPaths = set()
        if not self.args.no_subdirectories:
            for path in subdirectories:
                projectPaths = Util.recurseThroughSubDs(path, self.args, projectPaths)
        # local directory
        if compileD.get("Build", None) is not None:
            projectPaths.add(self.args.project_prefix)

        for path in projectPaths:
            refinedPath = "/"+"/".join(y for y in [x for x in path.split("/") if x != ""])
            self.projects.add( pj( self.rootPath, refinedPath, self.args.build, self.args.input_file) )

    def run(self):
        """
        @brief  Walks the directory tree, finds all projects with input JSON name and builds the makefiles.
        @param[in]  args        Runtime args to the DA tool
        @retval     projects    List of Project objects currently building. Can be either process IDs in bash or SLURM IDs. Note: The bash process IDs are the IDs of the shells launched by subprocess, not the actual job itself.
        """
        processes = 0
        self.getProjects()

        # for each project, run its build command
        waitingProjects = set()
        for proj in self.projects:
            if proj.Valid:
                waitingProjects.add( tupleHash(proj, buildBashCommand( proj.run(returnCommand=True), proj.buildPath, proj.logFile, proj.scriptName )) )
        for proj in waitingProjects:
            self.buildingProjects.add( tupleHash( proj[0], runBashCommand( proj[1] ) ) )                    
            time.sleep(0.01)

        doneProjects = set()
        waitingBitcodes = set()
        while len(self.buildingProjects):
            for tup in self.buildingProjects:
                proj = tup[0]
                job  = tup[1]
                if job.poll() is not None:
                    with open(proj.buildPath+"logs/"+proj.logFile, "w") as f:
                        f.write(job.stdout.read().decode("utf-8"))
                    proj.done()
                    doneProjects.add(tup)
                    for BC in proj.Bitcodes:
                        newBC = Bc(self.args.project_prefix, proj.projectPath, BC, proj.Bitcodes[BC]["LFLAGS"], proj.Bitcodes[BC]["RARGS"], self.DASQL.ID, -1, self.args)
                        if not newBC.errors:
                            for BCPath in newBC.BCDict:
                                for NTV in newBC.BCDict[BCPath]:
                                    if NTV[-6:] == "native":
                                        for PROkey in newBC.BCDict[BCPath][NTV]:
                                            if PROkey.startswith("TRC"):
                                                waitingBitcodes.add( tupleHash( newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Log"], buildBashCommand( newBC.getCommand(BCPath, NTV, PROkey), newBC.buildPath, newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Log"].split("/")[-1], newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Script"].split("/")[-1] ) ) )
                        else:
                            self.log.error("Found errors in bitcode "+newBC.projectPath)
                    self.log.info("Project "+proj.projectPath+" is done.")
            oldSize = len(self.buildingProjects)
            self.buildingProjects -= doneProjects
            if len(self.buildingProjects) < oldSize:
                self.log.info("There are "+str(len(self.buildingProjects))+" remaining.")
            time.sleep(0.1)
        self.log.info("Projects complete.")

        for bit in waitingBitcodes:
            if processes < MAX_PROCESSES:
                print("Launching bitcode "+bit[0])
                self.buildingBitcodes.add( tupleHash(bit[0], runBashCommand( bit[1] ) ) )
                processes += 1
                time.sleep(0.01)
            else:
                while processes > MAX_PROCESSES:
                    for bit2 in self.buildingBitcodes:
                        if bit2[1].poll() is not None:
                            processes -= 1
                            print(str(processes)+" active jobs")
                            time.sleep(0.1)
                print("Launching bitcode "+bit[0])
                self.buildingBitcodes.add( tupleHash(bit[0], runBashCommand( bit[1] ) ) )
                processes += 1

        TimeMap = {}
        doneBitcodes = set()
        oldMapSize = len(TimeMap)
        while len(self.buildingBitcodes):
            for bit in self.buildingBitcodes:
                if bit[1].poll() is not None:
                    with open(bit[0], "w") as f:
                        f.write(bit[1].stdout.read().decode("utf-8"))
                    doneBitcodes.add(bit)
                    processes -= 1
                    # update TimeMap file                        
                    natives, profiles, filePrints, kernels, transforms, segs, nodes, endNodes, edges, endEdges, startEntropy, endEntropy, startTotalEntropy, endTotalEntropy = parseLogFileInfo(bit[0], self.args)
                    totals = [profiles[i]+filePrints[i]+segs[i] for i in range(len(natives))]
                    bitLogFile = Util.getPathDiff(self.rootPath, "/".join(bit[0].split("/")[-1:]), build=False)
                    self.log.info("Updating TimeMap with bitcode "+bit[0])
                    try:
                        TimeMap[bitLogFile] = { "Natives":       { "Times": natives, "Nodes": st.median(nodes), "Kernels": st.median(kernels), "EndNodes": st.median(endNodes), "Edges": st.median(edges), "endEdges": st.median(endEdges), "StartEntropy": st.median(startEntropy), "EndEntropy": st.median(endEntropy), "StartTotalEntropy": st.median(startTotalEntropy), "EndTotalEntropy": st.median(endTotalEntropy), "Mean": st.mean(natives), "Median": st.median(natives), "stdev": st.pstdev(natives) },\
                                                "Profiles":      { "Times": profiles, "Dilations": [profiles[i]/natives[i] for i in range(len(natives))],   "Mean": -1, "Median": -1, "stdev": -1 },\
                                                "FilePrints":    { "Times": filePrints, "Dilations": [filePrints[i]/natives[i] for i in range(len(natives))], "Mean": -1, "Median": -1, "stdev": -1 },\
                                                "Transforms":    { "Times": transforms, "Dilations": [transforms[i]/natives[i] for i in range(len(natives))], "Mean": -1, "Median": -1, "stdev": -1 },\
                                                "Segmentations": { "Times": segs, "Dilations": [segs[i]/natives[i] for i in range(len(natives))],       "Mean": -1, "Median": -1, "stdev": -1 },\
                                                "Total":         { "Dilations": [totals[i]/natives[i] for i in range(len(natives))],     "Mean": -1, "Median": -1, "stdev": -1 } }
                        TimeMap[bitLogFile]["Profiles"]["Mean"]   = st.mean(   TimeMap[bitLogFile]["Profiles"]["Dilations"] )
                        TimeMap[bitLogFile]["Profiles"]["Median"] = st.median( TimeMap[bitLogFile]["Profiles"]["Dilations"] )
                        TimeMap[bitLogFile]["Profiles"]["stdev"]  = st.pstdev( TimeMap[bitLogFile]["Profiles"]["Dilations"] )
                        TimeMap[bitLogFile]["FilePrints"]["Mean"]   = st.mean(   TimeMap[bitLogFile]["FilePrints"]["Dilations"] )
                        TimeMap[bitLogFile]["FilePrints"]["Median"] = st.median( TimeMap[bitLogFile]["FilePrints"]["Dilations"] )
                        TimeMap[bitLogFile]["FilePrints"]["stdev"]  = st.pstdev( TimeMap[bitLogFile]["FilePrints"]["Dilations"] )
                        TimeMap[bitLogFile]["Transforms"]["Mean"]   = st.mean(   TimeMap[bitLogFile]["Transforms"]["Dilations"] )
                        TimeMap[bitLogFile]["Transforms"]["Median"] = st.median( TimeMap[bitLogFile]["Transforms"]["Dilations"] )
                        TimeMap[bitLogFile]["Transforms"]["stdev"]  = st.pstdev( TimeMap[bitLogFile]["Transforms"]["Dilations"] )                        
                        TimeMap[bitLogFile]["Segmentations"]["Mean"]   = st.mean(   TimeMap[bitLogFile]["Segmentations"]["Dilations"] )
                        TimeMap[bitLogFile]["Segmentations"]["Median"] = st.median( TimeMap[bitLogFile]["Segmentations"]["Dilations"] )
                        TimeMap[bitLogFile]["Segmentations"]["stdev"]  = st.pstdev( TimeMap[bitLogFile]["Segmentations"]["Dilations"] )
                        TimeMap[bitLogFile]["Total"]["Mean"]   = st.mean(   TimeMap[bitLogFile]["Total"]["Dilations"] )
                        TimeMap[bitLogFile]["Total"]["Median"] = st.median( TimeMap[bitLogFile]["Total"]["Dilations"] )
                        TimeMap[bitLogFile]["Total"]["stdev"]  = st.pstdev( TimeMap[bitLogFile]["Total"]["Dilations"] )
                    except Exception as e:
                        self.log.error("Failed to calculate statistics for "+bit[0]+": "+str(e))
                    self.log.info("Bitcode job "+str(bit[1].pid)+" is done.")
            oldSize = len(self.buildingBitcodes)
            self.buildingBitcodes -= doneBitcodes
            if len(self.buildingBitcodes) < oldSize:
                self.log.info("There are "+str(len(self.buildingBitcodes))+" remaining.")
            if len(TimeMap) > oldMapSize:
                self.log.info("Writing TimeMap to file...")
                oldMapSize = len(TimeMap)
                with open(TimeMapFile, "w+") as f:
                    json.dump(TimeMap, f, indent=4)

            time.sleep(0.1)
        self.log.info("Bitcodes done.")

        # search through all bitcode logs and find their times
        """TimeMap = {}
        for bit in bitLogFiles:
            natives, profiles, filePrints, segs, nodes, edges = parseLogFileInfo(bit)
            totals = [profiles[i]+filePrints[i]+segs[i] for i in range(len(natives))]
            TimeMap[bit] = { "Natives":       { "Mean": st.mean(natives), "Median": st.median(natives), "stdev": st.pstdev(natives) },\
                                  "Profiles":      { "Dilations": [profiles[i]/natives[i] for i in range(len(natives))],   "Mean": -1, "Median": -1, "stdev": -1 },\
                                  "FilePrints":    { "Dilations": [filePrints[i]/natives[i] for i in range(len(natives))], "Mean": -1, "Median": -1, "stdev": -1 },\
                                  "Segmentations": { "Dilations": [segs[i]/natives[i] for i in range(len(natives))],       "Mean": -1, "Median": -1, "stdev": -1 },\
                                  "Total":         { "Dilations": [totals[i]/natives[i] for i in range(len(natives))],     "Mean": -1, "Median": -1, "stdev": -1 } }
            TimeMap[bit]["Profiles"]["Mean"]   = st.mean(   TimeMap[bit]["Profiles"]["Dilations"] )
            TimeMap[bit]["Profiles"]["Median"] = st.median( TimeMap[bit]["Profiles"]["Dilations"] )
            TimeMap[bit]["Profiles"]["stdev"]  = st.pstdev( TimeMap[bit]["Profiles"]["Dilations"] )
            TimeMap[bit]["FilePrints"]["Mean"]   = st.mean(   TimeMap[bit]["FilePrints"]["Dilations"] )
            TimeMap[bit]["FilePrints"]["Median"] = st.median( TimeMap[bit]["FilePrints"]["Dilations"] )
            TimeMap[bit]["FilePrints"]["stdev"]  = st.pstdev( TimeMap[bit]["FilePrints"]["Dilations"] )
            TimeMap[bit]["Segmentations"]["Mean"]   = st.mean(   TimeMap[bit]["Segmentations"]["Dilations"] )
            TimeMap[bit]["Segmentations"]["Median"] = st.median( TimeMap[bit]["Segmentations"]["Dilations"] )
            TimeMap[bit]["Segmentations"]["stdev"]  = st.pstdev( TimeMap[bit]["Segmentations"]["Dilations"] )
            TimeMap[bit]["Total"]["Mean"]   = st.mean(   TimeMap[bit]["Segmentations"]["Dilations"] )
            TimeMap[bit]["Total"]["Median"] = st.median( TimeMap[bit]["Segmentations"]["Dilations"] )
            TimeMap[bit]["Total"]["stdev"]  = st.pstdev( TimeMap[bit]["Segmentations"]["Dilations"] )
        print(TimeMap)
        """

def main():
    if sys.version_info[0] != 3:
        exit("DashAutomate requires python3!")

    args = Util.argumentParse()

    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',filename=args.log_file, filemode='w', level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(args.log_level)
    console.setFormatter(logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s"))
    logging.getLogger().addHandler(console)

    DA = DashAutomate( args )
    DA.run()
main()
