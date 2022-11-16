import Util
import pyodbc
import time
import logging
import json
import ctypes

globLog = logging.getLogger("SQLDatabase")

# keep track of the number of DB connections we make
DB_COUNT = 0
# cannot create more than one DB connection at a time
DB_MAX_COUNT = 1

class SQLDataBase:
    DB_COUNT += 1
    if DB_COUNT > DB_MAX_COUNT:
        raise ValueError("Cannot create more than one DB connection at a time!")
    # by default, this class is not active, and when it is not, it doesn't submit SQL commands.
    enabled  = False
    # connection parameters for pyodbc
    username = None
    password = None
    database = None
    server   = None
    cnxn     = None
    # when the connection breaks for whatever reason, this flag is raised to alert class children of a possible change
    reset    = False
    # If true, autocommits each SQL statement as they are submitted. If false, explicit commit is required
    # When autocom is off, locks on rows of the database can remain open indefinitely, increasing the hazard of deadlock for the sql service
    autocom  = True
    # Timeout period to wait for a lock when querying a locked row (for example)
    # If the timeout period is reached, the query returns an error
    # Applied to all statements, and valid for the entire connection
    timeout  = 1000

    @classmethod
    def __enabled__(cls, flag):
        """
        """
        cls.enabled = flag

    @classmethod
    def __server__(cls, name):
        """
        @param[in]  server      Address of the server hosting the database.
        """
        cls.server = name

    @classmethod
    def __database__(cls, name):
        """
        @param[in]  database    Literal name of the database.
        """
        cls.database = name

    @classmethod
    def __username__(cls, name):
        """
        @param[in]  username    Username for logging into the database.
        """
        cls.username = name

    @classmethod
    def __password__(cls, word):
        """
        @param[in]  password    Password for the username.
        """
        cls.password = word

    @classmethod
    def connect(cls):
        """
        @brief      Creates an active connection to the target SQL database.
        """
        if cls.enabled:
            if cls.cnxn is None:
                cls.cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};SERVER="+cls.server+";DATABASE="+cls.database+";UID="+cls.username+";PWD="+cls.password, autocommit=cls.autocom)
            else:
                raise ValueError("Cannot connect to another database while a connection is still active!")
            # set timeout period for locks
            cls.command("SET LOCK_TIMEOUT "+str(cls.timeout)+";")
            
    @classmethod
    def disconnect(cls):
        """
        @brief      Explicitly closes the connection between the self object and its SQL database. Called at the end of pushToSQL in dashAutomate
                    class.
        """
        if cls.enabled:
            cls.cnxn.close()
            cls.cnxn = None

    @classmethod
    def command(cls, command, ret=False):
        """
        @brief      Allows the user to insert a raw sql command into the valid dashDatabase object.
        @param[in]  command     Raw string that will be inserted into the valid SQL command line of this object.
        @param[in]  ret         Returns result of a query, if desired
        """
        if cls.enabled:
            globLog.debug(command)
            if cls.cnxn == None:
                raise ValueError("Cannot submit a command when there is no DB connection!")

            try:
                curse = cls.cnxn.execute(command)
            except Exception as e:
                globLog.critical("Exception thrown when pushing SQL command: \n\t"+str(e))
                cls.handleException(e)
                if ret:
                    return []
                return 

            if ret:
                try:
                    row = curse.fetchall()
                except Exception as e:
                    globLog.critical("Exception thrown when requesting SQL return data:\n\t"+str(e))
                    row = []
                    cls.handleException(e)
                return row
            else:
                return
        else:
            if ret:
                return []

    @classmethod
    def getLastID(cls, handle=True):
        """
        @brief      Retrieves the ID of the last entry put into the database by the object self.
                    This will only return the last ID generated for this SQL connection
        """
        if cls.enabled:
            if cls.cnxn == None:
                raise ValueError("Cannot retrieve an ID from the DB when there is no DB connection!")
            returnlist = []

            try:
                curse = cls.cnxn.execute("SELECT SCOPE_IDENTITY() ")
            except Exception as e:
                globLog.critical("Exception thrown when running 'SELECT SCOPE_IDENTITY()':\n\t"+str(e))
                if handle:
                    cls.handleException(e)
                return -1
            try:
                row = curse.fetchall()
            except Exception as e:
                globLog.error("When getting last ID of SQL push: "+str(e))
                if handle:
                    cls.handleException(e)
                return -1
        
            ID = row[0][0] # ID should just be the first entry
            if ID is None:
                ID = -1
            globLog.debug("ID -> "+str(ID))
            return ID 

    @classmethod
    def commit(cls):
        """
        @brief      Equivalent to 'GO' in a SQL terminal. By default changes are not made to the database, this function must be called to do so. 
                    Note that even when this isn't called, the UIDs of each pending row are still valid, and will not reappear in the database.
        """
        if cls.enabled:
            if cls.cnxn == None:
                raise ValueError("Cannot commit changes when there is no DB connection!")
            try:
                cls.cnxn.commit()
            except Exception as e:
                globLog.critical("Exception thrown when running cnxn.cursor.commit()':\n\t"+str(e))
                cls.handleException(e)
                return 
            
            globLog.debug("Committed changes")

    @classmethod
    def reconnect(cls):
        """
        @brief Checks the connection and attempts to reset and reestablish if necessary
        """
        if cls.enabled:
            tries = 0
            success = False
            while not success and tries <= 9:
                time.sleep(2**tries)
                tries += 1
                globLog.warning("Attempting to reconnect to database...")
                cls.disconnect()
                cls.connect()
                # try to retrieve the most recent UID generated for the kernel table
                try:
                    curse = cls.cnxn.execute("SELECT IDENT_CURRENT( 'Kernels' );")
                except Exception as e:
                    globLog.error("When testing reestablished connection the following exception ocurred: "+str(e))
                    continue
                out = curse.fetchall()
                globLog.info("Returned value after reconnection attempt was "+str(out))
                success = True if out[0][0] is not None else False

            if not success:
                exit("Connection could not be reestablished. Exiting...")

            globLog.info("Successfully reestablished connection!")
            cls.reset = True

    @classmethod
    def handleException(cls, e):
        """
        """
        if "08S01" in str(e):
            # communication link failure
            cls.reconnect()
        
