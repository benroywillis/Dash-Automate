import os
import re
import json

def readKernels(kf, log):
	if "makeNative_" in log:
		path = log.split("/")[:-1]
		logName = log.split("/")[-1]
		logName = "Cartographer_"+logName.split("_")[1:]
		log = path+logName
		print(log)
	Kernels = -1
	staticBlockCoverage = 0.0
	# first open the log to verify that the step ran 
	try:
		log = open(log,"r")
	except Exception as e:
		print("Could not open "+log+": "+str(e))
		return (0,0.0)
	try:
		hj = json.load( open(kf, "r") )
	except Exception as e:
		print("Could not open "+kf+": "+str(e))
		return Kernels,staticBlockCoverage
	if hj.get("Kernels") is not None:
		Kernels = len(hj["Kernels"].keys())
	else:
		return Kernels, staticBlockCoverage

	totalBlocks = 0
	if hj.get("ValidBlocks") is not None:
		totalBlocks = len(hj["ValidBlocks"])
	else:
		return Kernels, staticBlockCoverage
	totalKernelBlocks = set()
	for kid in hj["Kernels"]:
		for entry in hj["Kernels"][kid]:
			if hj["Kernels"][kid].get("Blocks") is not None:
				for block in hj["Kernels"][kid]["Blocks"]:
					totalKernelBlocks.add(block)
	return Kernels, float( float(len(totalKernelBlocks))/float(totalBlocks) )

def readScops(log):
    scops = -1
    try:
        logFile = open(log, "r")
    except Exception as e:
        print("Could not find logfile "+log+": "+str(e))
        return scops

    try:
        for line in logFile:
            scops += len(re.findall("Writing\sJScop\s", line))
    except Exception as e:
        print("Could not parse a line of "+log+": "+str(e))
        return scops

    return scops

# the functions in this file only work if the file tree project has Dash-Corpus in its root path
def findProject(path):
	project = ""
	l = path.split("/")
	for i in range(len(l)):
		if (i+1 < len(l)) and (l[i] == "Dash-Corpus"):
			project = l[i+1]
	return project

def recurseIntoFolder(path, BuildNames, stepStrings, dataMap):
	"""
	@brief 	   recursive algorithm to search through all branches of a directory tree for directories containing files of interest
	@param[in] path			Absolute path to a directory of interest. Initial call should be to to the root of the tree to be searched
	@param[in] BuildNames	Folder names that are being sought after. Likely build folder names
	@param[in] stepString   List of step descriptor substrings to match to log file name strings. This essentially dictates which pipeline steps you are interested in (for example, ["makeNative","Cartographer"])
	@param[in] dataMap      Hash of the data being processed. Contains [project][logFileName][Folder] key and 
	Steps:
	For the profiled builds
	1.) Find each profile log in the build folder (use its name to index dataMap
	2.) Regex the log for the profile time
	3.) Fill in the relevant category in the kernel map (either profiled or unprofiled time) for that project/profile combo
	Then do the same thing for the unprofiled builds, but make sure that for each new unprofiled entry there is a profiled entry (otherwise this profile did not work with the backend)
	"""
	currentFolder = path.split("/")[-1]
	path += "/"
	projectName   = findProject(path)
	if currentFolder in set(BuildNames):
		if dataMap.get(projectName) is None:
			dataMap[projectName] = dict()
		logFiles = []
		logs = path+"/logs/"
		files = os.scandir(logs)
		for stepString in stepStrings:
			for f in files:
				if f.name.startswith(stepString):
					logFiles.append(f.path)
		for log in logFiles:
			logFileName = log.split("/")[-1]
			refinedLogFileName = logFileName
			if refinedLogFileName.startswith("makeNative"):
				refinedLogFileName = "makeNative_"+refinedLogFileName[10:].split(".")[0]+"_0.log"
			kernelFileName = "kernel_"+"_".join(x for x in refinedLogFileName.split("_")[1:]).split(".")[0]+".json"
			keyName     = ""
			for step in stepStrings:
				if logFileName.startswith(step):
					keyName = log.split("/")[-1].replace(step, "")
					break

			if dataMap[projectName].get(keyName) is None:
				dataMap[projectName][keyName] = dict()
				dataMap[projectName][keyName][currentFolder] = (-1,0.0)
			if "HC" in currentFolder:
				print("Hotcode: "+kernelFileName)
				dataMap[projectName][keyName][currentFolder] = readKernels(path+kernelFileName, path+"/logs/"+logFileName)
			elif "2DMarkov" in currentFolder:
				print("2DMarkov: "+kernelFileName)
				dataMap[projectName][keyName][currentFolder] = readKernels(path+kernelFileName, path+"/logs/"+logFileName)
			else:
				print("Scops: "+logFileName)
				dataMap[projectName][keyName][currentFolder] = (readScops(path+"/logs/"+logFileName), 0.0)
		
	directories = []
	for f in os.scandir(path):
		if f.is_dir():
			directories.append(f)

	for d in directories:
		dataMap = recurseIntoFolder(d.path, BuildNames, stepStrings, dataMap)
	return dataMap
