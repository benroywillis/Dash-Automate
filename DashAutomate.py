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
        # thread one generates the project directory tree, builds each valid project, and starts each respective project's bitcode once the project is done
        self.thread1 = threading.Thread(target=self.ThreadOne)
        # flags indicating activity for each thread
        self.thread1on = False
        self.thread2on = False
        # thread 2 monitors each building bitcode and pushes their contents using SQL when each bitcode is done
        self.thread2 = threading.Thread(target=self.ThreadTwo)
        # lock on each thread to protect the buildingBitcodes set
        self.threadlock = threading.Condition()
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
        self.FULLREPORT["Full Report"]["Tik Errors"] = dict()
        self.FULLREPORT["Full Report"]["TikSwap Errors"] = dict()
        self.FULLREPORT["Full Report"]["Bad Projects"] = list()
        self.FULLREPORT["Full Report"]["Bitcodes with Errors"] = dict()

    def givePermission(self):
        """
        @brief Used by thread 1 to give thread 2 permission to iterate through buildingBitcodes
        """
        if self.thread2on:
            self.log.debug("Giving permission to thread 2")
            try:
                self.threadlock.wait()
            except Exception as e:
                self.log.critical("Exception when waiting: "+str(e))

    def waitForPermission(self):
        """
        @brief Used by thread 2 to wait for permission from thread 1 to iterate through buildingBitcodes
        """
        if self.thread1on:
            self.log.debug("waiting for permission")
            return self.threadlock.acquire(blocking=True, timeout=1.0)
        else:
            return True

    def release(self):
        """
        @brief Used by thread 2 to notify thread 1 that it is done with buildingBitcodes
        """
        if self.thread1on:
            try:
                self.threadlock.notify()
                self.threadlock.release()
            except Exception as e:
                logging.critical("Failed notifying waiting thread: "+str(e))
                Util.EXIT_TOOL()

    def initSQL(self):
        """
        @brief Initializes SQLDatabase class connection
        """
        # make a connection to the DB
        SQL.SQLDataBase.__enabled__(self.args.commit)
        SQL.SQLDataBase.connect()
        # now push the RunID
        if self.args.run_id == "0":
            self.DASQL.pushRunID()
            self.log.debug("RunID: "+str(self.DASQL.ID))
            self.reportFile = os.getcwd()+"/FULLREPORT_"+str(self.DASQL.ID)+"_"+self.args.build+".json"

        else:
            self.DASQL.ID = self.args.run_id
            self.reportFile = os.getcwd()+"/FULLREPORT_"+str(self.DASQL.ID)+"_"+self.args.build+".json"

    def run(self):
        """
        @brief Runs the Dash-Automate flow
        """
        # first, initialize DASQL
        self.initSQL()
        self.thread1.start()
        self.thread2.start()

    def addProjectReport(self, project):
        """
        @brief Adds input project report to global report file
        """
        if project.errors:
            self.FULLREPORT["Full Report"]["Bad Projects"].append(project.projectPath)

        with open(self.reportFile, "w+") as report:
            json.dump(self.FULLREPORT, report, indent=4)

    def addBitcodeReport(self, bitcode):
        """
        @brief Adds bitcode report to global report file
        """
        # relative path to the project directory, not including the build folder name
        relPath = Util.getPathDiff(self.rootPath, bitcode.projectPath, build=False)
        if self.FULLREPORT.get( relPath, None ) is None:
            self.FULLREPORT[relPath] = dict()
        self.FULLREPORT[relPath][bitcode.BC] = bitcode.report()

        # sum FullReport totals
        self.FULLREPORT["Full Report"]["Traces"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Traces"]
        self.FULLREPORT["Full Report"]["Tik Traces"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Traces"]
        self.FULLREPORT["Full Report"]["Tik Swaps"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Swaps"]
        self.FULLREPORT["Full Report"]["Tik Compilations"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Compilations"]
        self.FULLREPORT["Full Report"]["Tik Successes"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Successes"]
        self.FULLREPORT["Full Report"]["Cartographer Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Kernels"]
        self.FULLREPORT["Full Report"]["Tik Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Kernels"]
        self.FULLREPORT["Full Report"]["TikSwap Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Kernels"]
        self.FULLREPORT["Full Report"]["Tik Compilation Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Compilation Kernels"]
        self.FULLREPORT["Full Report"]["Tik Success Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Success Kernels"]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"]:
            if self.FULLREPORT["Full Report"]["Tik Errors"].get(key) is None:
                self.FULLREPORT["Full Report"]["Tik Errors"][key] = 0
            self.FULLREPORT["Full Report"]["Tik Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"][key]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"]:
            if self.FULLREPORT["Full Report"]["TikSwap Errors"].get(key) is None:
                self.FULLREPORT["Full Report"]["TikSwap Errors"][key] = 0
            self.FULLREPORT["Full Report"]["TikSwap Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"][key]

        # add errors
        if len(self.FULLREPORT[relPath][bitcode.BC]["Errors"]) > 0:
            self.FULLREPORT["Full Report"]["Bitcodes with Errors"][bitcode.BC] = self.FULLREPORT[relPath][bitcode.BC]["Errors"]

        with open(self.reportFile, "w+") as report:
            json.dump(self.FULLREPORT, report, indent=4)
        
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
                #absPath = self.args.project_prefix+path
                projectPaths = Util.recurseThroughSubDs(path, self.args, projectPaths)
        # local directory
        if compileD.get("Build", None) is not None:
            projectPaths.add(self.args.project_prefix)

        for path in projectPaths:
            rawpath = path.split("/")
            while "" in rawpath:
                rawpath.remove("")
            refinedPath = "/"+"/".join(x for x in rawpath)
            self.projects.add( pj( self.rootPath, refinedPath, self.args.build, self.args.input_file) )

    def ThreadOne(self):
        """
        @brief  Walks the directory tree, finds all projects with input JSON name and builds the makefiles.
        @param[in]  args        Runtime args to the DA tool
        @retval     projects    List of Project objects currently building. Can be either process IDs in bash or SLURM IDs. Note: The bash process IDs are the IDs of the shells launched by subprocess, not the actual job itself.
        """
        self.thread1on = True
        self.threadlock.acquire(blocking=True)
        self.getProjects()

        # for each project, run its build command
        returnProjects = []
        for proj in self.projects:
            if proj.Valid:
                proj.run()
                self.buildingProjects.add(proj)
            else:
                self.log.error("Project is not valid: "+proj.projectPath)

        doneProjects = set()
        while len(self.buildingProjects) > 0:
            self.givePermission()
            for proj in self.buildingProjects:
                if proj.done():
                    if not proj.Valid:
                        self.log.error("Project is not valid: "+proj.projectPath)
                        self.addProjectReport(proj)
                    doneProjects.add(proj)
                    for BC in proj.Bitcodes:
                        newBC = Bc(self.args.project_prefix, proj.projectPath, BC, proj.Bitcodes[BC]["LFLAGS"], proj.Bitcodes[BC]["RARGS"], self.DASQL.ID, proj.ID, self.args)
                        if not newBC.errors:
                            newBC.run()
                            self.buildingBitcodes.add(newBC)
                        else:
                            self.addBitcodeReport(newBC)
                    self.log.info("Project "+proj.projectPath+" is done.")
                    self.addProjectReport(proj)
                    if proj.PSQL.newEntry:
                        self.DASQL.commit()
            self.buildingProjects -= doneProjects
        self.log.info("Projects complete.")
        self.thread1on = False

    def ThreadTwo(self):
        """
        @brief Facilitates the creation of Bitcode objects and their buildflows.
        @param[in] args         Dictionary of arguments passed to the tool at runtime
        @param[in] projects     Project objects of the buildflows already in progress. Can be either SLURM IDs or bash processes (if bash processes, these IDs are not the actual job IDs, they are the shell IDs spawned by subprocess)
        """
        self.thread2on = True
        doneBitcodes = set()
        while len(self.buildingBitcodes) > 0 or self.thread1on:
            if not self.waitForPermission():
                continue
            for bit in self.buildingBitcodes:
                if bit.done():
                    self.log.info("Bitcode "+bit.buildPath+bit.BC+" is done.")
                    self.addBitcodeReport(bit)
                    doneBitcodes.add(bit)
                    self.DASQL.commit()
            self.buildingBitcodes -= doneBitcodes
            self.release()
        self.log.info("Bitcodes done.")
        self.thread2on = False

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