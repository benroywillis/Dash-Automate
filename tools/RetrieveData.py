# for reading and writing jsons
import json
# for filesystem ops
import os
# for reading binary-encoded profiles
import struct
# for reading log file strings
import re
## input data
# for testing
#CorpusFolder = "/mnt/heorot-03/bwilli46/Dash-Corpus/GSL/"
#CorpusFolder = "/mnt/heorot-03/bwilli46/Dash-Corpus/Artisan/"
#buildFolders = { "build_noHLconstraints_hc98" }

# most recent build
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
CorpusFolder = "/mnt/heorot-03/bwilli46/Dash-Corpus/"
#CorpusFolder = "/home/bwilli46/Algorithms/BilateralFilter/API/tests/"
#CorpusFolder = "/home/bwilli46/TraceAtlas/build/Tests/"
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
#buildFolders = { "build6-30-22_hc95" }
#buildFolders = { "build7-5-22_hc95" }
#buildFolders = { "build7-28-22_hc95" }
#buildFolders = { "build7-29-22_hc95" }
#buildFolders = { "build8-07-22_hc95" }
#buildFolders = { "build8-12-22" }
#buildFolders = { "build8-16-22" }
#buildFolders = { "build8-17-22" }
#buildFolders = { "build8-20-22" }
#buildFolders = { "build8-22-22" }
#buildFolders = { "build8-24-22" }
#buildFolders = { "build8-28-22" }
#buildFolders = { "build9-04-22" }
#buildFolders = { "build9-09-22" }
#buildFolders = { "build9-12-22" }
#buildFolders = { "build9-19-22" }
#buildFolders = { "build9-20-22" }
#buildFolders = { "build9-22-22" }
#buildFolders = { "build9-30-22" }
#buildFolders = { "build10-05-22" }
buildFolders = { "build10-22-22" }
#buildFolders = { "build_OPENCV_test" }
#buildFolders = { "OldBuild" }
#buildFolders = { "STL_Test" }

def PrintFigure(plt, name, buildTag=True):
	if buildTag:
		figureName = "Figures/"+name+"_"+list(buildFolders)[0]
	else:
		figureName = "Figures/"+name+".svg"
	plt.savefig(figureName+".svg",format="svg")
	plt.savefig(figureName+".eps",format="eps")
	plt.savefig(figureName+".png",format="png")

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

def getTraceName(kfName, instance=False):
	"""
	kfName should be an absolute path to a kernel file
	This method assumes the file name is kernel_<tracename>.json<_hotCodeType.json>
	"""
	if "instance" in kfName:
		instance = True
	path = "/".join(x for x in kfName.split("/")[:-1])
	file = kfName.split("/")[-1]
	if instance:
		trcName = file.split(".")[0].split("instance_")[1]
	else:
		trcName = file.split(".")[0].split("kernel_")[1]
	return path+"/"+trcName

# global parameters for Uniquify to remember its previous work
UniqueIDMap = {}
UniqueID = 0
def Uniquify(project, kernels, tn=True, blocks = False):
	"""
	Uniquifies the basic block IDs such that no ID overlaps with another ID from another distict application
	"""
	global UniqueID
	global UniqueIDMap
	# project processing, the project name will be the stuff between kernel_ and the first ., indicating the trace name
	if tn:
		traceName = getTraceName(project)
	else:
		traceName = project
	mappedBlocks = set()
	if UniqueIDMap.get(traceName) is None:
		UniqueIDMap[traceName] = {}
	if not blocks:
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
	else:
		for block in [int(x) for x in kernels]:
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

def readTimingPassTime(line):
	time = re.findall("NATIVETIME\:\s\d+\.\d+", line)
	if len(time):
		s = time[0].split(" ")[1]
		return [float(s)]
	return []

def readMarkovPassTime(line):
	time = re.findall("PROFILETIME\:\s\d+\.\d+", line)
	if len(time):
		s = time[0].split(" ")[1]
		return [float(s)]
	return []

def readMemoryPassTime(line):
	time = re.findall("MEMORYPROFILETIME\:\s\d+\.\d+", line)
	if len(time):
		s = time[0].split(" ")[1]
		return [float(s)]
	return []

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

