import Util
import shutil
import os
import logging
import subprocess as sp
import re

# specifies the maximum size a SLURM script is allowed to have, in megabytes
MemSize = 4000

logger = logging.getLogger("Command")

"""
@brief Class facilitating the generation of bash scripts and commands

Scripts and Commands come in pairs: The script contains useful work and the command runs the bash script on a Unix command line.
The scripts and commands can be build for either SLURM or just the local bashing software.
"""
class Command:
    def __init__(self, sourcePath, scriptPath="", logFilePath="", targetPath="", SLURM=True, partition=[], environment = ""):
        """
        @param[in] sourcePath   Path to the directory containing the files that will serve as input parameters
        @param[in] scriptPath   Path to the folder that will contain the scripts
        @param[in] logFilePath  Path to the folder that will contain the logs
        @param[in] targetpath   Absolute path to the directory that the output files will go
        @param[in] SLURM        Flag setting the bash files targeted at SLURM or the script software. Right now this is the only bashing interface supported
        @param[in] partition    List of strings specifying which SLURM partition to run scripts on
        """
        # absolute path to the directory holding our input files
        self.sourcePath = sourcePath
        self.scriptsPath = sourcePath if scriptPath == "" else scriptPath
        self.logFilePath = sourcePath if logFilePath == "" else logFilePath
        self.targetPath  = sourcePath if targetPath == "" else targetPath 
        self.SLURM = SLURM
        self.partition = ",".join(x for x in partition)
        self.environment = environment

    def buildTrees(self, scriptTree, globalJobIDs=[], dependencyID=""):
        """
        @brief Builds a depencency tree of bash scripts to be run by SLURM
        @param[in] scriptTree   Input of absolute paths to scripts. Must be a list containing lists, strings and tuples.
        @param[in] globalJobIDs Compound structure describing the dependency tree of all jobs in the scriptTree.
        @param[in] dependencyID String form of the last job ID to go live
        """
        lastID = dependencyID if len(dependencyID) > 0 else ""
        if isinstance(scriptTree, list):
            for i in range( len(scriptTree) ):
                if isinstance(scriptTree[i], list):
                    self.buildTrees(scriptTree[i], globalJobIDs=globalJobIDs, dependencyID=lastID)
                elif isinstance(scriptTree[i], tuple):
                    tupleIDs = tuple()
                    for entry in scriptTree[i]:
                        if isinstance(entry, list):
                            for i in range( len(entry) ):
                                self.buildTrees(entry[i], globalJobIDs=globalJobIDs, dependencyID=tupleIDs[-1])
                        elif isinstance(entry, tuple):
                            # not allowed, skip it
                            continue
                        elif isinstance(entry, str):
                            if len(lastID) > 0:
                                command = "cd "+self.scriptsPath+" ; chmod +x "+entry+" ; sbatch --partition "+self.partition+" --dependency=afterok:"+lastID+" "+entry+" ; exit"
                            else:
                                command = "cd "+self.scriptsPath+" ; chmod +x "+entry+" ; sbatch --partition "+self.partition+" "+entry+" ; exit"
                            tupleIDs = tupleIDs + ( str(int(Util.RunJob(command))), )
                    lastID = ",".join(x for x in tupleIDs)
                    globalJobIDs.append(tupleIDs)

                elif isinstance(scriptTree[i], str):
                    if len(lastID) > 0:
                        command = "cd "+self.scriptsPath+" ; chmod +x "+scriptTree[i]+" ; sbatch --partition "+self.partition+" --dependency=afterok:"+lastID+" "+scriptTree[i]+" ; exit"
                    else:
                        command = "cd "+self.scriptsPath+" ; chmod +x "+scriptTree[i]+" ; sbatch --partition "+self.partition+" "+scriptTree[i]+" ; exit"
                    lastID = Util.RunJob(command)
                    globalJobIDs.append( lastID )

        elif isinstance(scriptTree, tuple):
            tupleIDs = tuple()
            for entry in scriptTree:
                if isinstance(entry, list):
                    for i in range( len(entry) ):
                        self.buildTrees(entry[i], globalJobIDs=globalJobIDs, dependencyID=tupleIDs[-1])
                elif isinstance(entry, tuple):
                    # not allowed, skip it
                    continue
                elif isinstance(entry, str):
                    if len(lastID) > 0:
                        command = "cd "+self.scriptsPath+" ; chmod +x "+entry+" ; sbatch --partition "+self.partition+" --dependency=afterok:"+lastID+" "+entry+" ; exit"
                    else:
                        command = "cd "+self.scriptsPath+" ; chmod +x "+entry+" ; sbatch --partition "+self.partition+" "+entry+" ; exit"
                    tupleIDs = tupleIDs + ( str(int(Util.RunJob(command))), )
            lastID = ",".join(x for x in tupleIDs)
            globalJobIDs.append(tupleIDs)

        elif isinstance(scriptTree, str):
            if len(lastID) > 0:
                command = "cd "+self.scriptsPath+" ; chmod +x "+scriptTree+" ; sbatch --partition "+self.partition+" --dependency=afterok:"+lastID+" "+scriptTree+" ; exit"
            else:
                command = "cd "+self.scriptsPath+" ; chmod +x "+scriptTree+" ; sbatch --partition "+self.partition+" "+scriptTree+" ; exit"
            lastID = Util.RunJob(command)
            globalJobIDs.append( lastID )

    def run(self, scriptTree, dependency=False):
        """
        @brief Runs the given bash script or scripts on a Unix terminal
        @param[in] scriptTree   Absolute path or paths to the script or scripts to run. Can be a string or a list of [string, (tuple of strings)]. If dependency is True, each index of the list (either string or tuple) will have a dependency on the previous index in the list. If dependency is false, bash scripts within tuples will be run as if they were regular string indices.
        @param[in] dependency   Push each entry of the list of scriptTreesto SLURM with a dependency on the previously pushed name. If this flag is set without SLURM, it has no effect
        @retval    jobid        Unique identifier for the job or jobs. Could be a SLURM ID or bash ID. If scriptTrees is a list, a list of each job ID, index aligned to scriptTree, will be returned.
        """
        # process scriptTree first
        jobId = []
        if self.SLURM:
            if dependency:
                self.buildTrees(scriptTree, globalJobIDs=jobId)
            else:
                if isinstance(scriptTree, str):
                    command = "cd "+self.scriptsPath+" ; chmod +x "+self.scriptsPath+" ; sbatch --partition "+self.partition+" "+scriptTree+" ; exit"
                    jobId.append( Util.RunJob(command) )
                elif isinstance(scriptTree, list):
                    for i in range( len(scriptTree) ):
                        command = "cd "+self.scriptsPath+" ; chmod +x "+self.scriptsPath+" ; sbatch --partition "+self.partition+" "+scriptTree[i]+" ; exit"
                        jobId.append( Util.RunJob(command) )
        else:
            logging.error("Only supporting SLURM for now.")

        return jobId

    def poll(self, jobId, checkDependencies=True):
        """
        @brief Polls a job queue for the jobId given.
        @param[in] jobId  Structure of jobIds to look inside the running jobs list for. Input is flattened (if iterable).
        @retval           Returns true if the jobId was found, false otherwise
        """
        # turn the input into integers
        if self.SLURM:
            check = sp.Popen("squeue --noheader -O jobid", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
            output = ""
            while check.poll() is None:
                output += check.stdout.read().decode("utf-8")
            activeIDs = re.findall("(\d+)", output)
            activeIDs = [int(x) for x in activeIDs]

            # flag indicates whether a job (any from the input arg) is still in the queue
            jobFound = False
            # list to keep all jobs whose dependencies have failed
            cancelJobs = []
            # flatten the input data
            for strjob in Util.flatten(jobId):
                job = int(strjob)
                if job in activeIDs:
                    jobFound = True
                    if checkDependencies:
                        # our job is present, check its state and dependencies
                        depjob = sp.Popen("squeue --noheader -j "+str(job)+" -O Reason", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
                        depstring = ""
                        while depjob.poll() is None:
                            depstring += depjob.stdout.read().decode("utf-8")
                        if "DependencyNeverSatis" in depstring:
                            logger.error("Cancelling job "+str(job)+" because its dependencies were never satisified.")
                            cancelJobs.append(job)
            if len(cancelJobs) > 0:
                self.cancel(cancelJobs)
            return jobFound
        else:
            # only supports SLURM for now
            logging.critical("In Command.poll()\n\tCan only handle dependency jobId lists from SLURM!")
            exit()
            return False

    def cancel(self, jobid):
        """
        @brief Cancels jobid in the SLURM queue
        @param[in] jobid    Is flattened before deletion of each member (if necessary)
        """
        cancelString = ""
        for id in Util.flatten(jobid):
            cancelString += str(id)+" "
        check = sp.Popen("scancel "+cancelString, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        output = ""
        while check.poll() is None:
            output += check.stdout.read().decode("utf-8")

    def generateFolder(self, Name="build", subfolders=[]):
        """
        @brief Generate a folder structure
        @param[in]  Name        String, representing the name of the root directory to be built
        @param[in]  subfolders  Folders to build within the root directory. Can be a list or dictionary if multiple levels of directories are desired.
        """
        try:
            os.mkdir(Name)
        except FileExistsError:
            shutil.rmtree(Name)
            os.mkdir(Name)
        if isinstance(subfolders, list):
            for folder in subfolders:
                os.mkdir(Name+"/"+folder)
        elif isinstance(subfolders, dict):
            unimplemented = True
        else:
            logging.error("Subfolders can only be a list or dictionary")

    def moveFiles(self, files, source, sink):
        """
        @brief Moves all files in the input list from the source directory to the sink directory

        During high system load, file movements can be slow, so this function ensures that all files that exist in source are transferred to sink.
        @param[in] files    List of file names (only) to be moved
        @param[in] source   Absolute path to the source directory (directory currently holding all files in files)
        @param[in] sink     Absolute path to the destination directory
        """
        files = set(files)
        toRemove = set()
        # make sure each file exists in its source
        for f in files:
            lf = Util.getLocalFiles(source)
            if f not in lf:
                logger.error("File "+f+" did not exist in folder "+source+"!")
                files.remove(f)

        # make sure each file moves to sink
        while len(files) > 0:
            for f in files:
                shutil.move(source+f, sink+f)
            lf = Util.getLocalFiles(sink)
            for f in files:
                if f in lf:
                    toRemove.add(f)
            for f in toRemove:
                files.remove(f)
            toRemove.clear()

    def constructBashFile(self, Name, commands, logfile="", tasks=1, environment=""):
        """
        @brief Accepts the commands as input and constructs a bash file to run the commands in
        @param[in] Name         String containing the bash file's name. If Name starts with '/', it is assumed to be the absolute path and self.scriptsPath is not used.
        @param[in] Commands     String or strings of commands to put into the bash file. 
                                Can either be a string single string or list of strings.
                                If commands is a string, it will be split by any ' ; ' characters in the string
                                If commands is a list, it will be split by entry: every entry will be treated as one command.
        @param[in] logfile      Optional argument specifying the logfile name in absolute path form
        @param[in] tasks        Number of simultaneous threads this job is expected to demand
        @retval    BashFile     Path to the bashfile that has been made.
        """
        # if not set, set environment to init parameter
        if len(environment) == 0:
            environment = self.environment

        if logfile=="":
            logfile = self.logFilePath+Name.split(".")[0]+".log"

        bashString = "#!/bin/bash\n"
        if self.SLURM:
            bashString += "#\n"
            bashString += "#SBATCH --ntasks="+str(tasks)+"\n"
            bashString += "#SBATCH --ntasks-per-core=1\n"
            if MemSize is not None:
                bashString += "#SBATCH --mem="+str(MemSize)+"\n"
            bashString += "#SBATCH --output="+logfile+"\n"
            bashString += "#SBATCH --error="+logfile+"\n"
            # set maximum time for a given script to be 1 day
            bashString += "#SBATCH --time=1440\n"
            if len(environment) > 0:
                bashString += "export "+environment+"\n"

        if isinstance(commands, list):
            for command in commands:
                bashString += command+"\n"
        elif isinstance(commands, str):
            commandList = commands.split(" ; ")
            for command in commandList:
                bashString += command+"\n"
        else:
            logging.error("Input must be a string or list")
            return None

        if Name.startswith("/"):
            bashFile = Name
        else:
            bashFile = self.scriptsPath+Name
        with open(bashFile, "w+") as f:
            f.write(bashString)
        return bashFile