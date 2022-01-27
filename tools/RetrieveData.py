import json
import os

def readKernelFile(kf, log):
	returnDict = {}
	# first open the log to verify that the step ran 
	try:
		log = open(log,"r")
	except Exception as e:
		print("Could not open "+log+": "+str(e))
		return returnDict
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
			returnDict["Kernels"][k] = list(hj["Kernels"][k]["Blocks"])
	return returnDict

# the functions in this file only work if the file tree project has Dash-Corpus in its root path
def findProject(path):
	project = ""
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
	print(path)
	print(project)
	return project

def recurseIntoFolder(path, BuildNames, folderMap):
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
	projectName   = findProject(path)
	if currentFolder in BuildNames:
		if folderMap.get(projectName) is None:
			folderMap[projectName] = dict()
		folderMap[projectName][currentFolder] = {}
	
	directories = []
	for f in os.scandir(path):
		if f.is_dir():
			directories.append(f)

	for d in directories:
		folderMap = recurseIntoFolder(d.path, BuildNames, folderMap)
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
		for bf in directoryMap[project]:
			bfPath = baseDir+"/"+project+"/"+bf+"/"+offset+"/"
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
		recurseIntoFolder(CorpusFolder, buildFolders, directoryMap)
		kernelTargets = getTargetFilePaths(directoryMap, "/".join(CorpusFolder.split("/")[:-2]), prefix="kernel_", suffix=".json")
		HCTargets = getTargetFilePaths(directoryMap, "/".join(CorpusFolder.split("/")[:-2]), prefix="kernel_", suffix="_HotCode.json")
		HLTargets = getTargetFilePaths(directoryMap, "/".join(CorpusFolder.split("/")[:-2]), prefix="kernel_", suffix="_HotLoop.json")
		for k in kernelTargets:
			dataMap[k] = parseKernelData(k)

		with open(CorpusFolder+"allKernelData.json","w") as f:
			json.dump(dataMap, f, indent=4)

	return dataMap

def matchData(dataMap, buildFolders):
	# pairs all types together
	matchedData = {}
	for project in dataMap:
		for keyName in dataMap[project]:
			# keys: directory information comes from, value: tuple( kernels, blockCoverage )
			d = dataMap[project][keyName]
			allFound = True
			for key in d:
				if d[key].get("Kernels") is None:
					allFound = False
			if allFound:
				if matchedData.get(project) is None:
					matchedData[project] = dict()
					# first index kernels, second index static block coverage
				if matchedData[project].get(keyName) is None:
					matchedData[project][keyName] = {}
				for bf in buildFolders:
					matchedData[project][keyName][bf] = dataMap[project][keyName][bf]

	with open("MatchedData.json","w") as f:
		json.dump(matchedData, f, indent=4)
	return matchedData


