from BitCode import BitCode as Bc
from Project import Project as pj
import Command
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
        # tree holds all existing traces in the specified previous runID
        self.existingMap = None
        # set to hold project paths that have already had a project built
        self.builtProjects = set()
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
        self.FULLREPORT["Full Report"]["Average Kernel Size (Nodes)"] = 0
        self.FULLREPORT["Full Report"]["Average Kernel Size (Blocks)"] = 0
        self.FULLREPORT["Full Report"]["Cartographer Errors"] = dict()
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
        params = Util.getDBParameters(self.args.database_file)
        SQL.SQLDataBase.__username__(params[0])
        SQL.SQLDataBase.__password__(params[1])
        SQL.SQLDataBase.__database__(params[2])
        SQL.SQLDataBase.__server__(params[3])
        
        # make a connection to the DB
        rootHead = [x for x in self.rootPath.split("/") if x != ""][-1]
        if (self.args.commit) and (rootHead != "Dash-Corpus"):
            self.log.error("In order to commit changes to the database, this tool must be called in the Dash-Corpus directory.")
            self.args.commit = False
            return
        SQL.SQLDataBase.__enabled__(self.args.commit or self.args.only_new or self.args.nightly_build)
        SQL.SQLDataBase.connect()

        if self.args.nightly_build or self.args.only_new:
            self.existingMap = self.DASQL.ExistingProjects()
        # now push the RunID
        if self.args.run_id == "0" and self.args.commit:
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
        copyReport = self.FULLREPORT
        with open(self.reportFile, "w+") as report:
            json.dump(copyReport, report, indent=4)

    def addBitcodeReport(self, bitcode):
        """
        @brief Adds bitcode report to global report file
        """
        self.log.debug("Adding bitcode report")
        # relative path to the project directory, not including the build folder name
        relPath = Util.getPathDiff(self.rootPath, bitcode.projectPath, build=False)
        if self.FULLREPORT.get( relPath, None ) is None:
            self.FULLREPORT[relPath] = dict()
            self.FULLREPORT[relPath]["Report"] = dict()
            self.FULLREPORT[relPath]["Report"]["Traces"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Traces"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Swaps"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Compilations"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Successes"] = 0
            self.FULLREPORT[relPath]["Report"]["Cartographer Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["TikSwap Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Compilation Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Success Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Success Kernels"] = 0
            self.FULLREPORT[relPath]["Report"]["Average Kernel Size (Nodes)"] = 0            
            self.FULLREPORT[relPath]["Report"]["Average Kernel Size (Blocks)"] = 0            
            self.FULLREPORT[relPath]["Report"]["Cartographer Errors"] = dict()
            self.FULLREPORT[relPath]["Report"]["Tik Errors"] = dict()
            self.FULLREPORT[relPath]["Report"]["TikSwap Errors"] = dict()
        # sum directory totals
        self.FULLREPORT[relPath][bitcode.BC] = bitcode.report()
        self.FULLREPORT[relPath]["Report"]["Traces"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Traces"]
        self.FULLREPORT[relPath]["Report"]["Tik Traces"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Traces"]
        self.FULLREPORT[relPath]["Report"]["Tik Swaps"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Swaps"]
        self.FULLREPORT[relPath]["Report"]["Tik Compilations"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Compilations"]
        self.FULLREPORT[relPath]["Report"]["Tik Successes"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Successes"]
        self.FULLREPORT[relPath]["Report"]["Cartographer Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Kernels"]
        self.FULLREPORT[relPath]["Report"]["Tik Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Kernels"]
        self.FULLREPORT[relPath]["Report"]["TikSwap Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Kernels"]
        self.FULLREPORT[relPath]["Report"]["Tik Compilation Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Compilation Kernels"]
        self.FULLREPORT[relPath]["Report"]["Tik Success Kernels"] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Success Kernels"]
        self.log.debug("Just summed directory totals")
        nodeSum = 0.0
        blockSum = 0.0
        # only count the traces that registered kernels, otherwise cartographer failures and other things taint the averages
        nonzeroTraces = 0
        for bitcodeFile in self.FULLREPORT[relPath]:
            if bitcodeFile == "Report":
                continue
            if self.FULLREPORT[relPath][bitcodeFile]["Total"]["Average Kernel Size (Nodes)"] > 0:
                nonzeroTraces += 1
            nodeSum += self.FULLREPORT[relPath][bitcodeFile]["Total"]["Average Kernel Size (Nodes)"]
            blockSum += self.FULLREPORT[relPath][bitcodeFile]["Total"]["Average Kernel Size (Blocks)"]
        self.FULLREPORT[relPath]["Report"]["Average Kernel Size (Nodes)"] = float( float(nodeSum) / float(nonzeroTraces) ) if nonzeroTraces > 0 else 0
        self.FULLREPORT[relPath]["Report"]["Average Kernel Size (Blocks)"] = float( float(blockSum) / float(nonzeroTraces) ) if nonzeroTraces > 0 else 0
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Errors"]:
            if self.FULLREPORT[relPath]["Report"]["Cartographer Errors"].get(key) is None:
                self.FULLREPORT[relPath]["Report"]["Cartographer Errors"][key] = 0
            self.FULLREPORT[relPath]["Report"]["Cartographer Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Errors"][key]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"]:
            if self.FULLREPORT[relPath]["Report"]["Tik Errors"].get(key) is None:
                self.FULLREPORT[relPath]["Report"]["Tik Errors"][key] = 0
            self.FULLREPORT[relPath]["Report"]["Tik Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"][key]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"]:
            if self.FULLREPORT[relPath]["Report"]["TikSwap Errors"].get(key) is None:
                self.FULLREPORT[relPath]["Report"]["TikSwap Errors"][key] = 0
            self.FULLREPORT[relPath]["Report"]["TikSwap Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"][key]
        self.log.debug("Just summed average kernel sizes")

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
        nodeSum = 0.0
        blockSum = 0.0
        nonzeroProjects = 0
        for path in self.FULLREPORT:
            if self.FULLREPORT[path].get("Report") is not None:
                if self.FULLREPORT[path]["Report"]["Cartographer Kernels"] > 0:
                    nonzeroProjects += 1
                nodeSum  += self.FULLREPORT[path]["Report"]["Average Kernel Size (Nodes)"]
                blockSum += self.FULLREPORT[path]["Report"]["Average Kernel Size (Blocks)"]
        self.FULLREPORT["Full Report"]["Average Kernel Size (Nodes)"] = float( float(nodeSum) / float(nonzeroProjects) ) if nonzeroProjects > 0 else 0
        self.FULLREPORT["Full Report"]["Average Kernel Size (Blocks)"] = float( float(blockSum) / float(nonzeroProjects) ) if nonzeroProjects > 0 else 0
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Errors"]:
            if self.FULLREPORT["Full Report"]["Cartographer Errors"].get(key) is None:
                self.FULLREPORT["Full Report"]["Cartographer Errors"][key] = 0
            self.FULLREPORT["Full Report"]["Cartographer Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Cartographer Errors"][key]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"]:
            if self.FULLREPORT["Full Report"]["Tik Errors"].get(key) is None:
                self.FULLREPORT["Full Report"]["Tik Errors"][key] = 0
            self.FULLREPORT["Full Report"]["Tik Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["Tik Errors"][key]
        for key in self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"]:
            if self.FULLREPORT["Full Report"]["TikSwap Errors"].get(key) is None:
                self.FULLREPORT["Full Report"]["TikSwap Errors"][key] = 0
            self.FULLREPORT["Full Report"]["TikSwap Errors"][key] += self.FULLREPORT[relPath][bitcode.BC]["Total"]["TikSwap Errors"][key]
        self.log.debug("Just calculated FullReport totals")

        # add errors
        if len(self.FULLREPORT[relPath][bitcode.BC]["Errors"]) > 0:
            self.FULLREPORT["Full Report"]["Bitcodes with Errors"][bitcode.BC] = self.FULLREPORT[relPath][bitcode.BC]["Errors"]
        self.log.debug("Just completed errors")

        reportCopy = self.FULLREPORT
        with open(self.reportFile, "w+") as report:
            json.dump(reportCopy, report, indent=4)
        self.log.debug("Done!")
        
    def toBuild(self, proj):
        """
        @brief Decides what can be built from the incoming project
        """
        # process project path to see if it is eligible for pushing
        if self.args.commit:
            if "Dash-Corpus" not in proj.projectPath:
                self.log.warn("Only projects within Dash-Corpus can be committed to the database. Skipping project "+proj.projectPath)
                return []
        # if this is not supposed to be a special build, just return the entire project
        if not self.args.nightly_build and not self.args.only_new:
            returnList = []
            for BC in proj.Bitcodes:
                returnList.append( (BC, proj.Bitcodes[BC]["LFLAGS"], proj.Bitcodes[BC]["RARGS"]) )
            return returnList

        relPath = Util.getPathDiff(self.rootPath, proj.projectPath)
        ## run from the highest density project from each makefile
        # this project's traces will be evaluated for the one with highest kernel/time density. That project will be chosen
        if self.args.nightly_build:
            # nightly builds are supposed to test changes to the TraceAtlas toolchain in a way that verifies the operation of its programs beyond its own test suite
            # It builds at least 1 project from each Makefile, ideally the one that has the highest kernels / (CAR time + trace time) density. 
            # It should not take more than 6h to build and push all of its projects to the database
            # Additionally it tries to build the minimum set of projects that will both build every kernel hash and optimize kernel density
            nightlyBuild = []
            minimumBitcode = ( None, (None,None), 0 )
            if len( self.builtProjects & {proj.projectPath} ) == 0:
                # have to find highest-density trace
                if self.existingMap.get(relPath, None) is not None:
                    for BC in proj.Bitcodes:
                        existingBCname = BC.split(".")[0]
                        if self.existingMap[relPath].get(existingBCname, None) is not None:
                            for NTV in self.existingMap[relPath][existingBCname]:
                                for TRC in self.existingMap[relPath][existingBCname][NTV]:
                                    TRCentry = self.existingMap[relPath][existingBCname][NTV][TRC]
                                    density = TRCentry["Kernels"] / TRCentry["Time"] if TRCentry["Time"] > 0 else 0 
                                    if density > minimumBitcode[2]:
                                        minimumBitcode = ( BC, self.existingMap[relPath][existingBCname][NTV][TRC]["Parameters"], density)
                self.builtProjects.add(relPath)
            if minimumBitcode[0] == None:
                # nothing to be done here, send back nothing
                self.log.debug("Returning no bitcodes because none were found in the database.")
                return nightlyBuild
            else:
                # find the minimum bitcode configuration and build that
                for BC in proj.Bitcodes:
                    if BC == minimumBitcode[0]:
                        for LFLAG in proj.Bitcodes[BC]["LFLAGS"]:
                            for RARG in proj.Bitcodes[BC]["RARGS"]:
                                if (LFLAG,RARG) == minimumBitcode[1]:
                                    self.log.debug("Returning bitcode "+minimumBitcode[0]+" with parameters "+minimumBitcode[1][0]+" and "+minimumBitcode[1][1]+".")
                                    return [(BC, [LFLAG], [RARG])]
                return []

        elif self.args.only_new:
        # build dictionary of projects in the database
            onlyNew = []
            existingBCs = dict()
            if self.existingMap.get(relPath, None) is not None:
                for BC in proj.Bitcodes:
                    existingBCname = BC.split(".")[0]
                    # compare each project bitcode to existing bitcode combos in the database
                    if self.existingMap[relPath].get(existingBCname, None) is not None:
                        for NTV in self.existingMap[relPath][existingBCname]:
                            for TRC in self.existingMap[relPath][existingBCname][NTV]:
                                if existingBCs.get(BC, None) is None:
                                    existingBCs[BC] = dict()
                                    existingBCs[BC]["combos"] = set()
                                existingBCs[BC]["combos"].add( (self.existingMap[relPath][existingBCname][NTV][TRC]["Parameters"][0], self.existingMap[relPath][existingBCname][NTV][TRC]["Parameters"][1]) )
                    else:
                        self.log.debug("Bitcode "+existingBCname+" not found in database")
                        # this bitcode is not in the database at all
                        onlyNew.append( (BC, proj.Bitcodes[BC]["LFLAGS"], proj.Bitcodes[BC]["RARGS"]) )
                        break
            else:
                self.log.debug("Path "+relPath+" not found in database")
                for BC in proj.Bitcodes:
                    onlyNew.append( (BC, proj.Bitcodes[BC]["LFLAGS"], proj.Bitcodes[BC]["RARGS"]) )
                return onlyNew

            ## only new projects
            # now loop through all bitcodes that were found in the database and compare their traces to what this project has
            # a project trace matches a trace already in the database if the path, BC and (LFLAG,RARG) all match 
            for BC in existingBCs:
                unfoundCombos = set()
                # check LFLAG, RARG against incoming project for existence
                for LFLAG in proj.Bitcodes[BC]["LFLAGS"]:
                    for RARG in proj.Bitcodes[BC]["RARGS"]:
                        combo = (LFLAG,RARG)
                        found = False
                        for eCombo in existingBCs[BC]["combos"]:
                            if combo == eCombo:
                                found = True
                        if not found:
                            unfoundCombos.add( combo )
                # now turn unique combos into lists that can be permuted
                LF = set()
                RR = set()
                for comb in unfoundCombos:
                    LF.add(comb[0])
                    RR.add(comb[1])
                if len(unfoundCombos) > 0:
                    if len(LF)*len(RR) == len(unfoundCombos):
                        onlyNew.append( (BC, list(LF), list(RR)) )
                    else:
                        # we have special combos of LF and RR that can't just be permuted by big lists. So we have to separate these into unique entries
                        self.log.warn("Found a unique combination of LFLAGS and RARGS in bitcode "+BC+" that cannot be permuted. This bitcode will appear multiple times when finishing.")
                        for comb in unfoundCombos:
                            onlyNew.append( BC, [comb[0]], [comb[1]])
            self.log.debug("Returning only LFLAGS and RARGS combos not found in database: "+str(onlyNew))
            return onlyNew

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
        for proj in self.projects:
            if proj.Valid:
                proj.run()
                self.buildingProjects.add(proj)
            else:
                self.log.error("Project is not valid: "+proj.projectPath)
                self.addProjectReport(proj)

        doneProjects = set()
        while len(self.buildingProjects) > 0:
            # clean all bad jobs before checking project progress
            Command.clean()
            self.givePermission()
            for proj in self.buildingProjects:
                self.log.debug("Checking project "+proj.relPath)
                if proj.done():
                    if not proj.Valid:
                        self.log.error("Project is not valid: "+proj.projectPath)
                        self.addProjectReport(proj)
                    doneProjects.add(proj)
                    BCsToBuild = self.toBuild(proj)
                    for BC in BCsToBuild:
                        newBC = Bc(self.args.project_prefix, proj.projectPath, BC[0], BC[1], BC[2], self.DASQL.ID, proj.ID, self.args)
                        if not newBC.errors:
                            newBC.run()
                            self.buildingBitcodes.add(newBC)
                        else:
                            self.addBitcodeReport(newBC)
                    self.log.info("Project "+proj.projectPath+" is done.")
                    self.log.info("Projects remaining: "+",".join(x.relPath for x in self.buildingProjects-doneProjects))
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
            self.buildingBitcodes -= doneBitcodes
            buildingBitcodeCopy = set()
            for bit in self.buildingBitcodes:
                buildingBitcodeCopy.add(bit)
            self.release()
			# clean all bad jobs before checking bitcode progress
            Command.clean()
            for bit in buildingBitcodeCopy:
                if bit.done():
                    self.log.info("Bitcode "+bit.buildPath+bit.BC+" is done.")
                    self.addBitcodeReport(bit)
                    doneBitcodes.add(bit)
                    if self.DASQL.reset:
                        self.DASQL.logger.warn("Resetting SQL attributes after reconnect")
                        self.DASQL.cnxn = bit.BCSQL.cnxn
                        self.DASQL.reset = False
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
