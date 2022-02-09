import json
import os

def getProjectName(kfPath, baseName):
	while "//" in kfPath:
		kfPath = kfPath.replace("//","/")
	folders = kfPath.split("/")
	for i in range(len(folders)):
		d = folders[i]
		if d == baseName:
			return folders[i+1]
	return ""

def getNativeName(loopName, kernel=False):
	"""
	loopName should be an absolute path to a loop file or kernel file if kernel==True
	This method assumes the loopfile name is Loop_<nativeName>.native
	"""
	path = "/".join(x for x in loopName.split("/")[:-1])
	if kernel:
		file = loopName.split("/")[-1]
		filename = "_".join(x for x in file.split(".")[0].split("kernel_")[1].split("_")[:-1])
	else:
		file = loopName.split("/")[-1]
		filename = file.split(".")[0].split("Loops_")[1]
	return path+"/"+filename

def getTraceName(kfName):
	"""
	kfName should be an absolute path to a kernel file
	This method assumes the file name is kernel_<tracename>.json<_hotCodeType.json>
	"""
	path = "/".join(x for x in kfName.split("/")[:-1])
	file = kfName.split("/")[-1]
	trcName = file.split(".")[0].split("kernel_")[1]
	return path+"/"+trcName

# global parameters for Uniquify to remember its previous work
UniqueIDMap = {}
UniqueID = 0
def Uniquify(project, kernels):
	"""
	Uniquifies the basic block IDs such that no ID overlaps with another ID from another distict application
	"""
	global UniqueID
	global UniqueIDMap
	# project processing, the project name will be the stuff between kernel_ and the first ., indicating the trace name
	traceName = getTraceName(project)
	mappedBlocks = set()
	if UniqueIDMap.get(traceName) is None:
		UniqueIDMap[traceName] = {}
	for k in kernels:
		for block in [int(x) for x in kernels[k]]:
			mappedID = -1
			if UniqueIDMap[traceName].get(block) is None:
				UniqueIDMap[traceName][block] = UniqueID
				mappedID = UniqueID
				UniqueID += 1
			else:
				mappedID = UniqueIDMap[traceName][block]
			if mappedID == -1:
				raise Exception("Could not map the block ID for {},{}!".format(traceName,block))
			mappedBlocks.add(mappedID)
	return mappedBlocks

def Uniquify_static(project, kernels, trc=False):
	"""
	Uniquifies the blocks from static loops in a native file
	Natives map to (possibly) multiple traces
	For example, if a native is foo_0.native, it maps to all traces with foo_0<trc>.bin
	Thus we need to match this native to its traces, if they exist, because they all share the same set of blocks
	@param[in] project 	Absolute path to the file that contains kernels
	@param[in] kernels	Structure of kernels. If trc, kernels is a kernel file. If not trc, kernels is a static loop file
	@retval    mappedBlocks 	Set of integers representing block IDs that have been mapped to the corresponding native file
	"""
	global UniqueID
	global UniqueIDMap
	ntvName = getNativeName(project, kernel=trc)
	mappedBlocks = set()
	if UniqueIDMap.get(ntvName) is None:
		UniqueIDMap[ntvName] = {}
	if trc:
		for k in kernels:
			for block in [int(x) for x in kernels[k]]:
				mappedID = -1
				if UniqueIDMap[ntvName].get(block) is None:
					UniqueIDMap[ntvName][block] = UniqueID
					mappedID = UniqueID
					UniqueID += 1
				else:
					mappedID = UniqueIDMap[ntvName][block]
				if mappedID == -1:
					raise Exception("Could not map the block ID for {},{}!".format(ntvName,block))
				mappedBlocks.add(mappedID)
	else:
		for l in kernels:
			for block in [int(x) for x in kernels[l]["Blocks"]]:
				mappedID = -1
				if UniqueIDMap[ntvName].get(block) is None:
					UniqueIDMap[ntvName][block] = UniqueID
					mappedID = UniqueID
					UniqueID += 1
				else:
					mappedID = UniqueIDMap[ntvName][block]
				if mappedID == -1:
					raise Exception("Could not map the block ID for {},{}!".format(ntvName,block))
				mappedBlocks.add(mappedID)
				
	return mappedBlocks