class DashAutomateSQL(SQLDataBase):
    def __init__(self, path, previous):
        """
        @brief Pushes RunID
        @param[in] path     Absolute path to the directory in which the Dash-Automate tool was called
        @param[in] previous Previous RunID that should be referenced when creating the project list for a nightly build.
        """
        self.path = path
        GitIDs = Util.getGitRepoIDs(path)
        self.corpusGitId = GitIDs[0]
        self.radioCorpusGitId = GitIDs[1]
        self.SDHGitId = GitIDs[2]
        self.KSSId = GitIDs[3]
        self.KCId  = GitIDs[4]
        self.oldID = previous
        # maps a project's relative path to its project to run
        self.pathProject = dict()
        self.ID = None
        self.runtime = "'"+time.strftime("%Y-%m-%d %H:%M:%S")+"'"
        self.logger = logging.getLogger("DashAutomate SQL")

    def pushRunID(self):
        """
        @brief Pushes an entry into the RunID table for a Dash-Corpus build
        @param[in]  path        Path to the relative directory of this tool.
        @param[in]  argDict     Dictionary containing all runtime args of this tool.
        @param[in]  dashDB      Optional flag containing either an active dashDatabase object with a valid connection, or nothing. 
                                Useful for when the tool is not recursing on subdirectories and already has a valid dashDB object.
        @param[in]  first       Indicates whether or not this is a subdirectory call. If this flag is true, the dashDB object created
                                immediately disconnects after pushing to RunId.
        @retval     ID          New UID of this RunId entry
                    runtime     String representation of the time of this run.
        """
        pushCom = "INSERT INTO RunIds (TimeExecuted,CorpusID,RadioID) VALUES ("+self.runtime+",'"+self.corpusGitId+"','"+self.radioCorpusGitId+"');"
        super().command(pushCom)
        self.ID = super().getLastID()

    def ExistingProjects(self):
        """
        @brief Creates a list of programs that summarize all traces in the current RunID

        The return list is composed of tuples: [(project path, BC, NTV, TRC, LFLAG, RARG, TRCtime, CARtime)]
        NOTE: the TRC name is actually the same as the NTV name, or binary name. The pushing protocol was changed to assign binary name to trace name after RunID 2300.
        """
        selCom = "SELECT Root.Path, Kernels.Binary, Kernels.LFLAG, Kernels.RARG, FlowMetrics.TraceTime, FlowMetrics.KernelDetectTime, Kernels.Hash FROM Kernels INNER JOIN FlowMetrics ON Kernels.FlowId = FlowMetrics.UID AND Kernels.RunId = "+str(self.oldID)+" INNER JOIN Root ON Kernels.Parent = Root.UID;"
        rows = super().command(selCom, ret=True)
        traceList = []
        for row in rows:
            relPath = ""
            if "build" in row[0].split("/")[-1]:
                relPath = row[0].split("/")[:-1]
            else:
                relPath = row[0].split("/")
            while "" in relPath:
                relPath.remove("")
            relPath = "/".join(x for x in relPath)+"/"
            trcName = row[1].split(".")[0]+"_"+str(len(traceList))+".trc"
            bcName = "_".join(x for x in trcName.split("_")[:-2])
            ntvName = "_".join(x for x in trcName.split("_")[:-1])
            LFLAG = row[2]
            RARG  = row[3]
            trcTime = row[4] if row[4] > 0 else 0
            carTime = row[5] if row[5] > 0 else 0
            h = int(row[6]) if row[6] is not None else 0
            traceList.append( (relPath, bcName, ntvName, trcName, LFLAG, RARG, trcTime, carTime, h) )

        # now sort the incoming data into a map
        traceMap = dict()
        for entry in traceList:
            if traceMap.get(entry[0], None) is None:
                traceMap[entry[0]] = dict()
            if traceMap[entry[0]].get(entry[1], None) is None:
                traceMap[entry[0]][entry[1]] = dict()
            if traceMap[entry[0]][entry[1]].get(entry[2], None) is None:
                traceMap[entry[0]][entry[1]][entry[2]] = dict()
            if traceMap[entry[0]][entry[1]][entry[2]].get(entry[3], None) is None:
                traceMap[entry[0]][entry[1]][entry[2]][entry[3]] = dict()

            if traceMap[entry[0]][entry[1]][entry[2]][entry[3]].get("Parameters", None) is None:
                traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Parameters"] = (entry[4],entry[5])

            if traceMap[entry[0]][entry[1]][entry[2]][entry[3]].get("Hashes", None) is None:
                traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Hashes"] = set()
            traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Hashes"].add( ctypes.c_long(entry[8]).value )

            if traceMap[entry[0]][entry[1]][entry[2]][entry[3]].get("Kernels", None) is None:
                traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Kernels"] = 0
            traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Kernels"] += 1

            if traceMap[entry[0]][entry[1]][entry[2]][entry[3]].get("Time", None) is None:
                traceMap[entry[0]][entry[1]][entry[2]][entry[3]]["Time"] = int(entry[6])+int(entry[7])
        for path in traceMap:
            for BC in traceMap[path]:
                for NTV in traceMap[path][BC]:
                    for TRC in traceMap[path][BC][NTV]:
                        traceMap[path][BC][NTV][TRC]["Hashes"] = list(traceMap[path][BC][NTV][TRC]["Hashes"])
        with open("traceMap.json","w") as f:
            json.dump(traceMap, f, indent=4)

        return traceMap

