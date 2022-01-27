import json
import os

def readKernelFile(kf, justBlocks=True):
	returnDict = {}
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
		return returnDict
	
	if hj.get("Kernels") is None:
		return returnDict
	if hj.get("ValidBlocks") is None:
		return returnDict
	returnDict["Kernels"] = {}
	for k in hj["Kernels"]:
		if hj["Kernels"][k].get("Blocks") is None:
			returnDict["Kernels"][k] = {}
		else:
			if justBlocks:
				returnDict["Kernels"][k] = list(hj["Kernels"][k]["Blocks"])
			else:
				returnDict["Kernels"][k] = hj["Kernels"][k]
	return returnDict

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
	"""	
	l = path.split("/")
	i = 0
	while i < len(l):
		if l[i] == "":
			del l[i]
		i += 1
	idx_DC = 100000000
	for i in range(len(l)):
		if (i+1 < len(l)) and (i > idx_DC):
			project += l[i]+"/"
		elif( l[i] == "Dash-Corpus" ):
			idx_DC = i
	return project
	"""

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

def retrieveKernelData(buildFolders, CorpusFolder, dataFileName, findOld=True):
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to kernel file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	generateData = ~findOld
	if not generateData:
		try:
			with open(CorpusFolder+dataFileName,"r") as f:
				dataMap = json.load( f )

		except FileNotFoundError:
			print("Could not find an existing {}, generating a new one".format(CorpusFolder+dataFileName))
			generateData = True
	if generateData:
		recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
#		kernelTargets = getTargetFilePaths(directoryMap, "/".join(CorpusFolder.split("/")[:-2]), prefix="kernel_", suffix=".json")
		kernelTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="kernel_", suffix=".json")
		HCTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="kernel_", suffix="_HotCode.json")
		HLTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="kernel_", suffix="_HotLoop.json")
		for k in kernelTargets:
			dataMap[k] = readKernelFile(k)#parseKernelData(k)

		with open(CorpusFolder+"allKernelData.json","w") as f:
			json.dump(dataMap, f, indent=4)

	return dataMap

def refineBlockData(dataMap):
	"""
	@brief 	Finds all entries in the map that are not valid ie the entry is -1 and removes them
	"""
	refinedMap = {}
	for file in dataMap:
		if dataMap[file] == -1:
			continue
		refinedMap[file] = {}
		for k in dataMap[file]:
			refinedMap[file][k] = dataMap[file][k]
	return refinedMap

def matchData(dataMap):
	# here we need to look for three kinds of the same project: PaMul, hotcode and hotloop
	projects = {}
	matchedData = {}
	for project in dataMap:
		name = project.split("/")[-1].split(".")[0]
		if name not in set(projects.keys()):
			projects[name] = { "HotCode": -1, "HotLoop": -1, "PaMul": -1 }
			# find out if its a PaMul, hotcode or hotloop
		if "HotCode" in project:
			projects[name]["HotCode"] = project
		elif "HotLoop" in project:
			projects[name]["HotLoop"] = project
		else:
			projects[name]["PaMul"] = project

	for project in dataMap:
		name = name = project.split("/")[-1].split(".")[0]
		if projects[name].get("HotCode") and projects[name].get("HotLoop") and projects[name].get("PaMul"):
			matchedData[project] = dataMap[project]
	print(matchedData)
	return matchedData