def readOverallCode(kf, profileInfo):
	try:
		hj = json.load( open(kf, "r") )
	except Exception as e:
		print("Could not open "+kf+": "+str(e))
		return -1
	if hj.get("Kernels") is None:
		return -1 
	if hj.get("ValidBlocks") is None:
		return -1
	Livecode = set()
	for edge in profileInfo:
		Livecode.add(edge[0])
		Livecode.add(edge[1])
	Deadcode = set(hj["ValidBlocks"]) - Livecode
	returnDict = { "Deadcode": list(Deadcode), "Livecode": list(Livecode) }
	return returnDict

def readKernelGrammarFile(kgf):
	"""
	"""
	try:
		kgj = json.load( open(kgf, "r") )
	except Exception as e:
		print("Could not open "+kgf+": "+str(e))
		return -1
	if kgj.get("Statistics") is not None:
		return kgj["Statistics"]
	return -1

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
		logfile = open(lf, "r")
	except Exception as e:
		print("Could not open logfile "+lf+": "+str(e))
	regexStrings = []
	try:
		for line in logfile:
			reg = regexf(line)
			if len(reg):
				regexStrings.append(reg)
	except Exception as e:
		print("Could not read a line in log file "+lf+": "+str(e))
	return regexStrings

def readProfile(f):
	"""
	Reads a profile in binary format
	@retval 	tuple( a map from edge to frequency, a map of block ID to frequency )
	"""
	try:
		pf = open(f, "rb")
	except Exception as e:
		print("Could not open profile file "+f+": "+str(e))
		return
	profile_b = pf.read()
	# markov order
	MO = struct.unpack("I", profile_b[:4])[0]
	# block count
	blockCount = struct.unpack("I", profile_b[4:8])[0]
	# edge count
	edgeCount = struct.unpack("I", profile_b[8:12])[0]
	# read each edge and frequency
	# maps a tuple of src,snk to a frequency count
	profile = {}
	for newEdge in struct.iter_unpack("IIL", profile_b[12:]):
		src = newEdge[0]
		snk = newEdge[1]
		fre = newEdge[2]
		profile[ (src,snk) ] = fre

	blockFrequencies = {}
	for edge in profile:
		if blockFrequencies.get(edge[1]) is None:
			blockFrequencies[edge[1]] = profile[edge]
		else:
			blockFrequencies[edge[1]] += profile[edge]
	return profile, blockFrequencies

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
				# remove excess slashes in the paths
				pathList = filePath.split("/")
				while "" in pathList:
					pathList.remove("")
				filePath = "/".join( x for x in pathList )
				targetFiles.append("/"+filePath+"/"+f.name)
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
		print("No pre-existing kernel data file. Running collection algorithm...")
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