class ProjectSQL(SQLDataBase):
    def __init__(self, relativePath, inputdict):
        """
        @brief Facilitates pushing to the Root table in Dash-Ontology database
        @param[in] abspath      Relative path from the root build directory to the specific directory of this project within the corpus.
        @param[in] inputdict    Input JSON file containing User information
        """
        self.relPath = relativePath
        self.author = Util.getAuthor(inputdict)
        self.libraries = Util.getLibraries(inputdict)
        self.ID = -1
        self.logger = logging.getLogger("Project: "+self.relPath)
        self.newEntry = False

    def getOldPost(self):
        """
        @brief Retrieve an entry from the database that may already represent the current object in the database
        """
        dataList = super().command("SELECT * FROM Root WHERE Path = '"+self.relPath+"';", ret=True)
        if len(dataList) == 0:
            self.logger.debug("No prior Root entry found")
            return None
        else:
            self.logger.debug("Prior Root entry found.")
            return dataList

    def push(self):
        """
        @brief      Pushes root entry for the given project path
        @retval     RootID      Entry ID for the root table entry
        """
        oldPost = self.getOldPost()
        if oldPost is not None:
            oldPost = list(oldPost[0]) # arrives as a list of tuples, just take the first entry. TODO: to handle multiple results, we need to match authors and libraries too
            self.ID = oldPost[0] # format: [UID, Path, Author, Libraries]
            if self.author != oldPost[2] or self.libraries != oldPost[3]:
                self.newEntry = True
                self.logger.debug("Updating Libraries and Author from "+oldPost[2]+","+oldPost[3]+" to "+self.libraries+","+self.author)
                super().command("UPDATE Root SET Libraries = '"+self.libraries+"', Author = '"+self.author+"' WHERE Uid = "+str(self.ID)+";")
            return self.ID
        else:
            self.newEntry = True
            super().command("INSERT INTO Root (Path,Author,Libraries) VALUES ('"+self.relPath+"','"+self.author+"','"+self.libraries+"');")
            self.ID = super().getLastID()

