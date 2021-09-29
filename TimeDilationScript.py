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
import time
import statistics as st
import re

# maximum number of bitcode buildflows that are allowed to run at once
MAX_PROCESSES=15
# number of samples for each category we should get
# Used to sample the space so we get an accurate read on the timing of each step and program
# This number should match SAMPLE_NUMBER in Bitcode.py
SAMPLE_ITERATIONS = 15
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

def getExecutionTimes(log):
    natives = []
    profiles = []
    printTimes = []
    segs = []
    with open(log,"r") as f:
        try:
            for line in f:
                newNative = re.findall("NATIVE_TIME:\s\d+\.\d+",line)
                newProfile = re.findall("PROFILETIME:\s\d+\.\d+",line)
                newFilePrint = re.findall("HASHTABLEPRINTTIME:\s\d+\.\d+",line)
                newSeg = re.findall("Cartographer\sEvaluation\sTime:\s\d+\.\d+",line)
                if (len(newNative) == 1):
                    numberString = newNative[0].replace("NATIVE_TIME: ","")
                    time = float(numberString)
                    natives.append( time )
                elif len(newProfile) == 1:
                    numberString = newProfile[0].replace("PROFILETIME: ","")
                    time = float(numberString)
                    profiles.append( time )
                elif len(newFilePrint) == 1:
                    numberString = newFilePrint[0].replace("HASHTABLEPRINTTIME: ","")
                    time = float(numberString)
                    printTimes.append( time )
                elif len(newSeg) == 1:
                    numberString = newSeg[0].replace("Cartographer Evaluation Time: ","")
                    time = float(numberString)
                    segs.append( time )
            totalTimes = len(natives) + len(profiles) + len(printTimes) + len(segs)
            if totalTimes != SAMPLE_ITERATIONS * 4:
                print("Did not find the correct number of samples for all four categories! Sample lengths were: natives "+str(len(natives))+", profiles: "+str(len(profiles))+", filePrints: "+str(len(printTimes))+", segmentations: "+str(len(segs)))
                return [], [], [], []
            return natives, profiles, printTimes, segs
        except Exception as e:
            print("Exception while reading through logFile "+log+": "+str(e))
            return [], [], [], []

def buildBashCommand(command, buildFilePath, logFile, scriptFile):
    # if not set, set environment to init parameter
    logFile = buildFilePath+"logs/"+logFile

    bashString = "#!/bin/bash\n"
    bashString += "export "+SourceScript+"\n"

    bashString += command+"\n"

    bashFile = buildFilePath+"scripts/"+scriptFile
    with open(bashFile, "w") as f:
        f.write(bashString)
    return "cd "+buildFilePath+"/scripts/ ; chmod +x "+bashFile+" ; "+bashFile+ " 2> " + logFile + " 1> " + logFile

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
                waitingProjects.add( (proj, buildBashCommand( proj.run(returnCommand=True), proj.buildPath, proj.logFile, proj.scriptName )) )
        for proj in waitingProjects:
            self.buildingProjects.add( ( proj[0], runBashCommand( proj[1] ) ) )                    
            time.sleep(0.01)

        doneProjects = set()
        waitingBitcodes = set()
        bitLogFiles = set()
        while len(self.buildingProjects):
            for tup in self.buildingProjects:
                proj = tup[0]
                job  = tup[1]
                if job.poll() is not None:
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
                                                bitLogFiles.add(newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Log"])
                                                waitingBitcodes.add( buildBashCommand( newBC.getCommand(BCPath, NTV, PROkey), newBC.buildPath, newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Log"].split("/")[-1], newBC.BCDict[BCPath][NTV][PROkey]["CAR"]["Script"].split("/")[-1] ) )
                    self.log.info("Project "+proj.projectPath+" is done.")
            self.buildingProjects -= doneProjects
            time.sleep(0.1)
        self.log.info("Projects complete.")

        doneBitcodes = set()
        for bit in waitingBitcodes:
            if processes < MAX_PROCESSES:
                self.buildingBitcodes.add( runBashCommand( bit ) )
                processes += 1
                time.sleep(0.01)
            else:
                while len(self.buildingBitcodes) > MAX_PROCESSES/2:
                    for bit in self.buildingBitcodes:
                        if bit.poll() is not None:
                            doneBitcodes.add(bit)
                    processes = len(self.buildingBitcodes) - len(doneBitcodes)
                    self.buildingBitcodes -= doneBitcodes
        while len(self.buildingBitcodes):
            for bit in self.buildingBitcodes:
                if bit.poll() is not None:
                    doneBitcodes.add(bit)
            processes = len(self.buildingBitcodes) - len(doneBitcodes)
            self.buildingBitcodes -= doneBitcodes
        self.log.info("Bitcodes done.")

        # search through all bitcode logs and find their times
        TimeMap = {}
        for bit in bitLogFiles:
            natives, profiles, fileprints, segs = getExecutionTimes(bit)
            totals = [profiles[i]+filePrints[i]+segs[i] for i in range(len(natives))]
            TimeMap[bit] = { "Natives":       { "Mean": st.mean(natives), "Median": st.median(natives), "stdev": st.pstdev(natives) },\
                                  "Profiles":      { "Dilations": [profiles[i]/natives[i] for i in range(len(natives))],   "Mean": -1, "Median": -1, "stdev": -1 },\
                                  "FilePrints":    { "Dilations": [fileprints[i]/natives[i] for i in range(len(natives))], "Mean": -1, "Median": -1, "stdev": -1 },\
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
            
        print(TimeMap)

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