def retrieveDeadCode(buildFolders, CorpusFolder, dataFileName, profileInfo):
	try:
		with open("Data/"+dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing deadcode data file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to kernel file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	kernelTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="kernel_", suffix=".json")
	for k in kernelTargets:
		# skip hotcode and hotloop files, that is redundant work (though they would yield the same answer)
		if "HotCode" in k:
			continue
		elif "HotLoop" in k:
			continue
		# find its profile info and hand it to the deadcode reader
		profileName = getTraceName(k)+".bin"
		if profileInfo.get(profileName) is None:
			print("Could not find profile info for {}! Skipping...".format(profileName))
			continue
		dataMap[k] = readOverallCode(k, profileInfo[profileName])

	with open("Data/"+dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveInstanceData(buildFolders, CorpusFolder, dataFileName, KFReader):
	try:
		with open("Data/"+dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing instance data file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to kernel file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	kernelTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="instance_", suffix=".json")
	for k in kernelTargets:
		dataMap[k] = KFReader(k)

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

def retrieveKernelGrammarData(buildFolders, CorpusFolder, dataFileName, kgReader):
	try:
		with open("Data/"+dataFileName, "r") as f:
			dataMap = json.load(f)
			return dataMap
	except FileNotFoundError:
		print("No pre-existing kernel grammar file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to log file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	kgTargets = getTargetFilePaths(directoryMap, CorpusFolder, prefix="KG_", suffix=".json")
	for k in kgTargets:
		dataMap[k] = readKernelGrammarFile(k)

	with open("Data/"+dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveLogData(buildFolders, CorpusFolder, dataFileName, lfReader, Prefix="Cartographer_"):
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
	logTargets = getTargetFilePaths(directoryMap, CorpusFolder, offset="logs/", prefix=Prefix, suffix=".log")
	for l in logTargets:
		dataMap[l] = readLogFile(l, lfReader)

	with open("Data/"+dataFileName,"w") as f:
		json.dump(dataMap, f, indent=4)

	return dataMap

def retrieveProfiles(buildFolders, CorpusFolder, dataFileName):
	try:
		with open("Data/"+dataFileName, "r") as f:
			kvList = json.load(f)
			# the file is stored as a list of key-value pairs, so reconstruct the map from that list
			dataMap = {}
			for path in kvList:
				dataMap[path] = {}
				for entry in kvList[path]:
					dataMap[path][tuple(entry["key"])] = entry["value"]
			return dataMap
	except FileNotFoundError:
		print("No pre-existing profile file. Running collection algorithm...")
	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to log file data
	# abs path : kernel data
	dataMap = {}
	# determines if the data generation code needs to be run
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)
	profileTargets = getTargetFilePaths(directoryMap, CorpusFolder, suffix=".bin")
	for l in profileTargets:
		dataMap[l] = readProfile(l)[0]

	with open("Data/"+dataFileName,"w") as f:
		# the json dumper can't handle tuples as keys
		# therefore we turn the map into a list of key-value pairs
		json.dump( { p: [ { "key": k, "value": v } for k, v in dataMap[p].items() ] for p in dataMap }, f, indent=4)

	return dataMap

def retrieveTimingData(buildFolders, CorpusFolder, dataFileName):
	try:
		with open("Data/"+dataFileName, "r") as f:
			return json.load(f)
	except FileNotFoundError:
		print("No pre-existing timing data file. Running collection algorithm...")
	# timing data is contained within three types log files
	# 1. timing pass
	# 2. markov pass
	# 3. memory pass
	# each pass will have one or more samples and they all need to be collected
	
	# all file names have within them a trace name that will unify their key in the dataMap

	# contains paths to all directories that contain files we seek 
	# project path : build folder 
	directoryMap = {}
	# maps project paths to log file data
	# abs path : kernel data
	dataMap = {}
	recurseIntoFolder(CorpusFolder, buildFolders, CorpusFolder, directoryMap)

	# first, timing pass
	profileTargets = getTargetFilePaths(directoryMap, CorpusFolder, offset="logs/", prefix="Timing_", suffix=".log")
	for l in profileTargets:
		tracePath = "/".join(x for x in l.split("/")[:-1])+"/"+"_".join( x for x in l.split("/")[-1].split(".")[0].split("_")[1:] )
		if dataMap.get(tracePath) is None:
			dataMap[tracePath] = { "Timing": {}, "Markov": {}, "Memory": {} }
		t = readLogFile(l, readTimingPassTime)
		if len(t):
			# record the sample number and time
			sampleS = re.findall("_sample\d+", l)
			if len(sampleS):
				sample = sampleS[0].split("sample")[1]
				dataMap[tracePath]["Timing"][sample] = t[0][0]
			else:
				print("Could not find sample number for log "+l)
		else:
			print("Could not retrieve time stat for log file "+l)
	
	# second, markov pass
	profileTargets = getTargetFilePaths(directoryMap, CorpusFolder, offset="logs/", prefix="makeTrace_", suffix=".log")
	for l in profileTargets:
		tracePath = "/".join(x for x in l.split("/")[:-1])+"/"+"_".join( x for x in l.split("/")[-1].split(".")[0].split("_")[1:] )
		if dataMap.get(tracePath) is None:
			print("found a file path when searching through markov not yet in datamap")
			dataMap[tracePath] = { "Timing": {}, "Markov": {}, "Memory": {} }
		t = readLogFile(l, readMarkovPassTime)
		if len(t):
			# record the sample number and time
			sampleS = re.findall("_sample\d+", l)
			if len(sampleS):
				sample = sampleS[0].split("sample")[1]
				dataMap[tracePath]["Markov"][sample] = t[0][0]
			else:
				print("Could not find sample number for log "+l)
		else:
			print("Could not retrieve time stat for log file "+l)

	# third, memory pass
	profileTargets = getTargetFilePaths(directoryMap, CorpusFolder, offset="logs/", prefix="MemoryPass_", suffix=".log")
	for l in profileTargets:
		tracePath = "/".join(x for x in l.split("/")[:-1])+"/"+"_".join( x for x in l.split("/")[-1].split(".")[0].split("_")[1:] )
		if dataMap.get(tracePath) is None:
			dataMap[tracePath] = { "Timing": {}, "Markov": {}, "Memory": {} }
		t = readLogFile(l, readMemoryPassTime)
		if len(t):
			# record the sample number and time
			sampleS = re.findall("_sample\d+", l)
			if len(sampleS):
				sample = sampleS[0].split("sample")[1]
				dataMap[tracePath]["Memory"][sample] = t[0][0]
			else:
				print("Could not find sample number for log "+l)
		else:
			print("Could not retrieve time stat for log file "+l)
	exit(dataMap)
	return dataMap

def refineBlockData(dataMap, loopFile=False, deadCodeFile=False):
	"""
	@brief 	Finds all entries in the map that are not valid ie the entry is -1 and removes them
	"""
	i = 0
	while( i < len(dataMap) ):
		currentKey = list(dataMap.keys())[i]
		if deadCodeFile:
			if dataMap[currentKey] == -1 :
				print("removing {}".format(currentKey))
				del dataMap[currentKey]
			elif dataMap[currentKey].get("Deadcode") is None:
				print("removing {}".format(currentKey))
				del dataMap[currentKey]
			elif dataMap[currentKey].get("Livecode") is None:
				print("removing {}".format(currentKey))
				del dataMap[currentKey]
			else:
				i += 1
		elif dataMap[currentKey] == -1:
			print("removing {}".format(currentKey))
			del dataMap[currentKey]
		elif loopFile and (len(dataMap[currentKey]) == 0):
			print("removing {}".format(currentKey))
			del dataMap[currentKey]
		elif (not loopFile) and (dataMap[currentKey].get("Kernels") is None):
			print("removing {}".format(currentKey))
			del dataMap[currentKey]
		elif (not loopFile) and (not isinstance( dataMap[currentKey]["Kernels"], dict )):
			print("removing {}".format(currentKey))
			del dataMap[currentKey]
		else:
			i += 1
	return dataMap

def matchData(dataMap, instanceMap=dict(), instance=False):
	# here we need to look for three kinds of the same project: PaMul, Instance, hotcode and hotloop
	projects = {}
	i = 0
	if instance:
		for key,value in instanceMap.items():
			dataMap[key] = value
			
	for project in dataMap:
		name = getTraceName(project, instance = True if "instance" in project else False)
		if name not in set(projects.keys()):
			projects[name] = { "HotCode": False, "HotLoop": False, "PaMul": False, "Instance": False }
			# find out if its a PaMul, hotcode or hotloop
		if "HotCode" in project:
			projects[name]["HotCode"] = True
		elif "HotLoop" in project:
			projects[name]["HotLoop"] = True
		elif "instance" in project:
			projects[name]["Instance"] = True
		else:
			projects[name]["PaMul"] = True

	while i < len(dataMap):
		project = list(dataMap.keys())[i]
		name = getTraceName(project, instance = True if "instance" in project else False)
		if projects[name]["HotCode"] and projects[name]["HotLoop"] and projects[name]["PaMul"] and projects[name]["Instance"]:
			i += 1
		else:
			del dataMap[project]
	return dataMap

def getProjectAxisLabels(keys):
	"""
	@brief 		Generates a list of axis tick labels specifying the beginning of projects
	@param[in] 	keys		Should be a list of file paths that contain a project name
	@retval		axisLabels	List of tick labels. 
							The labels are either a project name (denoting the start of a project's applications, from left to right)
							Or they are an empty string
	"""
	axisLabels = []
	projectNames = set()
	for path in keys:
		project = getProjectName(path, "Dash-Corpus")
		newProject = False
		if project not in projectNames:
			axisLabels.append(project)
			projectNames.add(project)
		else:
			axisLabels.append("")
	return axisLabels

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

def OverlapRegions(HCKs, HLKs, PaMulKs):
	"""
	This function overlaps all 7 regions possible for a 3-circle venn diagram
	The input appMap should be a map of native file data as described in the return value description of SortAndMap_App
	"""
	HCset = set()
	for k in HCKs:
		for b in HCKs[k]:
			HCset.add(int(b))
	HLset = set()
	for k in HLKs:
		for b in HLKs[k]:
			HLset.add(int(b))
	PaMulset = set()
	for k in PaMulKs:
		for b in PaMulKs[k]:
			PaMulset.add(int(b))
	# john: do this in reverse order bc that saves work
	HC        = HCset - HLset - PaMulset
	HL        = HLset - HCset - PaMulset
	PaMul     = PaMulset - HCset - HLset
	HCHL      = HCset.intersection(HLset) - PaMulset
	PaMulHC   = PaMulset.intersection(HCset) - HLset
	PaMulHL   = PaMulset.intersection(HLset) - HCset
	PaMulHCHL = PaMulset.intersection(HCset).intersection(HLset) 
	# when using this with matplotlib_venn, [A, B, AB, C, AC, BC, ABC] with labels [A, B, C]
	return HC, HL, PaMul, HCHL, PaMulHC, PaMulHL, PaMulHCHL

def neutralPath(path):
	"""
	@brief Finds the path that only contains the unique identifier of that application (the trace name with its absolute path)
	Does almost exactly what RD.getTraceName() does but it doesn't set any hard requirements on the filename
	"""
	return "/".join( x for x in path.split("/")[:-1]) + path.split("/")[-1].split(".")[0].split("_")[1]

def combineData( loopData = {}, profileData = {}, kernelData = {}, instanceData = {}, deadBlocksData = {} ):
	"""
	@brief Takes all maps, finds the common path between keys in each map and combines them into a single map
	@param[in] kernelData 		Map of kernel data, which may contain hotcode and hotloop information. Each key should be an absolute path to a kernel file
	@param[in] instanceData 	Map of instance data, which should only contain instance data. Each key should be an absolute path to an instance file.
	"""
	allData = {}
	# add deadcode data
	for path in deadBlocksData:
		projectPath = getTraceName(path)
		if allData.get(projectPath) is None:
			allData[projectPath] = { "LiveBlocks": {}, "DeadBlocks": {}, "Loop": {}, "Profile": {}, "HotCode": {}, "HotLoop": {}, "PaMul": {}, "Instance": {} }
		allData[projectPath]["LiveBlocks"] = deadBlocksData[path]["Livecode"]
		allData[projectPath]["DeadBlocks"] = deadBlocksData[path]["Deadcode"]
	# add profile data
	for path in profileData:
		projectPath = "/".join( x for x in path.split("/")[:-1]) + "/" + path.split("/")[-1].split(".")[0]
		if allData.get(projectPath) is None:
			allData[projectPath] = { "LiveBlocks": {}, "DeadBlocks": {}, "Loop": {}, "Profile": {}, "HotCode": {}, "HotLoop": {}, "PaMul": {}, "Instance": {} }
		allData[projectPath]["Profile"] = profileData[path]
	# add kernel data
	for path in kernelData:
		#projectPath = "/".join( x for x in path.split("/")[:-1]) + path.split("/")[-1].split(".")[0].split("_")[1]
		projectPath = getTraceName(path)
		if allData.get(projectPath) is None:
			allData[projectPath] = { "LiveBlocks": {}, "DeadBlocks": {}, "Loop": {}, "Profile": {}, "HotCode": {}, "HotLoop": {}, "PaMul": {}, "Instance": {} }
		if "HotCode" in path:
			if isinstance( kernelData[path], dict ):
				allData[projectPath]["HotCode"] = kernelData[path]["Kernels"]
		elif "HotLoop" in path:
			if isinstance( kernelData[path], dict ):
				allData[projectPath]["HotLoop"] = kernelData[path]["Kernels"]
		else:
			if isinstance( kernelData[path], dict ):
				allData[projectPath]["PaMul"] = kernelData[path]["Kernels"]
	# add instance data
	for path in instanceData:
		projectPath = getTraceName(path)
		if allData.get(projectPath) is None:
			allData[projectPath] = { "LiveBlocks": {}, "DeadBlocks": {}, "Loop": {}, "Profile": {}, "HotCode": {}, "HotLoop": {}, "PaMul": {}, "Instance": {} }
		if isinstance( instanceData[path], dict ):
			allData[projectPath]["Instance"] = instanceData[path]["Kernels"]
	# add loop data
	# we do this last so that the entire application namespace is already in allData
	for path in loopData:
		# native namespace (the Loop files are named after standalone binaries because static loops are per-binary, not application)
		# thus, you have to apply all permutations seen in the application namespace to the native namespace
		nativePath = getNativeName(path)
		if isinstance(loopData[path], dict):
			for tracePath in allData:
				if nativePath in tracePath:
					allData[tracePath]["Loop"] = loopData[path]
	# remove all entries that do not have all types
	projects = {}
	i = 0
	for project in allData:
		if project not in set(projects.keys()):
			projects[project] = { "LiveBlocks": False, "DeadBlocks": False, "Loop": False, "Profile": False, "HotCode": False, "HotLoop": False, "PaMul": False, "Instance": False }
		if len(allData[project]["LiveBlocks"]):
			projects[project]["LiveBlocks"] = True
		if len(allData[project]["DeadBlocks"]):
			projects[project]["DeadBlocks"] = True
		if len(allData[project]["Loop"]):
			projects[project]["Loop"] = True
		if len(allData[project]["Profile"]):
			projects[project]["Profile"] = True
		if len(allData[project]["HotCode"]):
			projects[project]["HotCode"] = True
		if len(allData[project]["HotLoop"]):
			projects[project]["HotLoop"] = True
		if len(allData[project]["PaMul"]):
			projects[project]["PaMul"] = True
		if len(allData[project]["Instance"]):
			projects[project]["Instance"] = True
	
	while i < len(allData):
		project = list(allData.keys())[i]
		if len(deadBlocksData):
			if (not projects[project]["LiveBlocks"]) or (not projects[project]["DeadBlocks"]):
				del allData[project]
				continue
			else:
				i += 1
		if len(loopData) and len(kernelData) and len(instanceData) and len(profileData):
			if 	projects[project]["Loop"]    and projects[project]["Profile"] and projects[project]["HotCode"] and \
				projects[project]["HotLoop"] and projects[project]["PaMul"]   and projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(profileData) and len(kernelData):
			if 	projects[project]["Loop"] and projects[project]["Profile"] and projects[project]["HotCode"] and \
				projects[project]["HotLoop"] and projects[project]["PaMul"] :
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(kernelData) and len(instanceData):
			if 	projects[project]["Loop"] and projects[project]["HotCode"] and projects[project]["HotLoop"] and \
				projects[project]["PaMul"] and projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(profileData) and len(instanceData):
			if 	projects[project]["Loop"] and projects[project]["Profile"] and projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(profileData) and len(kernelData) and len(instanceData):
			if 	projects[project]["Profile"] and projects[project]["HotCode"] and projects[project]["HotLoop"] and \
				projects[project]["PaMul"] and projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(profileData):
			if  projects[project]["Loop"] and projects[project]["Profile"]:
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(kernelData):
			if  projects[project]["Loop"] and projects[project]["HotCode"] and projects[project]["HotLoop"] and projects["PaMul"]:
				i += 1
			else:
				del allData[project]
		elif len(loopData) and len(instanceData):
			if  projects[project]["Loop"] and projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(profileData) and len(kernelData):
			if 	projects[project]["Profile"] and projects[project]["HotCode"] and projects[project]["HotLoop"] and \
				projects[project]["PaMul"]:
				i += 1
			else:
				del allData[project]
		elif len(profileData) and len(instanceData):
			if projects[project]["Profile"] and projects["Instance"]:
				i += 1
			else:
				del allData[project]
		elif len(kernelData) and len(instanceData):
			if  projects[project]["HotCode"] and projects[project]["HotLoop"] and projects[project]["PaMul"] and \
				projects[project]["Instance"]:
				i += 1
			else:
				del allData[project]

	return allData

def RetrieveData(deadcode=False, livecode=False, loop=False, profile=False, hotcode=False, hotloop=False, pamul=False, instance=False, regenerate=False):
	"""
	@brief Retrieves data on a per-application basis where each application has the information selected from the input flags

	All optional arguments match their corresponding keys in the return dictionary exactly
	@param[in] deadcode 	Include deadcode code information
	@param[in] livecode 	Include livecode code information
	@param[in] loop 		Include static loop information
	@param[in] profile		Include profile information
	@param[in] hotcode		Include hotcode information
	@param[in] hotloop		Include hotloop information
	@param[in] pamul 		Include PaMul information
	@param[in] instance		Include instance information
	@retval    userData 	Maps an application path to its information
							Kernel information (for hotcode, hotloop, pamul, instance) only includes block information
	"""
	# data file names to retrieve and write to
	deadBlocksFileName = "DeadBlocks_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+".json"
	loopDataFileName = "Loops_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+".json"
	profileDataFileName = "Profiles_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+".json"
	kernelDataFileName= "Kernels_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+".json"
	instanceDataFileName = "Instances_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+".json"

	# the allData file is named after the forpus folder + build folder it was retrieved from
	allDataFileName = "allData_"+"".join( x for x in CorpusFolder.split("/") )+list(buildFolders)[0]+".json"

	# check to see if we already printed that data for this run
	# if we can't find the file we will automatically turn on all the flags, collect the data, then print the file
	# afterward we will choose the data requested and return that
	# else we just collect the data necessary and return that
	allData = {}
	try:
		# if the user is asking to regenerate, make sure this fails
		if regenerate:
			allDataFileName = "apdofhewpjfnqpjrnv"
		with open("Data/"+allDataFileName, "r") as f:
			# collect the data we are looking for and return it
			allData  = json.load(f)
	except FileNotFoundError:
		if regenerate:
			print("Regenerating data file...")
		else:
			print("Could not find file ./Data/"+allDataFileName+". Generating file...")

		loopData     = retrieveStaticLoopData(buildFolders, CorpusFolder, loopDataFileName, readLoopFile)
		profileData  = retrieveProfiles(buildFolders, CorpusFolder, profileDataFileName)
		kernelData   = retrieveKernelData(buildFolders, CorpusFolder, kernelDataFileName, readKernelFile)
		instanceData = retrieveInstanceData(buildFolders, CorpusFolder, instanceDataFileName, readKernelFile)
		deadBlocks   = retrieveDeadCode(buildFolders, CorpusFolder, deadBlocksFileName, profileData)

		refinedLoopData     = refineBlockData(loopData, loopFile=True)
		refinedProfileData  = profileData
		refinedDeadBlocks   = refineBlockData(deadBlocks, deadCodeFile=True)
		refinedKernelData   = refineBlockData(kernelData)
		refinedInstanceData = refineBlockData(instanceData)

		allData = combineData( loopData = refinedLoopData, profileData = refinedProfileData, kernelData = refinedKernelData, \
						   instanceData = refinedInstanceData, deadBlocksData = refinedDeadBlocks )

		with open("Data/"+allDataFileName, "w") as f:
			# profile data needs to be formatted in a specific way to work
			formatted = allData
			for entry in allData:
				# list of dictionaries, where each one is { "key": [srcID, snkID], "value": frequency }
				profileEdges = []
				for edge in allData[entry]["Profile"]:
					profileEdges.append( { "key": [edge[0], edge[1]], "value": allData[entry]["Profile"][edge] } )
				formatted[entry]["Profile"] = profileEdges
			json.dump(allData, f, indent=2)

	userData = {}
	for entry in allData:
		userData[entry] = {}
		if deadcode:
			userData[entry]["deadcode"] 	= allData[entry]["DeadBlocks"]
		if livecode:
			userData[entry]["livecode"] 	= allData[entry]["LiveBlocks"]
		if loop:
			userData[entry]["loop"] 		= allData[entry]["Loop"]
		if profile:
			userData[entry]["profile"] 		= allData[entry]["Profile"]
		if hotcode:
			userData[entry]["hotcode"] 		= allData[entry]["HotCode"]
		if hotloop:
			userData[entry]["hotloop"] 		= allData[entry]["HotLoop"]
		if pamul:
			userData[entry]["pamul"] 		= allData[entry]["PaMul"]
		if instance:
			userData[entry]["instance"] 	= allData[entry]["Instance"]

	return userData