class BitcodeSQL(SQLDataBase):
    """
    @brief Pushes FlowMetrics, DAG, tik and tikswap information 
    """
    def __init__(self, BC, run, parent, BCDict, rtargs):
        """
        @param[in] BC       String of the BC file whose trace data will be pushed
        @param[in] run      Integer representing the UID of the RunId table entry this push belongs to
        @param[in] parent   Integer representing the UID of the Root table entry this bitcode belongs to
        @param[in] BCDict   Dictionary of file information for this bitcode file
        @param[in] rtargs   Runtime args object
        """
        self.BCD = BCDict
        self.RunID = run
        self.parentID = parent
        self.DAGID = -1
        self.FlowID = -1
        self.tikID = -1
        self.tikswapID = -1
        self.args = rtargs
        self.logger = logging.getLogger("BCSQL: "+BC)

    def push(self):
        self.pushTRC()
        self.pushKernel()

    def pushTRC(self):
        for BC in self.BCD:
            for NTV in self.BCD[BC]:
                if NTV.endswith("native"):
                    for TRC in self.BCD[BC][NTV]:
                        if TRC.startswith("TRC"):
                            # FlowMetrics data
                            FlowMetricsColumns = ["Parent","Version","Zlib","Size","TraceTime","KernelDetectTime","KernelExtractTime","LFLAG","RARG","BINARY"]
                            zlibVersion = -1
                            compressionLevel = self.args.trace_compression
                            traceSize = self.BCD[BC][NTV][TRC]["size"]
                            traceTime = self.BCD[BC][NTV][TRC][0]["time"]
                            cartTime  = self.BCD[BC][NTV][TRC]["CAR"]["time"]
                            LFLAG     = self.BCD[BC][NTV]["LFLAG"]
                            RARG      = self.BCD[BC][NTV][TRC]["RARG"].strip("'")
                            ELFName   = self.BCD[BC][NTV]["Name"]
                            FlowMetricsData = [self.parentID, "'"+str(zlibVersion)+"'", compressionLevel, traceSize, traceTime, cartTime, -1, "'"+LFLAG+"'", "'"+RARG+"'", "'"+ELFName+"'"]
                            pushCommand = "INSERT INTO FlowMetrics ("+",".join(str(x) for x in FlowMetricsColumns)+") VALUES ("+",".join(str(x) for x in FlowMetricsData)+");"
                            super().command(pushCommand)
                            self.FlowID = super().getLastID()
                            self.logger.debug("Flow ID: "+str(self.FlowID))

                            # DAG data
                            DAGdata = "''"
                            try:
                                DAGfile = open(self.BCD[BC][NTV][TRC]["DE"]["buildPath"], "r")
                            except FileNotFoundError:
                                #self.logger.warn("Could not find DAG file: "+self.BCD[BC][NTV][TRC]["DE"]["buildPath"])
                                DAGfile = None
                            if DAGfile is not None:
                                DAGdata = "'"+DAGfile.read()+"'"

                            if len(DAGdata) < 100000:
                                super().command("INSERT INTO DagData (DagData) VALUES ("+DAGdata+");")
                                self.DAGID = super().getLastID()
                                self.logger.debug("DAG ID: "+str(self.DAGID))
                            else:
                                self.logger.warning("DAG data was greater than 100,000 characters long. Skipping...")
                                self.DAGID = -1
                                
                            # tik data
                            try:
                                tikFile = open(self.BCD[BC][NTV][TRC]["tik"]["buildPath"], "rb")
                            except FileNotFoundError:
                                self.logger.warn("Could not find tik file: "+self.BCD[BC][NTV][TRC]["tik"]["buildPath"])
                                tikFile = None
                                self.tikID = -1
                            if tikFile is not None:
                                tikBin = tikFile.read()
                                if super().enabled:
                                    try:
                                        super().cnxn.execute("INSERT INTO tik (tik) VALUES (?) ", pyodbc.Binary(tikBin))
                                        IDtuple = super().command("SELECT UID from tik;", ret=True)
                                        self.tikID = IDtuple[-1][0]
                                        self.logger.debug("tik ID: "+str(self.tikID))
                                    except Exception as e:
                                        self.logger.error("Exception when pushing tik data: "+str(e))
                                        self.tikID = -1
                            # tikswap data
                            # nothing for now

    def pushKernel(self):
        """
        """
        for BC in self.BCD:
            for NTV in self.BCD[BC]:
                if NTV.endswith("native"):
                    for TRC in self.BCD[BC][NTV]:
                        if TRC.startswith("TRC"):
                            ## open per-trace files
                            # kernel file
                            try:
                                KD = json.load( open (self.BCD[BC][NTV][TRC]["CAR"]["buildPath"],"r") )
                            except FileNotFoundError:
                                self.logger.warn("Could not find kernel file: "+self.BCD[BC][NTV][TRC]["CAR"]["buildPath"])
                                KD = None
                                continue
                            # kernel hash file
                            try:
                                KHD = json.load( open( self.BCD[BC][NTV][TRC]["KH"]["buildPath"],"r" ) )
                            except:
                                self.logger.warn("Could not find kernel hash file: "+self.BCD[BC][NTV][TRC]["KH"]["buildPath"])
                                KHD = None
                            # function file
                            try:
                                FD = json.load( open( self.BCD[BC][NTV][TRC]["function"]["buildPath"],"r" ) )
                            except:
                                #self.logger.warn("Could not find function annotation file: "+self.BCD[BC][NTV][TRC]["function"]["buildPath"])
                                FD = None
                            # pig file
                            try:
                                PD = json.load( open( self.BCD[BC][NTV][TRC]["CAR"]["buildPathpigfile"],"r" ) )
                            except:
                                #self.logger.warn("Could not find pig file: "+self.BCD[BC][NTV][TRC]["CAR"]["buildPathpigfile"])
                                PD = None

                            # push per-kernel data
                            KernelColumns = ["Parent","[Index]","Binary","LFLAG","RARG","RunID","Libraries","FlowID","BowId","DagId","Hash","TikId","PigId","CpigId","Labels","EPigId","ECPigId"]
                            if isinstance(KD, dict):
                                if KD.get("Kernels", None) is not None:
                                    for index in KD["Kernels"]:
                                        parent = self.parentID
                                        ind = index
                                        binary = self.BCD[BC][NTV]["Name"]
                                        LFLAG  = self.BCD[BC][NTV]["LFLAG"]
                                        RARG   = self.BCD[BC][NTV][TRC]["RARG"]
                                        RunID  = self.RunID
                                        Libraries = Util.getKernelLibraries(FD, str(index))
                                        FlowId = self.FlowID
                                        BowId = -1
                                        DagId = self.DAGID
                                        Hash = Util.getKernelHash(KHD, str(index))
                                        TikId = self.tikID
                                        pigIDs = self.pushPigData(KD, str(index))
                                        PigId = pigIDs[0]
                                        CpigId = pigIDs[1]
                                        Labels = Util.getKernelLabels(KD, str(index))                                            
                                        EPigId = pigIDs[2]
                                        ECPigId = pigIDs[3]

                                        # figure out which values will be made NULL in the push
                                        if len(LFLAG) == 0:
                                            LFLAG = None
                                        if len(RARG) == 0:
                                            RARG = None
                                        if len(Libraries) == 0:
                                            Libraries = None
                                        if len(Labels) == 0:
                                            Labels = None
                                        # to keep the parsing uniform, EPig and ECpig will never be made null
                                        
                                        # construct columns and data that will be pushed
                                        finalColumns = ["Parent","[Index]","Binary"]
                                        finalData = [parent, ind, "'"+binary+"'"]
                                        if LFLAG is not None:
                                            finalColumns += ["LFLAG"]
                                            finalData += ["'"+LFLAG+"'"]
                                        if RARG is not None:
                                            finalColumns += ["RARG"]
                                            finalData += ["'"+RARG+"'"]
                                        finalColumns += ["RunID"]
                                        finalData    += [RunID]
                                        if Libraries is not None:
                                            finalColumns += ["Libraries"]
                                            finalData    += ["'"+Libraries+"'"]
                                        finalColumns += ["FlowID","BowId","DagId","Hash","TikId","PigId","CpigId"]
                                        finalData    += [FlowId, BowId, DagId, Hash, TikId, PigId, CpigId]
                                        if Labels is not None:
                                            finalColumns += ["Labels"]
                                            finalData    += ["'"+";".join(x for x in Labels)+"'"]
                                        finalColumns += ["EPigId","ECPigId"]
                                        finalData    += [EPigId, ECPigId]
                                        
                                        super().command("INSERT INTO Kernels ("+",".join(x for x in finalColumns)+") VALUES ("+",".join(str(x) for x in finalData)+");")
                                        kernelID = super().getLastID()
                                        self.logger.debug("Kernel ID: "+str(kernelID))

                                        # finally, BBH table entry
                                        BBHList = Util.getBBHList(KHD, str(index))
                                        if BBHList is not None:
                                            super().command("INSERT INTO BasicBlockHash (Parent,HashList) VALUES ("+str(kernelID)+",'"+",".join(str(x) for x in BBHList)+"');")

                                else:
                                    self.logger.warn("Kernel file did not have kernels in it.")
                            else:
                                self.logger.warn("Kernel file was not a dictionary.")

    def pushPigData(self, KD, index):
        """
        @brief      Pushes Performance Intrinsics Data: static (pig), dynamic(cpig), cross-product static(epig), cross-product dynamic(ecpig)
        @param[in]  PD     Dictionary of kernel data
        @param[in]  index  Index (string) of the kernel ID
        @retval     IDs    List of 4 push IDs [pigID, cpigID, epigID, ecpigID]
        """
        IDs = [-1,-1,-1,-1]
        # read in file
        if KD.get("Kernels") is None:
            return IDs
        if KD["Kernels"].get(index) is None:
            return IDs
        if KD["Kernels"][index].get("Performance Intrinsics") is None:
            return IDs
        PD = KD["Kernels"][index]["Performance Intrinsics"]
        
        # dictionaries hold all columns of each respective SQL table
        pigD = dict.fromkeys(["typeVoid", "typeFloat", "typeInt", "typeArray", "typeVector", "typePointer", "instructionCount", "addCount",
                                "subCount", "mulCount", "udivCount", "sdivCount", "uremCount", "sremCount", "shlCount", "lshrCount", "ashrCount", "andCount", "orCount",
                                "xorCount", "faddCount", "fsubCount", "fmulCount", "fdivCount", "fremCount", "extractelementCount", "insertelementCount",
                                "shufflevectorCount", "extractvalueCount", "insertvalueCount", "allocaCount", "loadCount", "storeCount", "fenceCount", "cmpxchgCount",
                                "atomicrmwCount", "getelementptrCount", "truncCount", "zextCount", "sextCount", "fptruncCount", "fpextCount", "fptouiCount", "fptosiCount",
                                "uitofpCount", "sitofpCount", "ptrtointCount", "inttoptrCount", "bitcastCount", "addrspacecastCount", "icmpCount", "fcmpCount", "phiCount",
                                "selectCount", "freezeCount", "callCount", "va_argCount", "landingpadCount", "catchpadCount", "cleanuppadCount", "retCount", "brCount",
                                "switchCount", "indirectbrCount", "invokeCount", "callbrCount", "resumeCount", "catchswitchCount", "cleanupretCount", "unreachableCount",
                                "fnegCount"], 0)
        cpigD = pigD

        # pig push
        if PD.get("Pig", None) is not None:
            push = True
            for inst in PD["Pig"].keys():
                found = False
                for column in pigD.keys():
                    if inst == column:
                        found = True
                        pigD[column] = PD["Pig"][inst]
                if not found:
                    self.logger.critical("Found this field: {}, in the pig data dictionary that did not exist in the pushing dictionary. Exiting and please fix the bug.".format(inst))
                    push = False
            if push:
                super().command("INSERT INTO pig ("+",".join(x for x in list(pigD.keys()))+") VALUES ("+",".join(str(x) for x in list(pigD.values()))+");")
                IDs[0] = super().getLastID()

        # cpig push
        if PD.get("CPig", None) is not None:
            push = True
            for inst in PD["CPig"].keys():
                found = False
                for column in cpigD.keys():
                    if inst == column:
                        found = True
                        cpigD[column] = PD["CPig"][inst]
                if not found:
                    self.logger.critical("Found this field: {}, in the cpig data dictionary that did not exist in the pushing dictionary. Exiting and please fix the bug.".format(inst))
                    push = False
            if push:
                super().command("INSERT INTO cpig ("+",".join(x for x in list(cpigD.keys()))+") VALUES ("+",".join(str(x) for x in list(cpigD.values()))+");")
                IDs[1] = super().getLastID()

        epigD = dict.fromkeys(["instructionCount", "fnegtypeInt", "fnegtypeFloat", "fnegtypeVoid", "fnegtypeArray", "fnegtypeVector", "fnegtypePointer", "addtypeInt",
                                "addtypeFloat", "addtypeVoid", "addtypeArray", "addtypeVector", "addtypePointer", "faddtypeInt", "faddtypeFloat", "faddtypeVoid", "faddtypeArray",
                                "faddtypeVector", "faddtypePointer", "subtypeInt", "subtypeFloat", "subtypeVoid", "subtypeArray", "subtypeVector", "subtypePointer", "fsubtypeInt",
                                "fsubtypeFloat", "fsubtypeVoid", "fsubtypeArray", "fsubtypeVector", "fsubtypePointer", "multypeInt", "multypeFloat", "multypeVoid", "multypeArray",
                                "multypeVector", "multypePointer", "fmultypeInt", "fmultypeFloat", "fmultypeVoid", "fmultypeArray", "fmultypeVector", "fmultypePointer", "udivtypeInt",
                                "udivtypeFloat", "udivtypeVoid", "udivtypeArray", "udivtypeVector", "udivtypePointer", "sdivtypeInt", "sdivtypeFloat", "sdivtypeVoid", "sdivtypeArray",
                                "sdivtypeVector", "sdivtypePointer", "fdivtypeInt", "fdivtypeFloat", "fdivtypeVoid", "fdivtypeArray", "fdivtypeVector", "fdivtypePointer", "uremtypeInt",
                                "uremtypeFloat", "uremtypeVoid", "uremtypeArray", "uremtypeVector", "uremtypePointer", "sremtypeInt", "sremtypeFloat", "sremtypeVoid", "sremtypeArray",
                                "sremtypeVector", "sremtypePointer", "fremtypeInt", "fremtypeFloat", "fremtypeVoid", "fremtypeArray", "fremtypeVector", "fremtypePointer", "shltypeInt",
                                "shltypeFloat", "shltypeVoid", "shltypeArray", "shltypeVector", "shltypePointer", "lshrtypeInt", "lshrtypeFloat", "lshrtypeVoid", "lshrtypeArray", "lshrtypeVector",
                                "lshrtypePointer", "ashrtypeInt", "ashrtypeFloat", "ashrtypeVoid", "ashrtypeArray", "ashrtypeVector", "ashrtypePointer", "andtypeInt", "andtypeFloat", "andtypeVoid",
                                "andtypeArray", "andtypeVector", "andtypePointer", "ortypeInt", "ortypeFloat", "ortypeVoid", "ortypeArray", "ortypeVector", "ortypePointer", "xortypeInt", "xortypeFloat",
                                "xortypeVoid", "xortypeArray", "xortypeVector", "xortypePointer", "insertelementtypeInt", "insertelementtypeFloat", "insertelementtypeVoid", "insertelementtypeArray",
                                "insertelementtypeVector", "insertelementtypePointer", "shufflevectortypeInt", "shufflevectortypeFloat", "shufflevectortypeVoid", "shufflevectortypeArray", "shufflevectortypeVector",
                                "shufflevectortypePointer", "storetypeInt", "storetypeFloat", "storetypeVoid", "storetypeArray", "storetypeVector", "storetypePointer", "fencetypeInt", "fencetypeFloat", "fencetypeVoid",
                                "fencetypeArray", "fencetypeVector", "fencetypePointer", "cmpxchgtypeInt", "cmpxchgtypeFloat", "cmpxchgtypeVoid", "cmpxchgtypeArray", "cmpxchgtypeVector", "cmpxchgtypePointer",
                                "allocatypeInt", "allocatypeFloat", "allocatypeVoid", "allocatypeArray", "allocatypeVector", "allocatypePointer", "atomicrmwtypeInt", "atomicrmwtypeFloat", "atomicrmwtypeVoid",
                                "atomicrmwtypeArray", "atomicrmwtypeVector", "atomicrmwtypePointer", "getelementptrtypeInt", "getelementptrtypeFloat", "getelementptrtypeVoid", "getelementptrtypeArray",
                                "getelementptrtypeVector", "getelementptrtypePointer", "trunctypeInt", "trunctypeFloat", "trunctypeVoid", "trunctypeArray", "trunctypeVector", "trunctypePointer", "zexttypeInt",
                                "zexttypeFloat", "zexttypeVoid", "zexttypeArray", "zexttypeVector", "zexttypePointer", "sexttypeInt", "sexttypeFloat", "sexttypeVoid", "sexttypeArray", "sexttypeVector",
                                "sexttypePointer", "fptrunctypeInt", "fptrunctypeFloat", "fptrunctypeVoid", "fptrunctypeArray", "fptrunctypeVector", "fptrunctypePointer", "fpexttypeInt", "fpexttypeFloat",
                                "fpexttypeVoid", "fpexttypeArray", "fpexttypeVector", "fpexttypePointer", "fptouitypeInt", "fptouitypeFloat", "fptouitypeVoid", "fptouitypeArray", "fptouitypeVector",
                                "fptouitypePointer", "fptositypeInt", "fptositypeFloat", "fptositypeVoid", "fptositypeArray", "fptositypeVector", "fptositypePointer", "uitofptypeInt", "uitofptypeFloat",
                                "uitofptypeVoid", "uitofptypeArray", "uitofptypeVector", "uitofptypePointer", "sitofptypeInt", "sitofptypeFloat", "sitofptypeVoid", "sitofptypeArray", "sitofptypeVector",
                                "sitofptypePointer", "ptrtointtypeInt", "ptrtointtypeFloat", "ptrtointtypeVoid", "ptrtointtypeArray", "ptrtointtypeVector", "ptrtointtypePointer", "inttoptrtypeInt", "inttoptrtypeFloat",
                                "inttoptrtypeVoid", "inttoptrtypeArray", "inttoptrtypeVector", "inttoptrtypePointer", "bitcasttypeInt", "bitcasttypeFloat", "bitcasttypeVoid", "bitcasttypeArray", "bitcasttypeVector",
                                "bitcasttypePointer", "addrspacecasttypeInt", "addrspacecasttypeFloat", "addrspacecasttypeVoid", "addrspacecasttypeArray", "addrspacecasttypeVector", "addrspacecasttypePointer",
                                "icmptypeInt", "icmptypeFloat", "icmptypeVoid", "icmptypeArray", "icmptypeVector", "icmptypePointer", "fcmptypeInt", "fcmptypeFloat", "fcmptypeVoid", "fcmptypeArray", "fcmptypeVector",
                                "fcmptypePointer", "rettypeInt", "rettypeFloat", "rettypeVoid", "rettypeArray", "rettypeVector", "rettypePointer", "brtypeInt", "brtypeFloat", "brtypeVoid", "brtypeArray",
                                "brtypeVector", "brtypePointer", "indirectbrtypeInt", "indirectbrtypeFloat", "indirectbrtypeVoid", "indirectbrtypeArray", "indirectbrtypeVector", "indirectbrtypePointer", "switchtypeInt",
                                "switchtypeFloat", "switchtypeVoid", "switchtypeArray", "switchtypeVector", "switchtypePointer", "invoketypeInt", "invoketypeFloat", "invoketypeVoid", "invoketypeArray", "invoketypeVector",
                                "invoketypePointer", "callbrtypeInt", "callbrtypeFloat", "callbrtypeVoid", "callbrtypeArray", "callbrtypeVector", "callbrtypePointer", "resumetypeInt", "resumetypeFloat", "resumetypeVoid",
                                "resumetypeArray", "resumetypeVector", "resumetypePointer", "catchrettypeInt", "catchrettypeFloat", "catchrettypeVoid", "catchrettypeArray", "catchrettypeVector",
                                "catchrettypePointer", "cleanuprettypeInt", "cleanuprettypeFloat", "cleanuprettypeVoid", "cleanuprettypeArray", "cleanuprettypeVector", "cleanuprettypePointer",
                                "unreachabletypeInt", "unreachabletypeFloat", "unreachabletypeVoid", "unreachabletypeArray", "unreachabletypeVector", "unreachabletypePointer", "extractelementtypeInt",
                                "extractelementtypeFloat", "extractelementtypeVoid", "extractelementtypeArray", "extractelementtypeVector", "extractelementtypePointer", "extractvaluetypeInt",
                                "extractvaluetypeFloat", "extractvaluetypeVoid", "extractvaluetypeArray", "extractvaluetypeVector", "extractvaluetypePointer", "insertvaluetypeInt", "insertvaluetypeFloat",
                                "insertvaluetypeVoid", "insertvaluetypeArray", "insertvaluetypeVector", "insertvaluetypePointer", "selecttypeInt", "selecttypeFloat", "selecttypeVoid", "selecttypeArray",
                                "selecttypeVector", "selecttypePointer", "loadtypeInt", "loadtypeFloat", "loadtypeVoid", "loadtypeArray", "loadtypeVector", "loadtypePointer", "phitypeInt", "phitypeFloat",
                                "phitypeVoid", "phitypeArray", "phitypeVector", "phitypePointer", "freezetypeInt", "freezetypeFloat", "freezetypeVoid", "freezetypeArray", "freezetypeVector", "freezetypePointer",
                                "calltypeInt", "calltypeFloat", "calltypeVoid", "calltypeArray", "calltypeVector", "calltypePointer", "va_argtypeInt", "va_argtypeFloat", "va_argtypeVoid", "va_argtypeArray",
                                "va_argtypeVector", "va_argtypePointer", "landingpadtypeInt", "landingpadtypeFloat", "landingpadtypeVoid", "landingpadtypeArray", "landingpadtypeVector", "landingpadtypePointer",
                                "catchpadtypeInt", "catchpadtypeFloat", "catchpadtypeVoid", "catchpadtypeArray", "catchpadtypeVector", "catchpadtypePointer", "cleanuppadtypeInt", "cleanuppadtypeFloat",
                                "cleanuppadtypeVoid", "cleanuppadtypeArray", "cleanuppadtypeVector", "cleanuppadtypePointer", "catchswitchtypeVector", "catchswitchtypePointer","catchswitchtypeInt","catchswitchtypeFloat",
                                "catchswitchtypeVoid","catchswitchtypeArray"], 0)
        ecpigD = epigD

        # epig push
        if PD.get("EPig", None) is not None:
            push = True
            for inst in PD["EPig"].keys():
                found = False
                for column in epigD.keys():
                    if inst == column:
                        found = True
                        epigD[column] = PD["EPig"][inst]
                if not found:
                    self.logger.critical("Found this field: {}, in the EPig data dictionary that did not exist in the pushing dictionary. Exiting and please fix the bug.".format(inst))
                    push = False
            if push:
                super().command("INSERT INTO epig ("+",".join(x for x in list(epigD.keys()))+") VALUES ("+",".join(str(x) for x in list(epigD.values()))+");")
                IDs[2] = super().getLastID()

        # ecpig push
        if PD.get("ECPig", None) is not None:
            push = True
            for inst in PD["ECPig"].keys():
                found = False
                for column in ecpigD.keys():
                    if inst == column:
                        found = True
                        ecpigD[column] = PD["ECPig"][inst]
                if not found:
                    self.logger.critical("Found this field: {}, in the ECPig data dictionary that did not exist in the pushing dictionary. Exiting and please fix the bug.".format(inst))
                    push = False
            if push:
                super().command("INSERT INTO ecpig ("+",".join(x for x in list(ecpigD.keys()))+") VALUES ("+",".join(str(x) for x in list(ecpigD.values()))+");")
                IDs[3] = super().getLastID()

        return IDs