def readKernelFile_Coverage(kf):
	# first open the log to verify that the step ran 
	"""
	try:
		log = open(log,"r")
	except Exception as e:
		print("Could not open "+log+": "+str(e))
		return -1
	"""
	try:
		hj = json.load( open(kf, "r") )
	except Exception as e:
		print("Could not open "+kf+": "+str(e))
		return -1
	
	if hj.get("Kernels") is None:
		return -1
	if hj.get("ValidBlocks") is None:
		return -1 
	kernelBlocks = set()
	for k in hj["Kernels"]:
		if hj["Kernels"][k].get("Blocks") is None:
			continue
		else:
			for b in hj["Kernels"][k]["Blocks"]:
				kernelBlocks.add(b)
	return len(kernelBlocks)/len(hj["ValidBlocks"])

def readKernelFile(kf, justBlocks=True):
	# first open the log to verify that the step ran 
	"""try:
		log = open(log,"r")
	except Exception as e:
		print("Could not open "+log+": "+str(e))
		return returnDict
	"""
	try:
		hj = json.load( open(kf, "r") )
	except Exception as e:
		print("Could not open "+kf+": "+str(e))
		return -1
	if hj.get("Kernels") is None:
		return -1 
	if hj.get("ValidBlocks") is None:
		return -1
	returnDict = { "Kernels": {} }
	for k in hj["Kernels"]:
		if hj["Kernels"][k].get("Blocks") is None:
			returnDict["Kernels"][k] = {}
		else:
			if justBlocks:
				returnDict["Kernels"][k] = list(hj["Kernels"][k]["Blocks"])
			else:
				returnDict["Kernels"][k] = hj["Kernels"][k]
	return returnDict

def readLoopFile(lf):
	returnDict = {}
	try:
		hj = json.load( open(lf, "r") )
	except Exception as e:
		print("Could not open "+lf+": "+str(e))
		return returnDict
	# hj is a map of { "Loops": {"blocks":[], type: [int]}, "Static Blocks": [] } objects
	if hj is None:
		return returnDict
	for i in range(len(hj["Loops"])):
		if hj["Loops"][i].get("Blocks") is None:
			returnDict[i] = {}
		else:
			returnDict[i] = { "Blocks": list(hj["Loops"][i]["Blocks"]), "Type": hj["Loops"][i]["Type"] }
	return returnDict

def readLoopFile_Coverage(lf):
	try:
		hj = json.load( open(lf, "r") )
	except Exception as e:
		print("Could not open "+lf+": "+str(e))
		return 0.0
	loopBlocks = set()
	# hj is a map of { "Loops": {"blocks":[], type: [int]}, "Static Blocks": [] } objects
	if hj.get("Loops") is None:
		return 0.0
	for i in range(len(hj["Loops"])):
		if hj["Loops"][i].get("Blocks"):
			for b in hj["Loops"][i]["Blocks"]:
				loopBlocks.add(b)
	if hj["Static Blocks"] is None:
		return 0.0
	return len(loopBlocks) / len(hj["Static Blocks"])

# the functions in this file only work if the file tree project has Dash-Corpus in its root path
def findOffset(path, basePath):
	b = set(basePath.split("/"))
	b.remove("")
	p = set(path.split("/"))
	p.remove("")
	offset = p - p.intersection(b)
	# now reconstruct the ordering
	orderedOffset = []
	while len(offset) > 0:
		for entry in path.split("/"):
			if entry in offset:
				orderedOffset.append(entry)
				offset.remove(entry)
	return "/".join(x for x in orderedOffset)

