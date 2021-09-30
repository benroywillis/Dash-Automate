import Util
from Command import Command as cm
import SQL
import json
import os

# number of times a native/profile is run to sample its runtime thoroughly
SAMPLE_NUMBER = 15

class BitCode:
    def __init__(self, rootPath, path, BC, LFLAGS, RARGS, run, parentID, rtargs):
        """
        @param[in]  rootPath    Absolute path leading to the project in which the Dash-Automate tool was originally called
        @param[in]  path        Absolute path of the directory in which this bitcode file was generated.
                                If the build folder is made, this variable is changed to the absolute path to the project build folder.
        @param[in]  BC          Name of the bitcode file with suffix to construct this object for
        @param[in]  LFLAGS      List of strings where each string represents compile-time dynamic linking flags 
        @param[in]  RARGS       List of strings where each string represents runtime arguments 
        @param[in]  run         Run ID of the Dash-Automate run.
        @param[in]  parentID    Root entry ID that the preceding Project object pushed.
        @param[in]  rtarg       Dictionary of the arguments passed to the program at runtime.
        """
        self.args           = rtargs
        self.rootPath       = rootPath
        self.projectPath    = path
        # path to relative build folder
        rawpath = path.split("/")
        while "" in rawpath:
            rawpath.remove("")
        self.buildPath      = "/"+"/".join(x for x in rawpath)+"/"+self.args.build+"/"
        # relative path from the root project to this bitcode project 
        self.relativePath   = Util.getPathDiff(rootPath, self.projectPath)
        # configure bitcode file, tmp folder name and products
        self.BC         = BC
        self.BCname     = self.BC.split(".")[0]
        self.tmpPath    = "/tmp/"+"".join(x for x in self.buildPath.split("/"))+self.BCname+"/"
        self.Command    = cm(self.projectPath, scriptPath=self.buildPath+"scripts/", logFilePath=self.buildPath+"logs/", partition=self.args.partition, environment=Util.SourceScript)
        # check if the bitcode file is there
        self.errors = False
        lf = Util.getLocalFiles(self.buildPath)
        if self.BC not in lf:
            self.errors = True
            self.BCDict = None
            return
        # job ID will be used when bitcode is running the toolchain
        # will hold the entire script dependency tree
        self.jobID = []
        # configure build tools
        self.CC                 = "clang"+self.args.compiler_suffix
        self.CXX                = "clang++"+self.args.compiler_suffix
        self.LD                 = "lld"+self.args.compiler_suffix
        self.OPT                = "opt"+self.args.compiler_suffix
        self.Tracer             = self.args.toolchain_prefix+"lib/AtlasPasses.so"
        self.Backend            = self.args.toolchain_prefix+"lib/libAtlasBackend.a"
        self.Cartographer       = self.args.toolchain_prefix+"bin/newCartographer"
        self.libDetectorBin     = self.args.toolchain_prefix+"bin/libDetector"
        self.DagExtractorPath   = self.args.toolchain_prefix+"bin/dagExtractor"
        self.tikBinary          = self.args.toolchain_prefix+"bin/tik"
        self.tikSwapBinary      = self.args.toolchain_prefix+"bin/tikSwap"
        self.WStool             = self.args.toolchain_prefix+"bin/workingSet"
        self.KHtool             = self.args.toolchain_prefix+"bin/kernelHasher"
        # generate the map that will house all of our files, paths and commands
        self.makeBCDict(LFLAGS, RARGS)
        # SQL pushing objects for trace and kernel data
        self.RunID = run
        self.BCSQL = SQL.BitcodeSQL(self.BC, self.RunID, parentID, self.BCDict, self.args)

    def __hash__(self):
        return hash(self.buildPath+self.BC)

    def __eq__(self, other):
        if isinstance(other, BitCode):
            return self.buildPath+self.BC == other.buildPath+other.BC
        return NotImplemented

    def __neq__(self, other):
        if isinstance(other, BitCode):
            return self.buildPath+self.BC != other.buildPath+other.BC
        return NotImplemented

    def makeBCDict(self, LFLAGS, RARGS):
        """
        @brief      Creates a dictionary that contains all information about this object
        @param[in]  LFLAGS  List of strings where each string is a unique compile-time flag for this bitcode
        @param[in]  RARGS   List of strings where each string is a unique runtime flag for this bitcode
        This function creates all file names, paths, folder names, commands for every step in the TraceAtlas flow and puts them into the BC dictionary.
        """
        self.BCDict = dict()
        BCpath = self.relativePath+self.BCname
        self.BCDict[BCpath] = {}
        self.BCDict[BCpath]["Name"] = self.BC
        self.BCDict[BCpath]["buildPath"] = self.buildPath+self.BC
        for i in range(len(LFLAGS)):
            NTV = self.BCname+"_" + str(i)+".native"
            NTVname = NTV.split(".")[0]
            self.BCDict[BCpath][NTV] = dict()
            self.BCDict[BCpath][NTV]["Name"] = NTV
            self.BCDict[BCpath][NTV]["buildPath"] = self.buildPath+NTV
            tmpFolder = self.tmpPath[:-1]+NTVname+"/"
            self.BCDict[BCpath]["tmpPath"] = tmpFolder+self.BC
            self.BCDict[BCpath][NTV]["tmpFolder"] = tmpFolder 
            self.BCDict[BCpath][NTV]["tmpPath"] = tmpFolder+NTV
            self.BCDict[BCpath][NTV]["TRAbuild"] = self.buildPath+NTVname+".tra"
            self.BCDict[BCpath][NTV]["TRAtmp"] = tmpFolder+NTVname+".tra"
            self.BCDict[BCpath][NTV]["LFLAG"] = LFLAGS[i]
            self.BCDict[BCpath][NTV]["Script"] = self.buildPath + "scripts/makeNative"+NTVname+".sh"
            self.BCDict[BCpath][NTV]["Log"] = self.buildPath+"logs/makeNative"+NTVname+".log"
            self.BCDict[BCpath][NTV]["SUCCESS"] = False
            if len(RARGS) == 0:
                RARGS.append("")
            for j in range(len(RARGS)):
                TRCkey = "TRC"+str(j)
                self.BCDict[BCpath][NTV][TRCkey] = dict()
                TRC = NTV[:-7]+"_"+str(j)+".bin"
                TRCname = TRC.split(".")[0]
                # Trace file name, information, and some counts about the trace
                self.BCDict[BCpath][NTV][TRCkey]["Name"] = TRC
                self.BCDict[BCpath][NTV][TRCkey]["buildPath"] = self.buildPath+TRC
                #tmpFolder = ""
                tmpFolder = self.tmpPath[:-1]+TRCname+"/"
                self.BCDict[BCpath][NTV][TRCkey]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["tmpPath"] = tmpFolder+TRC
                self.BCDict[BCpath][NTV][TRCkey]["BlockFileName"] = "BlockInfo_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["buildPathBlockFile"] = self.buildPath+self.BCDict[BCpath][NTV][TRCkey]["BlockFileName"]
                self.BCDict[BCpath][NTV][TRCkey]["tmpPathBlockFile"]   = tmpFolder+     self.BCDict[BCpath][NTV][TRCkey]["BlockFileName"]
                self.BCDict[BCpath][NTV][TRCkey]["RARG"] = RARGS[j]
                self.BCDict[BCpath][NTV][TRCkey]["Script"] = self.buildPath+"scripts/makeTrace"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["Log"] = self.buildPath+"logs/makeTrace"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["time"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["size"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["SUCCESS"] = False
                # Cartographer information
                self.BCDict[BCpath][NTV][TRCkey]["CAR"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"] = "kernel_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPath"] = self.buildPath+"kernel_"+TRCname+".json"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"].split(".")[0]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPath"] = tmpFolder+"kernel_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPathpigfile"] = self.buildPath+"pig_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPathpigfile"] = tmpFolder+"pig_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPathBBfile"] = self.buildPath+"BB_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPathBBfile"] = tmpFolder+"BB_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Script"] = self.buildPath+"scripts/Cartographer_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Log"] = self.buildPath+"logs/Cartographer_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["time"] = []
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Kernels"] = []
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["SUCCESS"] = False
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["ERRORS"] = {}

    def tmpFileFacility(self, tmpFolder, prefixFiles=[], suffixFiles=[] ):
        """
        @brief Facilitates the setup and teardown required to run in tmp on arbitrary machines
        @param[in] prefixFiles  List of files that need to be copied into the tmp folder at script time for the script to run properly. Entries should point to the files where they stand before the script runs.
        @param[in] suffixFiles  List of files that need to be copied out of the tmp filder after the script commands are done. Entries should point to the files where they stand in the tmp folder.
        """
        # interrupt handler to ensure the tmp folder is always deleted
        prefix =  "except()\n{\n\techo \"Script interrupted! Destroying tmp folder.\"\n\trm -rf "+tmpFolder+"\n\texit\n}\ntrap except 2 9 15 # catch SIGINT SIGKILL SIGTERM\n\n"
        prefix += "hostname ; sleep 1 ; cd /tmp/ ; "
        prefix += "if [ -d \""+tmpFolder+"\" ]; then\n\techo \"Removing old folder!\"\n\trm -rf "+tmpFolder+"\nfi\n"
        prefix += Util.waitOnFile(tmpFolder, tmpFolder, appear=False, message="Waiting for old folder to disappear!")
        prefix += "mkdir "+tmpFolder+" ; " # make new folder and wait for it to be there
        prefix += Util.waitOnFile(tmpFolder, tmpFolder) # wait for the new one to be genned
        prefix += "cd "+tmpFolder+" ; " # change to it
        for entry in prefixFiles:
            prefix += "if cp "+entry+" "+tmpFolder+"; then\n"
            prefix += Util.waitOnFile(tmpFolder+entry.split("/")[-1], tmpFolder, directory=False, message="Waiting on "+entry+" copy!", level=1)
            prefix += "fi\n"
        suffix = ""
        for entry in suffixFiles:
            suffix += Util.waitOnFile(entry, tmpFolder, directory=False, message="Waiting on output file "+entry)
            suffix += "if mv "+entry+" "+self.buildPath+"; then\n"
            suffix += Util.waitOnFile(self.buildPath+entry.split("/")[-1], tmpFolder, directory=False, message="Waiting on "+self.buildPath+entry.split("/")[-1]+" to move!", level=1)
            suffix += "fi\n"
        suffix += "rm -rf "+tmpFolder+" ; " # clean up after ourselves and wait for the removal to complete
        suffix += Util.waitOnFile(tmpFolder, tmpFolder, appear=False, message="Waiting on tmp folder to delete!")
        suffix += "exit" # close the terminal

        return prefix, suffix

    def bashCommandWrapper(self, path, command, step):
        """
        """
        return "if "+command+"; then\n\techo \"DAStepSuccess: "+step+" command succeeded\"\nelse\n\techo \"DAStepERROR: "+step+" command failed\"\n\trm -rf "+path+"\n\texit 1\nfi ; "

    def getProfileCommand(self, BC, NTV, TRC):
        if self.args.opt_level[0]:
            optOptString = "-O"+self.args.opt_level[0]
        else:
            optOptString = ""
        if self.args.opt_level[1]:
            optClangString = "-O"+self.args.opt_level[1]
        else:
            optClangString = ""

        #tmpFolder = self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]
        tmpFolder = self.buildPath
        profileBC = self.BCDict[BC][NTV]["TRAbuild"]
        NTVfile = tmpFolder+"/"+self.BCDict[BC][NTV]["Name"]+".markov"
        TRCfile   = tmpFolder+"/"+self.BCDict[BC][NTV][TRC]["Name"]
        BlockFile = tmpFolder+"/"+self.BCDict[BC][NTV][TRC]["BlockFileName"]
        BCfile    = tmpFolder+"/"+self.BCDict[BC]["Name"]
        command = "export MARKOV_FILE="+TRCfile + " BLOCK_FILE="+BlockFile+" ; "

        optCommand = self.OPT+" -load "+self.Tracer+" -Markov "+BCfile+" -o "+profileBC+" "+optOptString
        clangPPCommand = self.CXX+" -lz -lpthread "+profileBC+" -o "+NTVfile+" "+self.BCDict[BC][NTV]["LFLAG"]+" "+self.Backend +" -fuse-ld="+self.LD+" "+optClangString
        command += optCommand + " ; " + clangPPCommand + " ; "

        profileCommand = NTVfile+" "+self.BCDict[BC][NTV][TRC]["RARG"] + " ; "
        samplingProfileCommand = profileCommand * self.args.samples
        command += samplingProfileCommand


        CARcommand   = self.Cartographer+" -i "+TRCfile+" -b "+BCfile+" -bi "+BlockFile+" -o "+self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"] + " ; "
        samplingCARcommand = CARcommand * self.args.samples
        command += samplingCARcommand
        return command


    def getNativeCommand(self, BC, NTV, TRC):
        if self.args.opt_level[0]:
            optOptString = "-O"+self.args.opt_level[0]
        else:
            optOptString = ""
        if self.args.opt_level[1]:
            optClangString = "-O"+self.args.opt_level[1]
        else:
            optClangString = ""

        #tmpFolder = self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]
        tmpFolder = self.buildPath
        BCfile = tmpFolder+"/"+self.BCDict[BC]["Name"]
        timingBC = self.BCDict[BC][NTV]["TRAbuild"]+".timing"
        NTVfile = tmpFolder+"/"+self.BCDict[BC][NTV]["Name"]+".timing"
        command = ""

        optCommand = self.OPT+" -load "+self.Tracer+" -Timing "+BCfile+" -o "+timingBC+" "+optOptString
        clangPPCommand = self.CXX+" -lz -lpthread "+timingBC+" -o "+NTVfile+" "+self.BCDict[BC][NTV]["LFLAG"]+" "+self.Backend +" -fuse-ld="+self.LD+" "+optClangString
        command += optCommand + " ; " + clangPPCommand + " ; "

        #prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["tmpPath"],self.BCDict[BC][NTV][TRC]["tmpPathBlockFile"]] )
        profileCommand = NTVfile+" "+self.BCDict[BC][NTV][TRC]["RARG"] + " ; "
        samplingProfileCommand = profileCommand * self.args.samples
        command += samplingProfileCommand

        return command

    def getCommand(self, BC, NTV, TRC):
        ntvCommand = self.getNativeCommand(BC, NTV, TRC)
        proCommand = self.getProfileCommand(BC, NTV, TRC)
        return ntvCommand + proCommand