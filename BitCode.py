import Util
from Command import Command as cm
import SQL
import json
import os

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
        self.CC                 = self.args.compiler_toolchain_prefix+"bin/clang"+self.args.compiler_suffix
        self.CXX                = self.args.compiler_toolchain_prefix+"bin/clang++"+self.args.compiler_suffix
        self.LD                 = self.args.compiler_toolchain_prefix+"bin/ld.lld"+self.args.compiler_suffix
        self.OPT                = self.args.compiler_toolchain_prefix+"bin/opt"+self.args.compiler_suffix
        self.Tracer             = self.args.toolchain_prefix+"lib/AtlasPasses.so"
        self.Backend            = self.args.toolchain_prefix+"lib/libAtlasBackend.so"
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
            self.BCDict[BCpath][NTV]["LoopFileName"] = "Loops_"+NTVname+".json"
            self.BCDict[BCpath][NTV]["buildPath"] = self.buildPath+NTV
            self.BCDict[BCpath][NTV]["LFbuildPath"] = self.buildPath+self.BCDict[BCpath][NTV]["LoopFileName"]
            tmpFolder = self.tmpPath[:-1]+NTVname+"/"
            self.BCDict[BCpath]["tmpPath"] = tmpFolder+self.BC
            self.BCDict[BCpath][NTV]["tmpFolder"] = tmpFolder 
            self.BCDict[BCpath][NTV]["tmpPath"] = tmpFolder+NTV
            self.BCDict[BCpath][NTV]["LFtmpPath"] = tmpFolder+self.BCDict[BCpath][NTV]["LoopFileName"]
            self.BCDict[BCpath][NTV]["TRAbuild"] = self.buildPath+NTVname+".tra"
            self.BCDict[BCpath][NTV]["TRAtmp"] = tmpFolder+NTVname+".tra"
            self.BCDict[BCpath][NTV]["LFLAG"] = LFLAGS[i]
            self.BCDict[BCpath][NTV]["Script"] = self.buildPath + "scripts/makeNative"+NTVname+".sh"
            self.BCDict[BCpath][NTV]["Log"] = self.buildPath+"logs/makeNative"+NTVname+".log"
            self.BCDict[BCpath][NTV]["Command"] = self.makeNativeCommand(BCpath, NTV)
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
                self.BCDict[BCpath][NTV][TRCkey]["Command"] = self.makeTraceCommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["Script"] = self.buildPath+"scripts/makeTrace"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["Log"] = self.buildPath+"logs/makeTrace"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["time"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["size"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["SUCCESS"] = False
                # Cartographer information
                self.BCDict[BCpath][NTV][TRCkey]["CAR"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"] = "kernel_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HCName"] = self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"]+"_HotCode.json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HLName"] = self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"]+"_HotLoop.json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPath"] = self.buildPath+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"]
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPath_HC"] = self.buildPath+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HCName"]
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPath_HL"] = self.buildPath+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HLName"]
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"].split(".")[0]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPath"] = tmpFolder+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Name"]
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPath_HC"] = tmpFolder+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HCName"]
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPath_HL"] = tmpFolder+self.BCDict[BCpath][NTV][TRCkey]["CAR"]["HLName"]
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPathpigfile"] = self.buildPath+"pig_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPathpigfile"] = tmpFolder+"pig_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["buildPathBBfile"] = self.buildPath+"BB_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["tmpPathBBfile"] = tmpFolder+"BB_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["dotFileTmpPath"] = tmpFolder+TRCname+".dot"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Script"] = self.buildPath+"scripts/Cartographer_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Log"] = self.buildPath+"logs/Cartographer_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Command"] = self.makeCartographerCommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["time"] = []
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["Kernels"] = []
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["SUCCESS"] = False
                self.BCDict[BCpath][NTV][TRCkey]["CAR"]["ERRORS"] = {}
                # tik information
                self.BCDict[BCpath][NTV][TRCkey]["tik"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Name"] = "tik_"+TRCname+".ll"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["buildPath"] = self.buildPath+"tik_"+TRCname+".ll"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["tik"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["tmpPath"] = tmpFolder+"tik_"+TRCname+".ll"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Script"] = self.buildPath+"scripts/tik_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Countlog"] = self.buildPath+"logs/countTik_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Log"] = self.buildPath+"logs/tik_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Command"] = self.makeTikCommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["Kernels"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["SUCCESS"] = False
                self.BCDict[BCpath][NTV][TRCkey]["tik"]["ERRORS"] = {}
                # tikSwap information
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Name"] = "tikSwap_"+TRCname+".ll"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["buildPath"] = self.buildPath+"tikSwap_"+TRCname+".ll"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["tmpPath"] = tmpFolder+"tikSwap_"+TRCname+".ll"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["binaryTmpPath"] = tmpFolder+"tikSwap_"+TRCname+".exec"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Script"] = self.buildPath+"scripts/tikSwap_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Log"] = self.buildPath+"logs/tikSwap_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Command"] = self.makeTikSwapCommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["Kernels"] = -2
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["SUCCESS"] = False
                self.BCDict[BCpath][NTV][TRCkey]["tikSwap"]["ERRORS"] = {}
                # function annotator information
                self.BCDict[BCpath][NTV][TRCkey]["function"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["function"]["Name"] = "function_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["function"]["buildPath"] = self.buildPath+"function_"+TRCname+".json"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["function"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["function"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["function"]["tmpPath"] = tmpFolder+"function_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["function"]["Script"] = self.buildPath+"scripts/function_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["function"]["Log"] = self.buildPath+"logs/function_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["function"]["Command"] = self.makeDetectorCommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["function"]["SUCCESS"] = False
                # Dag Extractor information
                self.BCDict[BCpath][NTV][TRCkey]["DE"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["Name"] = "DE_"+TRCname+".json"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["DE"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["buildPath"] = self.buildPath+"DE_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["tmpPath"] = tmpFolder+"DE_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["dotFileName"] = TRCname+".dot"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["dotBuildPath"] = self.buildPath+TRCname+".dot"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["dotTmpPath"] = tmpFolder+TRCname+".dot"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["Script"] = self.buildPath+"scripts/DE_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["Log"] = self.buildPath+"logs/DE_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["Command"] = self.makeDEcommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["DE"]["SUCCESS"] = False
                # Working set information
                self.BCDict[BCpath][NTV][TRCkey]["WS"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["Name"] = "WS_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["buildPath"] = self.buildPath+"WS_"+TRCname+".json"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["WS"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["tmpPath"] = tmpFolder+"WS_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["Script"] = self.buildPath+"scripts/WS_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["Log"] = self.buildPath+"logs/WS_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["Command"] = self.makeWScommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["WS"]["SUCCESS"] = False
                # Kernel Hasher information
                self.BCDict[BCpath][NTV][TRCkey]["KH"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["Name"] = "KH_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["buildPath"] = self.buildPath+"KH_"+TRCname+".json"
                tmpFolder = self.tmpPath[:-1]+self.BCDict[BCpath][NTV][TRCkey]["KH"]["Name"]+"/"
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["tmpFolder"] = tmpFolder 
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["tmpPath"] = tmpFolder+"KH_"+TRCname+".json"
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["Script"] = self.buildPath+"scripts/KH_"+TRCname+".sh"
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["Log"] = self.buildPath+"logs/KH_"+TRCname+".log"
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["Command"] = self.makeKHcommand(BCpath, NTV, TRCkey)
                self.BCDict[BCpath][NTV][TRCkey]["KH"]["SUCCESS"] = False
                # Dictionary for PAPI file information, can only be initialized after # of kernels are known
                self.BCDict[BCpath][NTV][TRCkey]["PAPI"] = dict()
                self.BCDict[BCpath][NTV][TRCkey]["PAPI"]["SUCCESS"] = False

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

    def makeNativeCommand(self, BC, NTV):
        """
        @brief      Creates a bash-ready command to build one native file for this bitcode
        @retval     command String
        """
        if self.args.opt_level[0]:
            optOptString = "-O"+self.args.opt_level[0]
        else:
            optOptString = ""

        if self.args.opt_level[1]:
            optClangString = "-O"+self.args.opt_level[1]
        else:
            optClangString = ""
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV]["tmpFolder"], prefixFiles=[self.BCDict[BC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV]["tmpPath"], self.BCDict[BC][NTV]["TRAtmp"],self.BCDict[BC][NTV]["LFtmpPath"]] )
        LOOP_FILE="LOOP_FILE="+self.BCDict[BC][NTV]["LoopFileName"]+" "
        optCommand = LOOP_FILE+self.OPT+" -load "+self.Tracer+" -Markov "+self.BCDict[BC]["tmpPath"]+" -o "+self.BCDict[BC][NTV]["TRAtmp"]+" "+optOptString
        clangPPCommand = self.CXX+" -lz -lpthread "+self.BCDict[BC][NTV]["TRAtmp"]+" -o "+self.BCDict[BC][NTV]["tmpPath"]+" "+self.BCDict[BC][NTV]["LFLAG"]+" "+self.Backend +" -fuse-ld="+self.LD+" "+optClangString
        #scopCommand = self.OPT+" -polly-canonicalize --basic-aa -polly-allow-nonaffine -polly-process-unprofitable -polly-use-llvm-names -polly-ast -polly-export-jscop "+self.BCDict[BC]["tmpPath"] + " -o "+self.BCDict[BC]["Name"]+"_polly"
        return prefix+self.bashCommandWrapper(self.BCDict[BC][NTV]["tmpFolder"], optCommand, "opt")+self.bashCommandWrapper(self.BCDict[BC][NTV]["tmpFolder"], clangPPCommand, "clang++")+suffix
        #return prefix+self.bashCommandWrapper(self.BCDict[BC][NTV]["tmpFolder"], optCommand, "opt")+self.bashCommandWrapper(self.BCDict[BC][NTV]["tmpFolder"], scopCommand, "scop")+self.bashCommandWrapper(self.BCDict[BC][NTV]["tmpFolder"], clangPPCommand, "clang++")+suffix

    def makeTraceCommand(self, BC, NTV, TRC):
        """
        @brief      Creates a bash-ready command that will run the given executable
        @retval     command     Bash-ready command for running the given NTV executable
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["tmpPath"],self.BCDict[BC][NTV][TRC]["tmpPathBlockFile"]] )

        envSet = "export LD_LIBRARY_PATH="+self.args.toolchain_prefix+"lib/ MARKOV_FILE="+self.BCDict[BC][NTV][TRC]["Name"] + " BLOCK_FILE="+self.BCDict[BC][NTV][TRC]["BlockFileName"] + " ; "
        NTVfile = self.BCDict[BC][NTV][TRC]["tmpFolder"]+self.BCDict[BC][NTV]["Name"]
        trcCommand = "time -p "+NTVfile+" "+self.BCDict[BC][NTV][TRC]["RARG"]
        return prefix+envSet+self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["tmpFolder"], trcCommand, "trace")+suffix

    def makeCartographerCommand(self, BC, NTV, TRC):
        """
        @brief      Creates commands that will run the kernel tool on each trace.
        @retval     commandList List of commands ready to be put into a bash script.
                    returnFiles Names of each bash script to be made. Indices of each list match each other.
        """
        # files copied from build folder that are required as input
        profile   = self.BCDict[BC][NTV][TRC]["buildPath"]
        bitcode   = self.BCDict[BC]["buildPath"]
        blockfile = self.BCDict[BC][NTV][TRC]["buildPathBlockFile"]
        loopfile  = self.BCDict[BC][NTV]["LFbuildPath"]
        # output files copied from tmp folder to build folder
        dotFile   = self.BCDict[BC][NTV][TRC]["CAR"]["dotFileTmpPath"]
        outputKF  = self.BCDict[BC][NTV][TRC]["CAR"]["tmpPath"]
        outputHC  = self.BCDict[BC][NTV][TRC]["CAR"]["tmpPath_HC"]
        outputHL  = self.BCDict[BC][NTV][TRC]["CAR"]["tmpPath_HL"]
        # generates header,footer commands for the bash script to move input and output files
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"], prefixFiles=[profile, bitcode, blockfile,loopfile], suffixFiles=[outputKF,dotFile,outputHC,outputHL] if self.args.hotcode_detection else [outputKF, dotFile] )
        
        TRCfile   = self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["Name"]
        BlockFile = self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["BlockFileName"]
        BCfile    = self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]+self.BCDict[BC]["Name"]
        hotCode   = " -h -l "+self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"]+"/"+self.BCDict[BC][NTV]["LoopFileName"] if self.args.hotcode_detection else ""
        command   = "LD_LIBRARY_PATH="+self.args.toolchain_prefix+"lib/ "+self.Cartographer+hotCode+" -i "+TRCfile+" -b "+BCfile+" -bi "+BlockFile+" -d "+dotFile+" -o "+self.BCDict[BC][NTV][TRC]["CAR"]["tmpPath"]

        return prefix + self.bashCommandWrapper( self.BCDict[BC][NTV][TRC]["CAR"]["tmpFolder"], command, "cartographer" ) + suffix

    def makeTikCommand(self, BC, NTV, TRC):
        """
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["tik"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], self.BCDict[BC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["tik"]["tmpPath"]] )

        kernelFile = self.BCDict[BC][NTV][TRC]["tik"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["CAR"]["Name"]
        BCfile = self.BCDict[BC][NTV][TRC]["tik"]["tmpFolder"]+self.BCDict[BC]["Name"]

        tikCommand = self.tikBinary+" -f LLVM -j "+kernelFile+" -t=LLVM -o "+self.BCDict[BC][NTV][TRC]["tik"]["tmpPath"]+" -S -v 5 -l "+self.BCDict[BC][NTV][TRC]["tik"]["Log"]+" "+BCfile
        return prefix +self.bashCommandWrapper( self.BCDict[BC][NTV][TRC]["tik"]["tmpFolder"], tikCommand, "tik" )+ suffix

    def makeTikSwapCommand(self, BC, NTV, TRC):
        """
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["tik"]["buildPath"], self.BCDict[BC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpPath"]] )

        BCfile = self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"]+self.BCDict[BC]["Name"]
        tikFile = self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["tik"]["Name"]
        tikFileCheck = "[ -f "+tikFile+" ]"
        tikSwapCommand = self.tikSwapBinary+" -t "+tikFile+" -b "+BCfile+" -o "+self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpPath"]
        compilationCommand = self.CXX+" -O3 -lz -lpthread -fuse-ld="+self.LD+" "+self.BCDict[BC][NTV]["LFLAG"]+" "+tikFile+" "+self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpPath"]+" "+self.Backend+" -o "+self.BCDict[BC][NTV][TRC]["tikSwap"]["binaryTmpPath"]
        runCommand = self.BCDict[BC][NTV][TRC]["tikSwap"]["binaryTmpPath"]+" "+self.BCDict[BC][NTV][TRC]["RARG"]
        return prefix + self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"], tikFileCheck, "tikFileCheck") + \
                        self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"], tikSwapCommand, "TikSwap") + \
                        self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"], compilationCommand, "Tik Compilation") + \
                        self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["tikSwap"]["tmpFolder"], runCommand, "Tik Binary") + suffix

    def makeDetectorCommand(self, BC, NTV, TRC):
        """
        @brief      Creates commands that facilitate the libDetector tool.
        @retval     Command in string form. The command assumes its input files are local
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["function"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], self.BCDict[BC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["function"]["tmpPath"]] )
        
        BCfile = self.BCDict[BC][NTV][TRC]["function"]["tmpFolder"]+self.BCDict[BC]["Name"]
        kernelFile = self.BCDict[BC][NTV][TRC]["function"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["CAR"]["Name"]
        libDetectorCommand = self.libDetectorBin+" -i "+BCfile +" -k "+kernelFile+" -o "+self.BCDict[BC][NTV][TRC]["function"]["tmpPath"]
        return prefix + self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["function"]["tmpFolder"], libDetectorCommand, "libDetector") + suffix

    def makeDEcommand(self, BC, NTV, TRC):
        """
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["DE"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], self.BCDict[BC][NTV][TRC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["DE"]["tmpPath"], self.BCDict[BC][NTV][TRC]["DE"]["dotTmpPath"]] )
        
        kernelFile = self.BCDict[BC][NTV][TRC]["DE"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["CAR"]["Name"]
        traceFile = self.BCDict[BC][NTV][TRC]["DE"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["Name"]
        DEcommand = self.DagExtractorPath+" -k "+kernelFile+" -t "+traceFile+" -d "+self.BCDict[BC][NTV][TRC]["DE"]["dotTmpPath"]+" -o "+self.BCDict[BC][NTV][TRC]["DE"]["tmpPath"]+" --nb"
        return prefix + self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["DE"]["tmpFolder"], DEcommand, "DagExtractor") + suffix

    def makeWScommand(self, BC, NTV, TRC):
        """
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["WS"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], self.BCDict[BC][NTV][TRC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["WS"]["tmpPath"]] )
        
        kernelFile = self.BCDict[BC][NTV][TRC]["WS"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["CAR"]["Name"]
        traceFile = self.BCDict[BC][NTV][TRC]["WS"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["Name"]
        WScommand = self.WStool+" -i "+traceFile+" -k "+kernelFile+" -o "+self.BCDict[BC][NTV][TRC]["WS"]["tmpPath"]+" --nb"
        return prefix + self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["WS"]["tmpFolder"], WScommand, "WorkingSet") + suffix

    def makeKHcommand(self, BC, NTV, TRC):
        """
        """
        prefix, suffix = self.tmpFileFacility( self.BCDict[BC][NTV][TRC]["KH"]["tmpFolder"], prefixFiles=[self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], self.BCDict[BC]["buildPath"]], suffixFiles=[self.BCDict[BC][NTV][TRC]["KH"]["tmpPath"]] )

        kernelFile = self.BCDict[BC][NTV][TRC]["KH"]["tmpFolder"]+self.BCDict[BC][NTV][TRC]["CAR"]["Name"]
        BCfile     = self.BCDict[BC][NTV][TRC]["KH"]["tmpFolder"]+self.BCDict[BC]["Name"]
        KHcommand  = self.KHtool+" -k "+kernelFile+" -i "+BCfile+" -o "+self.BCDict[BC][NTV][TRC]["KH"]["tmpPath"]
        return prefix + self.bashCommandWrapper(self.BCDict[BC][NTV][TRC]["KH"]["tmpFolder"], KHcommand, "KernelHasher") + suffix

    def makeScripts(self):
        """
        @brief Creates a script for the given step
        @param[in] step     Integer index of the 
        """
        # list of list of lists of [strings, (tuple of strings)] where each innermost list is a sequence of scripts to be handed to self.Comand
        # one level outside the innermost is a list of entries for the build flow of each NTV
        # the outermost level has entries for each BC
        runQueue = []
        i = 0
        for BC in self.BCDict:
            runQueue.append([])
            j = 0
            for NTV in self.BCDict[BC]:
                if NTV[-6:] == "native":
                    runQueue[i].append([])
                    NTVdict = self.BCDict[BC][NTV]
                    # make natives
                    runQueue[i][j].append( self.Command.constructBashFile(NTVdict["Script"], NTVdict["Command"], NTVdict["Log"], environment=Util.SourceScript) )
                    k = 1 # because the first index is the NTV command
                    for TRC in self.BCDict[BC][NTV]:
                        if TRC.startswith("TRC"):
                            runQueue[i][j].append([])
                            # make Profiles tied to their native scripts
                            TRCdict = self.BCDict[BC][NTV][TRC]
                            runQueue[i][j][k].append( self.Command.constructBashFile(TRCdict["Script"], TRCdict["Command"], TRCdict["Log"], environment=Util.SourceScript) )
                            # make cartographers tied to their trace scripts
                            CARdict = TRCdict["CAR"]
                            runQueue[i][j][k].append( self.Command.constructBashFile(CARdict["Script"], CARdict["Command"], CARdict["Log"], environment=Util.SourceScript) )
                            # tikSwap is tied to tik, therefore it immediately follows tik within brackets
                            # tik, DE, func, WS, KH all tied to the cartographer script
                            #ExtraTuple = (  self.Command.constructBashFile(TRCdict["tik"]["Script"], TRCdict["tik"]["Command"], TRCdict["tik"]["Log"], timeLimit=10 ), \
                                            #[ self.Command.constructBashFile(TRCdict["tikSwap"]["Script"], TRCdict["tikSwap"]["Command"], TRCdict["tikSwap"]["Log"], timeLimit=10 ) ], \
                                            #self.Command.constructBashFile(TRCdict["DE"]["Script"], TRCdict["DE"]["Command"], TRCdict["DE"]["Log"] ), \
                                            #self.Command.constructBashFile(TRCdict["function"]["Script"], TRCdict["function"]["Command"], TRCdict["function"]["Log"] ),\
                                            #self.Command.constructBashFile(TRCdict["WS"]["Script"], TRCdict["WS"]["Command"], TRCdict["WS"]["Log"] ), \
                                            #self.Command.constructBashFile(TRCdict["KH"]["Script"], TRCdict["KH"]["Command"], TRCdict["KH"]["Log"]) )
                            #runQueue[i][j][k].append(ExtraTuple)
                            k += 1 # increment TRC counter
                    j += 1 # increment NTV counter
            i += 1 # increment BC counter
        return runQueue

    def run(self):
        """
        @brief Runs the configured build flow as described by the input args for this particular bitcode
        """
        runQueue = self.makeScripts()
        for BC in runQueue:
            for NTV in BC:
                self.jobID.append( self.Command.run(NTV, dependency=True) )

    def done(self):
        """
        """
        if not self.Command.poll(self.jobID, checkDependencies=False):
            # get size and times for SQL push
            self.sizeAndTime()
            # push to SQL
            self.BCSQL.push()
            # delete trace if needed
            if not self.args.keep_trace:
                self.deleteProfiles()
            return True

    def sizeAndTime(self):
        for BC in self.BCDict:
            for NTV in self.BCDict[BC]:
                if NTV[-6:] == "native":
                    for TRC in self.BCDict[BC][NTV]:
                        if TRC.startswith("TRC"):
                            self.BCDict[BC][NTV][TRC]["size"] = Util.getProfilesize(self.BCDict[BC][NTV][TRC]["buildPath"])
                            self.BCDict[BC][NTV][TRC]["time"] = Util.getLogTime(self.BCDict[BC][NTV][TRC]["Log"])
                            self.BCDict[BC][NTV][TRC]["CAR"]["time"] = Util.getLogTime(self.BCDict[BC][NTV][TRC]["CAR"]["Log"])

    def report(self):
        """
        """
        reportDict = dict()
        reportDict["Errors"] = list()
        reportDict["Total"] = dict()
        reportDict["Total"]["Size"] = 0
        reportDict["Total"]["Executables"] = 0
        reportDict["Total"]["Profiles"] = 0
        reportDict["Total"]["Failed Profiles"] = 0
        reportDict["Total"]["Segmented Profiles"] = 0
        reportDict["Total"]["Tik Profiles"] = 0
        reportDict["Total"]["Tik Swaps"] = 0
        reportDict["Total"]["Tik Compilations"] = 0
        reportDict["Total"]["Tik Successes"] = 0
        reportDict["Total"]["Cartographer Kernels"] = 0
        reportDict["Total"]["Tik Kernels"] = 0
        reportDict["Total"]["TikSwap Kernels"] = 0
        reportDict["Total"]["Tik Compilation Kernels"] = 0
        reportDict["Total"]["Tik Success Kernels"] = 0
        reportDict["Total"]["Average Kernel Size (Nodes)"] = 0        
        reportDict["Total"]["Average Kernel Size (Blocks)"] = 0        
        reportDict["Total"]["Cartographer Errors"] = dict()
        reportDict["Total"]["Tik Errors"] = dict()
        reportDict["Total"]["TikSwap Errors"] = dict()
        if self.BCDict == None:
            reportDict["Errors"] += ["Bitcode file not found"]
            return reportDict

        # keeps track of all Profiles that had non-zero kernels
        nonzeroProfiles = 0
        for BC in self.BCDict:
            reportDict[BC] = dict()
            for NTV in self.BCDict[BC]:
                if NTV[-6:] == "native":
                    reportDict[BC][NTV] = dict()
                    # if the native failed, don't look at anything else
                    if Util.findErrors(self.BCDict[BC][NTV]["Log"]):
                        reportDict["Errors"].append(self.BCDict[BC][NTV]["Log"])
                        continue
                    # add the executable
                    reportDict["Total"]["Executables"] += 1
                    self.BCDict[BC][NTV]["SUCCESS"] = True
                    for TRC in self.BCDict[BC][NTV]:
                        if TRC.startswith("TRC"):
                            """
                            # if the trace failed, don't look at anything else
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["Log"])
                                reportDict["Total"]["Failed Profiles"] += 1
                                continue
                            """
                            self.BCDict[BC][NTV][TRC]["SUCCESS"] = True

                            reportDict[BC][NTV][TRC] = dict()
                            # record the trace
                            reportDict["Total"]["Profiles"] += 1
                            # trace size and time integration
                            
                            reportDict[BC][NTV][TRC]["size"] = self.BCDict[BC][NTV][TRC]["size"]
                            reportDict["Total"]["Size"] += reportDict[BC][NTV][TRC]["size"]
                            reportDict[BC][NTV][TRC]["TRCtime"] = self.BCDict[BC][NTV][TRC]["time"]
                            # kernel size stats
                            reportDict[BC][NTV][TRC]["Average Kernel Size (Nodes)"] = Util.getAvgKSize(self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], Nodes=True)
                            reportDict["Total"]["Average Kernel Size (Nodes)"] += float(reportDict[BC][NTV][TRC]["Average Kernel Size (Nodes)"])
                            reportDict[BC][NTV][TRC]["Average Kernel Size (Blocks)"] = Util.getAvgKSize(self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"], Blocks=True)
                            reportDict["Total"]["Average Kernel Size (Blocks)"] += float(reportDict[BC][NTV][TRC]["Average Kernel Size (Blocks)"])
                            # parse cartographer errors
                            self.BCDict[BC][NTV][TRC]["CAR"]["ERRORS"] = Util.getCartographerErrors(self.BCDict[BC][NTV][TRC]["CAR"]["Log"])
                            reportDict[BC][NTV][TRC]["Cartographer Errors"] = self.BCDict[BC][NTV][TRC]["CAR"]["ERRORS"]
                            for key in self.BCDict[BC][NTV][TRC]["CAR"]["ERRORS"]:
                                if reportDict["Total"]["Cartographer Errors"].get(key, None) is None:
                                    reportDict["Total"]["Cartographer Errors"][key] = 0
                                reportDict["Total"]["Cartographer Errors"][key] += self.BCDict[BC][NTV][TRC]["CAR"]["ERRORS"][key]
                            # if the cartographer failed, don't look at anything else
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["CAR"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["CAR"]["Log"])
                                continue

                            reportDict["Total"]["Segmented Profiles"] += 1
                            self.BCDict[BC][NTV][TRC]["CAR"]["SUCCESS"] = True
                            reportDict[BC][NTV][TRC]["CARtime"] = self.BCDict[BC][NTV][TRC]["CAR"]["time"]
                            self.BCDict[BC][NTV][TRC]["CAR"]["Kernels"] = Util.getCartographerKernels(self.BCDict[BC][NTV][TRC]["CAR"]["buildPath"])
                            reportDict[BC][NTV][TRC]["Cartographer Kernels"] = self.BCDict[BC][NTV][TRC]["CAR"]["Kernels"]
                            reportDict["Total"]["Cartographer Kernels"] += reportDict[BC][NTV][TRC]["Cartographer Kernels"]
                            if self.BCDict[BC][NTV][TRC]["CAR"]["Kernels"] <= 0:
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["Log"]+" -> 0 Kernels")
                            else:
                                nonzeroProfiles += 1
                            """
                            # accessories
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["DE"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["DE"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["DE"]["SUCCESS"] = True
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["function"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["function"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["function"]["SUCCESS"] = True
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["KH"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["KH"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["KH"]["SUCCESS"] = True
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["WS"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["WS"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["WS"]["SUCCESS"] = True
                            # parse tik information
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["tik"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["tik"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["tik"]["SUCCESS"] = True
                                reportDict["Total"]["Tik Profiles"] += 1
                            self.BCDict[BC][NTV][TRC]["tik"]["Kernels"] = Util.getTikKernels(self.BCDict[BC][NTV][TRC]["tik"]["Log"])
                            reportDict[BC][NTV][TRC]["Tik Kernels"] = self.BCDict[BC][NTV][TRC]["tik"]["Kernels"] if self.BCDict[BC][NTV][TRC]["tik"]["Kernels"] > 0 else 0
                            reportDict["Total"]["Tik Kernels"] += reportDict[BC][NTV][TRC]["Tik Kernels"]
                            self.BCDict[BC][NTV][TRC]["tik"]["ERRORS"] = Util.getTikErrors(self.BCDict[BC][NTV][TRC]["tik"]["Log"])
                            reportDict[BC][NTV][TRC]["Tik Errors"] = self.BCDict[BC][NTV][TRC]["tik"]["ERRORS"]
                            for key in self.BCDict[BC][NTV][TRC]["tik"]["ERRORS"]:
                                if reportDict["Total"]["Tik Errors"].get(key, None) is None:
                                    reportDict["Total"]["Tik Errors"][key] = 0
                                reportDict["Total"]["Tik Errors"][key] += self.BCDict[BC][NTV][TRC]["tik"]["ERRORS"][key]

                            # parse tikSwap information
                            if Util.findErrors(self.BCDict[BC][NTV][TRC]["tikSwap"]["Log"]):
                                reportDict["Errors"].append(self.BCDict[BC][NTV][TRC]["tikSwap"]["Log"])
                            else:
                                self.BCDict[BC][NTV][TRC]["tikSwap"]["SUCCESS"] = True
                            swaps, comps, successes = Util.parseTikSwapResults(self.BCDict[BC][NTV][TRC]["tikSwap"]["Log"])
                            reportDict[BC][NTV][TRC]["TikSwap Kernels"] = swaps[0]
                            reportDict[BC][NTV][TRC]["Tik Swaps"] = swaps[1]
                            reportDict["Total"]["TikSwap Kernels"] += reportDict[BC][NTV][TRC]["TikSwap Kernels"]
                            reportDict["Total"]["Tik Swaps"] += reportDict[BC][NTV][TRC]["Tik Swaps"]
                            reportDict[BC][NTV][TRC]["Tik Compilation Kernels"] = comps[0]
                            reportDict[BC][NTV][TRC]["Tik Compilations"] = comps[1]
                            reportDict["Total"]["Tik Compilation Kernels"] += reportDict[BC][NTV][TRC]["Tik Compilation Kernels"]
                            reportDict["Total"]["Tik Compilations"] += reportDict[BC][NTV][TRC]["Tik Compilations"]
                            reportDict[BC][NTV][TRC]["Tik Success Kernels"] = successes[0]
                            reportDict[BC][NTV][TRC]["Tik Successes"] = successes[1]
                            reportDict["Total"]["Tik Success Kernels"] += reportDict[BC][NTV][TRC]["Tik Success Kernels"]
                            reportDict["Total"]["Tik Successes"] += reportDict[BC][NTV][TRC]["Tik Successes"]
                            self.BCDict[BC][NTV][TRC]["tikSwap"]["ERRORS"] = Util.getTikSwapErrors(self.BCDict[BC][NTV][TRC]["tikSwap"]["Log"])
                            reportDict[BC][NTV][TRC]["TikSwap Errors"] = self.BCDict[BC][NTV][TRC]["tikSwap"]["ERRORS"]
                            for key in self.BCDict[BC][NTV][TRC]["tikSwap"]["ERRORS"]:
                                if reportDict["Total"]["TikSwap Errors"].get(key, None) is None:
                                    reportDict["Total"]["TikSwap Errors"][key] = 0
                                reportDict["Total"]["TikSwap Errors"][key] += self.BCDict[BC][NTV][TRC]["tikSwap"]["ERRORS"][key]
                            """

        # normalize average kernel size stats to the number of Profiles because the cartographer gives us per-trace averages
        # only count the programs that had more than 1 kernel
        reportDict["Total"]["Average Kernel Size (Nodes)"] = reportDict["Total"]["Average Kernel Size (Nodes)"] / float(nonzeroProfiles) if nonzeroProfiles > 0 else 0
        reportDict["Total"]["Average Kernel Size (Blocks)"] = reportDict["Total"]["Average Kernel Size (Blocks)"] / float(nonzeroProfiles) if nonzeroProfiles > 0 else 0
        return reportDict

    def deleteProfiles(self):
        """
        """
        for BC in self.BCDict:
            for NTV in self.BCDict[BC]:
                if NTV[-6:] == "native":
                    for TRC in self.BCDict[BC][NTV]:
                        if TRC.startswith("TRC"):
                            try:
                                os.remove(self.BCDict[BC][NTV][TRC]["buildPath"])
                            except FileNotFoundError:
                                doNothing = True