def recurseIntoFolder(path, BuildNames, basePath, folderMap):
	"""
	@brief 	   recursive algorithm to search through all branches of a directory tree for directories containing files of interest

	In general we want a function that can search through a tree of directories and find build folders we are interested in
	The resulting map will form the foundation for uniquifying each entry of data (likely from and automation flow)
	This function constructs that uniquifying map, and at each leaf there lies a build folder of interest

	@param[in] path			Absolute path to a directory of interest. Initial call should be to to the root of the tree to be searched
	@param[in] BuildNames	Folder names that are being sought after. Likely build folder names
	@param[in] folderMap      Hash of the data being processed. Contains [project][logFileName][Folder] key and 
	"""
	BuildNames = set(BuildNames)
	currentFolder = path.split("/")[-1]
	path += "/"
	offset = findOffset(path, basePath)
	if currentFolder in BuildNames:
		if folderMap.get(offset) is None:
			folderMap[offset] = dict()
	
	directories = []
	for f in os.scandir(path):
		if f.is_dir():
			directories.append(f)

	for d in directories:
		folderMap = recurseIntoFolder(d.path, BuildNames, basePath, folderMap)
	return folderMap

def getTargetFilePaths(directoryMap, baseDir, offset = "", prefix = "", suffix = ""):
	"""
	@brief For each entry in the directory map, this function looks for all files that have directoryPath+filePrefix in their absolute path
	@param[in] directoryMap		Map of project folders of interest
								This map should have project path as keys, mapping to a map of build folder(s) of interest
	@param[in] offset			Directory offset that extends the file tree into the build folder
								For example if the user is interested in acquiring log files, the offset should be "logs/"
	@param[in] prefix		String that every file of interest will start with
								For example if the user is interested in kernel files, the prefix should be "kernel_"
	"""
	# list of absolute paths to target files
	targetFiles = []
	for project in directoryMap:
		bfPath = baseDir+"/"+project+"/"+offset+"/"
		for f in os.scandir(bfPath):
			filePath = bfPath+"/"
			if f.name.startswith(prefix) and f.name.endswith(suffix):
				targetFiles.append(filePath+f.name)
	return targetFiles

def parseKernelData(k):
	"""
	@param[in] k 	Absolute path to a kernel file (.json) whose kernel data needs to be extracted
	"""
	with open(k) as f:
		d = json.load(f)
		if d.get("Kernels") is not None:
			return d["Kernels"]
		else:
			return -1

def retrieveKernelData(buildFolders, CorpusFolder, dataFileName, KFReader):
	try:
		with open(dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing data file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to kernel file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
#	kernelTargets = getTargetFilePaths(directoryMap, "/".join(CorpusFolder.split("/")[:-2]), prefix="kernel_", suffix=".json")
	kernelTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="kernel_", suffix=".json")
	for k in kernelTargets:
		dataMap[k] = KFReader(k)#parseKernelData(k)

	with open(dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveStaticLoopData(buildFolders, CorpusFolder, dataFileName, lfReader):
	try:
		with open(dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing loop file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to kernel file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	loopTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="Loops_", suffix=".json")
	for l in loopTargets:
		dataMap[l] = lfReader(l)#parseKernelData(k)

	with open(dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def refineBlockData(dataMap):
	"""
	@brief 	Finds all entries in the map that are not valid ie the entry is -1 and removes them
	"""
	i = 0
	while( i < len(dataMap) ):
		currentKey = list(dataMap.keys())[i]
		if dataMap[currentKey] == -1:
			print("removing {}".format(currentKey))
			del dataMap[currentKey]
		else:
			i += 1
	return dataMap

def matchData(dataMap):
	# here we need to look for three kinds of the same project: PaMul, hotcode and hotloop
	projects = {}
	i = 0
	for project in dataMap:
		name = getTraceName(project)#project.split("/")[-1].split(".")[0]
		if name not in set(projects.keys()):
			projects[name] = { "HotCode": False, "HotLoop": False, "PaMul": False }
			# find out if its a PaMul, hotcode or hotloop
		if "HotCode" in project:
			projects[name]["HotCode"] = True
		elif "HotLoop" in project:
			projects[name]["HotLoop"] = True
		else:
			projects[name]["PaMul"] = True

	while i < len(dataMap):
		project = list(dataMap.keys())[i]
		name = getTraceName(project)#project.split("/")[-1].split(".")[0]
		if projects[name]["HotCode"] and projects[name]["HotLoop"] and projects[name]["PaMul"]:
			i += 1
		else:
			del dataMap[project]
	return dataMap
