import json
import os

## input data
# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Artisan/"
#buildFolders = { "build_noHLconstraints_hc98" }

# most recent build
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#buildFolders = { "build1-30-2022_noHLconstraints" }
#buildFolders = { "build1-31-2022_noHLconstraints_hc95" }
#buildFolders = { "build_noHLconstraints_hc98" } # started 1-31-22
#buildFolders = { "build_2-3-2022_hc95" }
#buildFolders = { "build2-8-2022_hc95" }
#buildFolders = { "build2-14-2022_hc95" }
#buildFolders = { "build2-23-2022_hc95" }
#buildFolders = { "build5-20-22_hc95" }
#buildFolders = { "build5-20-22_newestChanges_hc95" }
#buildFolders = { "build5-22-22_hc95" }
#buildFolders = { "build6-02-22_hc95" }
#buildFolders = { "build6-07-22_hc95" }
buildFolders = { "build6-30-22_hc95" }

def PrintFigure(plt, name):
	plt.savefig("Figures/"+name+".svg",format="svg")
	plt.savefig("Figures/"+name+".eps",format="eps")
	plt.savefig("Figures/"+name+".png",format="png")

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

def reverseUniquify(uniquified, file):
	"""
	Reverse-maps the uniquified BBIDs in uniquified, belonging to the original file argument
	"""
	trcName = getTraceName(file)
	originalIDs = set()
	if UniqueIDMap.get(trcName) is not None:
		for UID in uniquified:
			OID = -1 # original BBID
			for BBID,MID in UniqueIDMap[trcName].items(): # basic block ID and mapped ID
				if UID == MID:
					OID = BBID
					break
			if OID == -1:
				raise ValueError("Cannot map this unique ID to a real BBID!")
			originalIDs.add(OID)
		return originalIDs
	else:
		return originalIDs

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
	if hj.get("Loops") is None:
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

def readLogFile(lf, regexf):
	"""
	lf - absolute path to a log file
	regexf - function looking for a regular expression, should return a string
	"""
	try:
		lf = open(lf, "r")
	except Exception as e:
		print("Could not open logfile "+lf+": "+str(e))
	regexStrings = []
	for line in lf:
		reg = regexf(line)
		if len(reg):
			regexStrings.append(reg)
	return regexStrings

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
		with open("Data/"+dataFileName, "r") as f:
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

	with open("Data/"+dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveStaticLoopData(buildFolders, CorpusFolder, dataFileName, lfReader):
	try:
		with open("Data/"+dataFileName, "r") as f:
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

	with open("Data/"+dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveLogData(buildFolders, CorpusFolder, dataFileName, lfReader):
	try:
		with open("Data/"+dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing log info file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to log file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	logTargets = getTargetFilePaths(directoryMap, CorpusFolder, offset="logs/", prefix="Cartographer_", suffix=".log")
	for l in logTargets:
		dataMap[l] = readLogFile(l, lfReader)

	with open("Data/"+dataFileName,"w") as f:
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

def SortAndMap_App(dataMap, InterestingProjects):
	"""
	This function turns a map of kernel files into a map of application names (native name), values { HC: { KID: set(uniquified_blocks) }, .. }
	@param[in] 	dataMap	Map of kernel files. Key is absolute path to a kernel file, value is a map of KIDs to sets of basic blocks
				Specifically: { kf: { "Kernels": { int(kid): set(blocks), ... } } }
	@param[in]  InterestingProjects	Set of project names that should be included in the data. If this set is empty, no project is vetted
	@retval appMap	Maps an application name (native name) to each type of segmentation, each segmentation is mapped to kernel IDs, each kernel ID has a set of uniquified basic block IDs
					ie { NTV: { "HC": { int(kid): set(uniquified_blocks), ... }, "HL": { ... }, "PaMul": { ... } }, ... }
	@retval xtickLabels 	List of strings, where each member corresponds to a key in appMap
							The keys in appMap are sorted, and whenever the project a given key comes from changes, the first key of that project gets an x-axis label of that project name
							For the rest of the keys belonging to that project, the xtick label is an empty string
	Since multiple traces can map to a single application, this method takes the union of each kernel ID from each trace
	"""
	# sorted list of absolute kernel file paths
	sortedKeys = sorted(dataMap)
	# list of labels that mark the beginnings and ends of each project in the x-axis applications
	xtickLabels = list()
	# set of projectNames that have been seen in the input data
	projectNames = set()
	# maps an application name to its HC, HL and PaMul data (each label has a set of uniquified basic block IDs
	appNames = dict()
	# for each trace
	for kfPath in sortedKeys:
		# make sure it is part of the projects we are interested in, and make an entry for it if it doesn't yet exist in our data
		if dataMap[kfPath].get("Kernels"):
			project = getProjectName(kfPath, "Dash-Corpus")
			if len(InterestingProjects):
				if project not in InterestingProjects:
					continue
			newProject = False
			if project not in projectNames:
				xtickLabels.append(project)
				projectNames.add(project)
				newProject = True

			# once that change is made, we will map multiple traces to one application... so you have to take the union of all traces for each application
			appName = "/".join(x for x in kfPath.split("/")[:-1])+getNativeName(kfPath, kernel=True)
			# if we haven't seen this app before, add an entry to the processed data array
			# this is a new application with a project, if this app isn't getting the project name as its xlabel give it a blank one
			if appName not in appNames:
				appNames[appName] = { "HC": set(), "HL": set(), "PaMul": set() }
				if not newProject:
					xtickLabels.append("")

			if "HotCode" in kfPath:
				appNames[appName]["HC"] = appNames[appName]["HC"].union( Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )
			elif "HotLoop" in kfPath:
				appNames[appName]["HL"] = appNames[appName]["HL"].union( Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )
			else:
				appNames[appName]["PaMul"] = appNames[appName]["PaMul"].union( Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )

	return appNames, xtickLabels

def OverlapRegions(appMap):
	"""
	This function overlaps all 7 regions possible for a 3-circle venn diagram
	The input appMap should be a map of native file data as described in the return value description of SortAndMap_App
	"""
	if not len(appMap):
		return [ [], [], [], [], [], [], [] ]
	for kfPath in appMap:
		HCset = appMap[kfPath]["HC"]
		HLset = appMap[kfPath]["HL"]
		PaMulset = appMap[kfPath]["PaMul"]
		# john: do this in reverse order bc that saves work
		HC        = HCset - HLset - PaMulset
		HL        = HLset - HCset - PaMulset
		PaMul     = PaMulset - HCset - HLset
		HCHL      = HCset.intersection(HLset) - PaMulset
		PaMulHC   = PaMulset.intersection(HCset) - HLset
		PaMulHL   = PaMulset.intersection(HLset) - HCset
		PaMulHCHL = PaMulset.intersection(HCset).intersection(HLset) 
	# when using this with matplotlib_venn, [A, B, AB, C, AC, BC, ABC] with labels [A, B, C]
	return [HC, HL, HCHL, PaMul, PaMulHC, PaMulHL, PaMulHCHL]
